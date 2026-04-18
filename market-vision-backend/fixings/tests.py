from django.core.management import call_command
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch

from authentication.models import User


class UpdateMarketDataViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="tester@example.com", password="secret123")
        self.client.force_authenticate(user=self.user)

    @patch("fixings.views.call_command")
    def test_update_market_uses_initial_load_command(self, mock_call_command):
        response = self.client.post("/api/fixings/market/update/", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_call_command.assert_called_once_with("get_fixings_alltime")
        self.assertEqual(response.data["message"], "Данные рынка успешно обновлены.")
