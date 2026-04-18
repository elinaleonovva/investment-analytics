from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from authentication.models import User


class AuthenticationFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_returns_tokens_and_creates_user(self):
        response = self.client.post(
            "/api/auth/register/",
            {"email": "User@Example.com", "password": "secret123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(User.objects.filter(email="user@example.com").exists())

    def test_login_works_after_registration(self):
        self.client.post(
            "/api/auth/register/",
            {"email": "user@example.com", "password": "secret123"},
            format="json",
        )

        response = self.client.post(
            "/api/auth/login/",
            {"email": "user@example.com", "password": "secret123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_is_case_insensitive_for_email(self):
        User.objects.create_user(email="user@example.com", password="secret123")

        response = self.client.post(
            "/api/auth/login/",
            {"email": "USER@EXAMPLE.COM", "password": "secret123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
