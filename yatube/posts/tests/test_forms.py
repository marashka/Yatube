import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post
from .utils import YatubeTestConstructor

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        test_shell = YatubeTestConstructor()
        test_shell.create_users()
        test_shell.create_groups(2)
        test_shell.create_posts(5)
        test_shell.uploaded_test_gif()
        cls.user, = test_shell.get_users()
        cls.group_1, cls.group_2 = test_shell.get_groups()
        cls.posts = test_shell.get_posts()
        cls.test_gif = test_shell.get_test_gif()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.user = PostsFormTests.user
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        """Проверка создания поста"""
        group_2 = PostsFormTests.group_2
        posts_count = Post.objects.count()
        test_gif = PostsFormTests.test_gif

        form_data = {
            'text': 'Новый пост',
            'group': group_2.id,
            'image': test_gif,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        new_post = Post.objects.first()
        compared_names = (
            (form_data['text'], new_post.text),
            (group_2, new_post.group),
            (self.user, new_post.author),
            ('posts/small.gif', new_post.image.name)
        )
        for expected_name, test_name in compared_names:
            with self.subTest(expected_name=expected_name):
                self.assertEqual(expected_name, test_name)

    def test_post_edit(self):
        """Проверка редактирования"""
        group_2 = PostsFormTests.group_2
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Edit Post',
            'group': group_2.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': '1'}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': '1'}))
        self.assertEqual(Post.objects.count(), posts_count)
        edit_post_text = Post.objects.last().text
        edit_post_group = Post.objects.last().group
        edit_post_author = Post.objects.last().author
        compared_names = (
            (form_data['text'], edit_post_text),
            (group_2, edit_post_group),
            (self.user, edit_post_author)
        )
        for expected_name, test_name in compared_names:
            with self.subTest(expected_name=expected_name):
                self.assertEqual(expected_name, test_name)
