from http import HTTPStatus

from django.test import TestCase, Client


class StaticPagesURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.responses = {
            '/about/author/': 'about/about_author.html',
            '/about/tech/': 'about/about_tech.html',
        }

    def test_about_url_uses_correct_template(self):
        """вызывается правильный шаблон и статус-код 200"""
        for response, template in StaticPagesURLTests.responses.items():
            with self.subTest(response=response):
                self.assertEqual(
                    StaticPagesURLTests.guest_client.get(
                        response).status_code,
                    HTTPStatus.OK
                )
                self.assertTemplateUsed(
                    StaticPagesURLTests.guest_client.get(response),
                    template
                )
