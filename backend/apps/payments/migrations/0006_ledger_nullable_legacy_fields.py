# Generated migration for Phase 2 ledger-driven support
# Ledger-driven PaymentRequests use entity_type, vendor/site, base_amount,
# total_amount and do not use beneficiary_name, beneficiary_account, purpose
# (constraint requires null). amount is populated from total_amount for ledger-driven.

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0005_add_phase2_constraints"),
    ]

    operations = [
        migrations.AlterField(
            model_name="paymentrequest",
            name="amount",
            field=models.DecimalField(
                decimal_places=2,
                max_digits=15,
                null=True,
                blank=True,
                validators=[django.core.validators.MinValueValidator(0.01)],
            ),
        ),
        migrations.AlterField(
            model_name="paymentrequest",
            name="beneficiary_name",
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name="paymentrequest",
            name="beneficiary_account",
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name="paymentrequest",
            name="purpose",
            field=models.TextField(null=True, blank=True),
        ),
        # Update amount_positive constraint to allow null for ledger-driven
        migrations.RemoveConstraint(
            model_name="paymentrequest",
            name="amount_positive",
        ),
        migrations.AddConstraint(
            model_name="paymentrequest",
            constraint=models.CheckConstraint(
                check=models.Q(("amount__isnull", True)) | models.Q(("amount__gt", 0)),
                name="amount_positive",
            ),
        ),
    ]
