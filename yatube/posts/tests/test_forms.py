import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Post, Comment


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class CommentCreateFormTest(TestCase):
    def setUp(self):
        self.author = User.objects.create(username='TestAuthor')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.post = Post.objects.create(
            author=self.author,
            text='Текст базового поста',
        )

    def test_create_comment(self):
        """Валидная форма создает запись в Comment."""
        comments_count = self.post.comments.count()
        form_data = {
            'text': 'Это комментарий!',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(self.post.comments.count(), comments_count + 1)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertTrue(
            Comment.objects.filter(
                text='Это комментарий!',
                author=self.author,
            ).exists()
        )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    def setUp(self):
        self.author = User.objects.create(username='TestAuthor')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.post = Post.objects.create(
            author=self.author,
            text='Текст базового поста',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        form_data = {
            'text': 'Тестовый текст',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': 'TestAuthor'})
        )
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=None,
                image='posts/small.gif',
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст базового поста изменённый',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': 1})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='Текст базового поста изменённый',
                group=None,
            ).exists()
        )
