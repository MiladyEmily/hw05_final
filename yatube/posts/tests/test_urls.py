from http import HTTPStatus

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache

from ..models import Group, Post


User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.author = User.objects.create_user(username='ImAuthor')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )
        cls.authorized_responses = {
            '/create/': 'posts/create.html',
            '/follow/': 'posts/follow.html',
        }
        cls.author_responses = {
            '/posts/1/edit/': 'posts/create.html',
        }

    def setUp(self):
        cache.clear()

    def url_location_and_template(self, responses, client, status):
        for response in responses:
            with self.subTest(response=response):
                self.assertEqual(
                    client.get(response).status_code,
                    status,
                )
        for response, template in responses.items():
            with self.subTest(response=response):
                self.assertTemplateUsed(
                    client.get(response),
                    template,
                )

    def test_common_posts_url(self):
        """шаблон и статус-код общедоступных страниц"""
        responses = {
            '/': 'posts/index.html',
            '/posts/1/': 'posts/post_detail.html',
            '/profile/HasNoName/': 'posts/profile.html',
            '/group/test/': 'posts/group_list.html',
        }
        self.assertEqual(
            PostsURLTests.guest_client.get('/profile/HasNoName/').status_code,
            HTTPStatus.OK,
        )
        self.url_location_and_template(
            responses=responses,
            client=PostsURLTests.guest_client,
            status=HTTPStatus.OK,
        )

    def test_unexisting_page_url(self):
        """статус-код несуществующей страницы"""
        responses = {
            '/unexisting_page/': 'core/404.html',
        }
        self.url_location_and_template(
            responses,
            PostsURLTests.guest_client,
            HTTPStatus.NOT_FOUND,
        )

    def test_auth_posts_url(self):
        """вызывает шаблон и статус-код страниц,
        доступных только авторизованным пользователям"""
        self.url_location_and_template(
            PostsURLTests.authorized_responses,
            PostsURLTests.authorized_client,
            HTTPStatus.OK,
        )

    def test_author_posts_url(self):
        """вызывает шаблон и статус-код страниц, доступных автору"""
        self.url_location_and_template(
            PostsURLTests.author_responses,
            PostsURLTests.authorized_author,
            HTTPStatus.OK,
        )

    def test_redirect_anonymous(self):
        """редиректит неавторизованного пользователя"""
        for item in PostsURLTests.authorized_responses:
            with self.subTest(item=item):
                response = PostsURLTests.guest_client.get(item, follow=True)
                self.assertRedirects(
                    response,
                    f'/auth/login/?next={item}',
                )

    def test_redirect_not_author(self):
        """редиректит не-автора поста"""
        for item in PostsURLTests.author_responses:
            with self.subTest(item=item):
                response = PostsURLTests.authorized_client.get(
                    item,
                    follow=True
                )
                self.assertRedirects(
                    response,
                    '/posts/1/',
                )
