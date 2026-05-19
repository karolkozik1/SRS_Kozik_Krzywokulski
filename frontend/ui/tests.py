from django.test import TestCase
from unittest.mock import Mock, patch
from django.urls import reverse


class FrontendViewTests(TestCase):
    """
    Podstawowe testy integracyjne frontendu Django.

    Testy sprawdzają, czy najważniejsze widoki aplikacji
    są dostępne i poprawnie renderują odpowiedzi HTML.
    """

    def test_home_page_returns_200(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)

    def test_login_page_returns_200(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)

    def test_login_page_contains_form(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form", html=False)
        self.assertContains(response, "password", html=False)

    @patch("ui.views.requests.get")
    def test_system_health_page_returns_200(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "backend": {
                "status": "running",
                "service": "FastAPI",
                "version": "0.2.0",
            },
            "database": {
                "status": "connected",
                "connected": True,
            },
            "statistics": {
                "users_count": 10,
                "rooms_count": 20,
                "reservations_count": 30,
                "active_reservations_count": 5,
            },
            "checked_at": "2026-05-18T12:00:00",
            "response_time_ms": 15.5,
        }

        mock_get.return_value = mock_response

        response = self.client.get(reverse("system_health"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard stanu systemu")
        self.assertContains(response, "System działa poprawnie")
            

class AdditionalPageTests(TestCase):
    def test_register_page_returns_200(self):
        response = self.client.get(reverse("register"))

        self.assertEqual(response.status_code, 200)

    def test_rooms_search_page_returns_200(self):
        response = self.client.get(reverse("rooms_search"))

        self.assertEqual(response.status_code, 200)

    def test_reports_page_returns_200(self):
        response = self.client.get(reverse("reports"))

        self.assertEqual(response.status_code, 200)
        
        