from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


User = get_user_model()


class UsersPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='TestAuthor')
        cls.authorized_client = Client()
        UsersPagesTests.authorized_client.force_login(UsersPagesTests.author)
        cls.guest_client = Client()

    def test_pages_uses_correct_template(self):
        """вызывается правильный шаблон по namespace:name"""
        templates_pages_names = {
            reverse('about:author'): 'about/about_author.html',
            reverse('about:tech'): 'about/about_tech.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = UsersPagesTests.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
