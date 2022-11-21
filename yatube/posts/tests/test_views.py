from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.core.cache import cache

from ..models import Post, Group, Comment, Follow
from ..forms import PostForm


User = get_user_model()


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='TestAuthor')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Это тестовая группа'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Текст поста 111',
        )
        cls.new_user = User.objects.create(username='TestUser')
        cls.new_authorized_client = Client()
        cls.new_authorized_client.force_login(cls.new_user)
        cls.follow_relation = Follow.objects.create(
            user=cls.new_user,
            author=cls.author
        )

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:follow_index'): 'posts/follow.html',
            reverse('posts:group_list',
                    kwargs={'group_condition': 'test-group'}):
                        'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'TestAuthor'}):
                        'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': 1}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': 1}):
                'posts/create.html',
            reverse('posts:post_create'): 'posts/create.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = PostsPagesTests.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
        Follow.objects.create(
            user=PostsPagesTests.author,
            author=PostsPagesTests.author
        )

    def test_pages_with_object_lists(self):
        """корректность контекста(списка объектов) от пагинатора"""
        new_author = User.objects.create(username='TestAuthor2')
        post_list = []
        for i in range(11):
            post_list.append(Post(
                author=new_author,
                text=f'Текст поста{i}',
                group=PostsPagesTests.group,
            ))
        Post.objects.bulk_create(post_list)
        first_context_objects = {
            reverse('posts:index'): Post.objects.latest('pub_date'),
            reverse('posts:group_list',
                    kwargs={'group_condition': 'test-group'}):
                        PostsPagesTests.group.posts.latest('pub_date'),
            reverse('posts:profile', kwargs={'username': 'TestAuthor2'}):
                new_author.posts.latest('pub_date'),
        }
        for page, expected_obj in first_context_objects.items():
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                first_object = response.context['page_obj'].object_list[0]
                self.assertEqual(first_object, expected_obj)
        paginator_2_page_length = {
            reverse('posts:index'): 2,
            reverse('posts:group_list',
                    kwargs={'group_condition': 'test-group'}): 1,
            reverse('posts:profile', kwargs={'username': 'TestAuthor2'}): 1,
        }
        for page, paginator_len in paginator_2_page_length.items():
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(
                    len(response.context['page_obj'].object_list),
                    10
                )
                response = self.authorized_client.get(page, {'page': 2})
                self.assertEqual(
                    len(response.context['page_obj'].object_list),
                    paginator_len
                )

    def test_post_detail(self):
        """правильный контекст для показа детального поста"""
        response = (self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1})))
        self.assertEqual(response.context.get('post'), PostsPagesTests.post)

    def test_correct_forms(self):
        """правильный контекст страниц с формами"""
        templates_pages_names = {
            reverse('posts:post_create'): False,
            reverse('posts:post_edit', kwargs={'post_id': 1}): True,
        }
        for reverse_name, is_edit in templates_pages_names.items():
            form_fields = {
                'group': forms.fields.ChoiceField,
                'text': forms.fields.CharField,
            }
            with self.subTest(reverse_name=reverse_name):
                response_context = PostsPagesTests.authorized_client.get(
                    reverse_name).context
                context_is_edit = response_context.get('is_edit')
                context_form = response_context.get('form')
                self.assertIsInstance(context_is_edit, bool)
                self.assertEqual(context_is_edit, is_edit)
                self.assertIsInstance(context_form, PostForm)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = context_form.fields.get(value)
                        self.assertIsInstance(form_field, expected)
        response = PostsPagesTests.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': 1}))
        self.assertEqual(
            response.context.get('form').instance,
            PostsPagesTests.post
        )

    def test_post_with_group(self):
        """добавление поста в БД при отправке формы"""
        new_post = Post.objects.create(
            author=PostsPagesTests.author,
            text='Текст нового поста',
            group=PostsPagesTests.group,
        )
        pages_list = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'group_condition': 'test-group'}),
            reverse('posts:profile', kwargs={'username': 'TestAuthor'}),
        ]
        for page in pages_list:
            response = self.authorized_client.get(page)
            self.assertEqual(
                response.context['page_obj'].object_list[0],
                new_post
            )

    def test_post_with_group_not_in_other_group(self):
        """недобавление нового поста на страницы других групп"""
        Group.objects.create(
            title='Тестовая группа 2',
            slug='test-group2',
            description='Это тестовая группа 2'
        )
        new_post_with_group = Post.objects.create(
            text='Тестовый текст нового поста',
            group=PostsPagesTests.group,
            author=PostsPagesTests.author,
        )
        response = PostsPagesTests.authorized_client.get(reverse(
            'posts:group_list', kwargs={'group_condition': 'test-group2'}))
        self.assertTrue(
            new_post_with_group not in response.context.get('page_obj')
        )

    def test_post_with_group(self):
        """добавление комментария в БД и на нужные страницы"""
        comment = Comment.objects.create(
            text='Тестовый коммент',
            author=PostsPagesTests.author,
            post=PostsPagesTests.post,
        )
        response = PostsPagesTests.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1}))
        self.assertTrue(comment in response.context.get('comments'))

    def test_comment_not_in_other_post(self):
        """недобавление нового комментария на страницы других постов"""
        new_post_with_group = Post.objects.create(
            text='Тестовый текст нового поста',
            group=PostsPagesTests.group,
            author=PostsPagesTests.author,
        )
        comment = Comment.objects.create(
            text='Тестовый коммент',
            author=PostsPagesTests.author,
            post=PostsPagesTests.post,
        )
        response = PostsPagesTests.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': new_post_with_group.pk}))
        self.assertTrue(comment not in response.context.get('comments'))

    def test_z_index_page_cache(self):
        """открытие главной страницы из кэша"""
        cache.clear()
        PostsPagesTests.authorized_client.get(
            reverse('posts:index'))
        response = PostsPagesTests.authorized_client.get(
            reverse('posts:index'))
        self.assertContains(response, 'Текст поста 111')

    def test_follow(self):
        """можно подписаться на автора"""
        response = PostsPagesTests.new_authorized_client.get(
            reverse('posts:follow_index'))
        self.assertContains(response, 'Текст поста 111')

    def test_unfollow(self):
        """можно отписаться на автора"""
        PostsPagesTests.follow_relation.delete()
        response = PostsPagesTests.new_authorized_client.get(
            reverse('posts:follow_index'))
        self.assertNotContains(response, 'Текст поста 111')

    def test_new_post_only_for_followers(self):
        """новый пост автора показывается только у тех, кто подписан"""
        Post.objects.create(
            author=PostsPagesTests.author,
            text='Текст поста для подписчиков',
        )
        response = PostsPagesTests.new_authorized_client.get(
            reverse('posts:follow_index'))
        self.assertContains(response, 'Текст поста для подписчиков')
        response = PostsPagesTests.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertNotContains(response, 'Текст поста для подписчиков')
