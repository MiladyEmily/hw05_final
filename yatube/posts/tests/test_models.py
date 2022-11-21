from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post_short = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.post_long = Post.objects.create(
            author=cls.user,
            text='Тестовый пост чуть длиннее предыдущего',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        posts_str = {
            PostModelTest.post_short: 'Тестовый пост',
            PostModelTest.post_long: 'Тестовый пост ч',
        }

        for post, expected_value in posts_str.items():
            with self.subTest(post=post):
                self.assertEqual(
                    str(post), expected_value)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post_short
        field_verboses = {
            'group': 'Группа',
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post_short
        field_help = {
            'group': 'Группа, к которой будет относиться пост, необязательно',
            'text': 'Введите текст поста',
        }
        for field, expected_value in field_help.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = GroupModelTest.group
        group_str = str(group)
        self.assertEqual(group_str, 'Тестовая группа')
