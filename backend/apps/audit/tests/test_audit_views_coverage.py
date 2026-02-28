"""
Branch coverage tests for apps.audit.views.

Goal: Hit unauthenticated, permission, filter, validation, and pagination branches.
Uses APIClient and real DB; no mocking.
"""

import uuid

from django.test import TestCase
from rest_framework.test import APIClient

from apps.audit.services import create_audit_entry
from apps.users.models import User

BASE = "/api/v1/audit"


def _admin_user():
    return User.objects.create_user(
        username="audit_admin",
        password="testpass123",
        display_name="Admin",
        role="ADMIN",
    )


def _viewer_user():
    return User.objects.create_user(
        username="audit_viewer",
        password="testpass123",
        display_name="Viewer",
        role="VIEWER",
    )


# -----------------------------
# 1. Unauthenticated → 401
# -----------------------------


class UnauthenticatedAccessTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_audit_unauthorized_returns_401(self):
        r = self.client.get(BASE + "/")
        self.assertEqual(r.status_code, 401)

    def test_get_audit_logs_alias_unauthorized_returns_401(self):
        r = self.client.get(BASE + "/logs")
        self.assertEqual(r.status_code, 401)


# -----------------------------
# 2. Authenticated non-admin and 3. Admin → 200 and list
# View uses IsAuthenticatedReadOnly; all authenticated roles (incl. VIEWER) get 200.
# -----------------------------


class AuthenticatedAccessTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = _admin_user()
        self.viewer = _viewer_user()

    def test_admin_user_gets_200_and_returns_list(self):
        self.client.force_authenticate(user=self.admin)
        r = self.client.get(BASE + "/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("results", r.json())
        self.assertIsInstance(r.json()["results"], list)

    def test_authenticated_viewer_gets_200(self):
        """Current view uses IsAuthenticatedReadOnly so VIEWER can list audit."""
        self.client.force_authenticate(user=self.viewer)
        r = self.client.get(BASE + "/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("results", r.json())


# -----------------------------
# 4. Empty audit list → []
# -----------------------------


class EmptyListTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = _admin_user()
        self.client.force_authenticate(user=self.admin)

    def test_empty_audit_list_returns_empty_results(self):
        r = self.client.get(BASE + "/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["results"], [])


# -----------------------------
# 5. Filtering by entity_id works
# 6. Filtering by invalid entity_id (bad format) → 400
# 7. Valid entity_id with no matches → []
# -----------------------------


class EntityIdFilterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = _admin_user()
        self.client.force_authenticate(user=self.admin)

    def test_filter_by_entity_id_returns_matching_entries(self):
        entity_id = uuid.uuid4()
        create_audit_entry(
            event_type="BATCH_CREATED",
            actor_id=self.admin.id,
            entity_type="PaymentBatch",
            entity_id=entity_id,
            new_state={"status": "DRAFT"},
        )
        create_audit_entry(
            event_type="REQUEST_ADDED",
            actor_id=self.admin.id,
            entity_type="PaymentRequest",
            entity_id=uuid.uuid4(),
            new_state={},
        )
        r = self.client.get(BASE + "/", {"entityId": str(entity_id)})
        self.assertEqual(r.status_code, 200)
        results = r.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["entityId"], str(entity_id))
        self.assertEqual(results[0]["entityType"], "PaymentBatch")

    def test_filter_by_invalid_entity_id_format_returns_400(self):
        r = self.client.get(BASE + "/", {"entityId": "not-a-uuid"})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("entityId", r.json()["error"]["message"])

    def test_filter_by_valid_entity_id_with_no_logs_returns_empty_list(self):
        r = self.client.get(BASE + "/", {"entityId": str(uuid.uuid4())})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["results"], [])


# -----------------------------
# entityType filter: valid and invalid
# -----------------------------


class EntityTypeFilterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = _admin_user()
        self.client.force_authenticate(user=self.admin)

    def test_filter_by_entity_type_payment_batch(self):
        create_audit_entry(
            event_type="BATCH_CREATED",
            actor_id=self.admin.id,
            entity_type="PaymentBatch",
            entity_id=uuid.uuid4(),
            new_state={},
        )
        create_audit_entry(
            event_type="REQUEST_ADDED",
            actor_id=self.admin.id,
            entity_type="PaymentRequest",
            entity_id=uuid.uuid4(),
            new_state={},
        )
        r = self.client.get(BASE + "/", {"entityType": "PaymentBatch"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["results"]), 1)
        self.assertEqual(r.json()["results"][0]["entityType"], "PaymentBatch")

    def test_filter_by_entity_type_payment_request(self):
        create_audit_entry(
            event_type="REQUEST_ADDED",
            actor_id=self.admin.id,
            entity_type="PaymentRequest",
            entity_id=uuid.uuid4(),
            new_state={},
        )
        r = self.client.get(BASE + "/", {"entityType": "PaymentRequest"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["results"]), 1)
        self.assertEqual(r.json()["results"][0]["entityType"], "PaymentRequest")

    def test_invalid_entity_type_returns_400(self):
        r = self.client.get(BASE + "/", {"entityType": "InvalidType"})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("entityType", r.json()["error"]["message"])


# -----------------------------
# actorId filter: valid and invalid format
# -----------------------------


class ActorIdFilterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = _admin_user()
        self.client.force_authenticate(user=self.admin)

    def test_filter_by_actor_id(self):
        create_audit_entry(
            event_type="BATCH_CREATED",
            actor_id=self.admin.id,
            entity_type="PaymentBatch",
            entity_id=uuid.uuid4(),
            new_state={},
        )
        r = self.client.get(BASE + "/", {"actorId": str(self.admin.id)})
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(len(r.json()["results"]), 1)

    def test_invalid_actor_id_format_returns_400(self):
        r = self.client.get(BASE + "/", {"actorId": "not-a-uuid"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("actorId", r.json()["error"]["message"])


# -----------------------------
# fromDate / toDate: valid and invalid
# -----------------------------


class DateFilterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = _admin_user()
        self.client.force_authenticate(user=self.admin)

    def test_filter_by_from_date_valid(self):
        create_audit_entry(
            event_type="BATCH_CREATED",
            actor_id=self.admin.id,
            entity_type="PaymentBatch",
            entity_id=uuid.uuid4(),
            new_state={},
        )
        r = self.client.get(
            BASE + "/",
            {"fromDate": "2020-01-01T00:00:00Z"},
        )
        self.assertEqual(r.status_code, 200)

    def test_filter_by_to_date_valid(self):
        r = self.client.get(
            BASE + "/",
            {"toDate": "2030-12-31T23:59:59Z"},
        )
        self.assertEqual(r.status_code, 200)

    def test_invalid_from_date_returns_400(self):
        r = self.client.get(BASE + "/", {"fromDate": "not-a-date"})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("fromDate", r.json()["error"]["message"])

    def test_invalid_to_date_returns_400(self):
        r = self.client.get(BASE + "/", {"toDate": "invalid"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("toDate", r.json()["error"]["message"])


# -----------------------------
# 8. Pagination (limit / offset)
# -----------------------------


class PaginationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = _admin_user()
        self.client.force_authenticate(user=self.admin)

    def test_pagination_limit_offset(self):
        for _ in range(5):
            create_audit_entry(
                event_type="BATCH_CREATED",
                actor_id=self.admin.id,
                entity_type="PaymentBatch",
                entity_id=uuid.uuid4(),
                new_state={},
            )
        r = self.client.get(BASE + "/", {"limit": 2, "offset": 0})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("results", data)
        self.assertLessEqual(len(data["results"]), 2)
        if "count" in data:
            self.assertGreaterEqual(data["count"], 5)
        r2 = self.client.get(BASE + "/", {"limit": 2, "offset": 2})
        self.assertEqual(r2.status_code, 200)
        self.assertIn("results", r2.json())

    def test_default_limit_returns_results(self):
        create_audit_entry(
            event_type="BATCH_CREATED",
            actor_id=self.admin.id,
            entity_type="PaymentBatch",
            entity_id=uuid.uuid4(),
            new_state={},
        )
        r = self.client.get(BASE + "/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("results", r.json())
