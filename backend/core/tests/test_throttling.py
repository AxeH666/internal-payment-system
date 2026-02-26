from django.urls import reverse
from rest_framework.test import APITestCase
from apps.users.models import User


class ThrottleSmokeTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="throttle_user",
            display_name="Throttle",
            role="ADMIN",
        )
        self.client.force_authenticate(self.user)

    def test_mutation_requests_execute(self):
        url = reverse("ledger:list-or-create-clients")

        response = self.client.post(
            url,
            {"name": "T1"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="abc123",
        )

        self.assertIn(response.status_code, [201, 400])
