"""
Reconciliation management command.

Verifies financial invariants and detects corruption.
Run: python manage.py reconcile_payments
"""

from django.core.management.base import BaseCommand
from django.db.models import Q, F
from apps.payments.models import PaymentRequest
from apps.audit.models import AuditLog


class Command(BaseCommand):
    help = "Reconcile payment requests and verify financial invariants"

    def handle(self, *args, **options):
        self.stdout.write("Starting payment reconciliation...")

        errors = []
        warnings = []

        # Check 1: total_amount correctness
        self.stdout.write("\n[1] Checking total_amount integrity...")
        invalid_totals = PaymentRequest.objects.filter(
            Q(total_amount__isnull=False)
            & ~Q(total_amount=F("base_amount") + F("extra_amount"))
        )
        if invalid_totals.exists():
            errors.append(
                f"Found {invalid_totals.count()} requests with incorrect total_amount"
            )
            for req in invalid_totals[:10]:  # Show first 10
                self.stdout.write(
                    self.style.ERROR(
                        f"  Request {req.id}: total={req.total_amount}, "
                        f"base={req.base_amount}, extra={req.extra_amount}"
                    )
                )
        else:
            self.stdout.write(self.style.SUCCESS("  ✓ All total_amount values correct"))

        # Check 2: Missing audit entries for state transitions
        self.stdout.write("\n[2] Checking audit log completeness...")
        requests_with_transitions = PaymentRequest.objects.exclude(status="DRAFT")
        for req in requests_with_transitions[:100]:  # Sample check
            has_audit = AuditLog.objects.filter(
                entity_type="PaymentRequest", entity_id=req.id
            ).exists()
            if not has_audit:
                warnings.append(
                    f"Request {req.id} (status={req.status}) has no audit entries"
                )

        if not warnings:
            self.stdout.write(self.style.SUCCESS("  ✓ Audit logs present"))

        # Check 3: Broken foreign key references
        self.stdout.write("\n[3] Checking foreign key integrity...")
        broken_vendors = PaymentRequest.objects.filter(vendor_id__isnull=False).exclude(
            vendor__isnull=False
        )
        broken_sites = PaymentRequest.objects.filter(site_id__isnull=False).exclude(
            site__isnull=False
        )
        broken_subcontractors = PaymentRequest.objects.filter(
            subcontractor_id__isnull=False
        ).exclude(subcontractor__isnull=False)

        if broken_vendors.exists():
            errors.append(
                f"Found {broken_vendors.count()} requests with broken vendor FK"
            )
        if broken_sites.exists():
            errors.append(f"Found {broken_sites.count()} requests with broken site FK")
        if broken_subcontractors.exists():
            errors.append(
                f"Found {broken_subcontractors.count()} requests with broken "
                "subcontractor FK"
            )

        if not (
            broken_vendors.exists()
            or broken_sites.exists()
            or broken_subcontractors.exists()
        ):
            self.stdout.write(self.style.SUCCESS("  ✓ All foreign keys valid"))

        # Check 4: Legacy vs Ledger exclusivity
        self.stdout.write("\n[4] Checking legacy/ledger exclusivity...")
        invalid_exclusivity = PaymentRequest.objects.filter(
            Q(entity_type__isnull=True, beneficiary_name__isnull=True)
            | Q(entity_type__isnull=False, beneficiary_name__isnull=False)
        )
        if invalid_exclusivity.exists():
            errors.append(
                f"Found {invalid_exclusivity.count()} requests violating "
                "legacy/ledger exclusivity"
            )
        else:
            self.stdout.write(self.style.SUCCESS("  ✓ Legacy/ledger exclusivity valid"))

        # Check 5: Vendor/Subcontractor exclusivity
        self.stdout.write("\n[5] Checking vendor/subcontractor exclusivity...")
        invalid_fks = PaymentRequest.objects.filter(
            vendor_id__isnull=False, subcontractor_id__isnull=False
        )
        if invalid_fks.exists():
            errors.append(
                f"Found {invalid_fks.count()} requests with both vendor and "
                "subcontractor"
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("  ✓ Vendor/subcontractor exclusivity valid")
            )

        # Summary
        self.stdout.write("\n" + "=" * 50)
        if errors:
            self.stdout.write(self.style.ERROR(f"\n❌ ERRORS FOUND: {len(errors)}"))
            for error in errors:
                self.stdout.write(self.style.ERROR(f"  - {error}"))
            return 1
        elif warnings:
            self.stdout.write(self.style.WARNING(f"\n⚠️  WARNINGS: {len(warnings)}"))
            for warning in warnings[:10]:
                self.stdout.write(self.style.WARNING(f"  - {warning}"))
            return 0
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ RECONCILIATION PASSED"))
            self.stdout.write("All financial invariants verified.")
            return 0
