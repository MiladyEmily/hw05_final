from http import HTTPStatus

from django.test import TestCase, Client


class UsersURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_url_location_and_template(self):
        """шаблон и статус-код страниц приложения users"""
        self.assertEqual(
            self.guest_client.get('/auth/signup/').status_code,
            HTTPStatus.OK
        )
        self.assertTemplateUsed(
            self.guest_client.get('/auth/signup/'),
            'users/signup.html'
        )
