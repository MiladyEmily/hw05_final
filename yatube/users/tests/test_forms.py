from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


User = get_user_model()


class UserCreateFormTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_create_user(self):
        """Валидная форма создает нового пользователя."""
        users_count = User.objects.count()
        form_data = {
            'username': 'test1',
            'password1': 'testPassword',
            'password2': 'testPassword',
        }
        self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertEqual(User.objects.count(), users_count + 1)
        self.assertTrue(
            User.objects.filter(
                username='test1',
            ).exists()
        )

    def test_create_not_unique_username(self):
        """Неуникальный username не создает нового пользователя
        и не роняет сайт."""
        form_data = {
            'username': 'test',
            'password1': 'testPassword',
            'password2': 'testPassword',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        users_count = User.objects.count()
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertEqual(User.objects.count(), users_count)
        self.assertFormError(
            response,
            'form',
            'username',
            'Пользователь с таким именем уже существует.'
        )
        self.assertEqual(response.status_code, 200)
