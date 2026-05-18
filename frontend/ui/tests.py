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

    @patch("requests.get")
    def test_rooms_page_returns_200(self, mock_get):
        """
        Test widoku listy sal.

        Odpowiedź backendu FastAPI jest mockowana, żeby test
        frontendu nie zależał od aktualnego stanu backendu i bazy danych.
        """

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 1,
                "room_number": "101",
                "building_id": 1,
                "floor": 1,
                "capacity": 30,
                "room_type_id": 1,
                "accessibility_id": 1,
            },
            {
                "id": 2,
                "room_number": "102",
                "building_id": 1,
                "floor": 1,
                "capacity": 25,
                "room_type_id": 1,
                "accessibility_id": 1,
            },
        ]

        mock_get.return_value = mock_response

        response = self.client.get(reverse("rooms"))

        self.assertEqual(response.status_code, 200)
        

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