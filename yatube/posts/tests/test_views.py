import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Post
from .utils import YatubeTestConstructor

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        test_shell = YatubeTestConstructor()
        test_shell.create_users(2)
        test_shell.create_groups(2)
        test_shell.create_posts(12)
        test_shell.uploaded_test_gif()
        cls.user_1, cls.user_2 = test_shell.get_users()
        cls.group_1, cls.group_2 = test_shell.get_groups()
        cls.posts = test_shell.get_posts()
        cls.test_gif = test_shell.get_test_gif()
        cls.first_post = cls.posts[23]
        cls.first_post.image = cls.test_gif
        cls.first_post.save()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_1 = Client()
        self.authorized_client_2 = Client()
        self.user_1 = PostsFormTests.user_1
        self.user_2 = PostsFormTests.user_2
        self.authorized_client_1.force_login(self.user_1)
        self.authorized_client_2.force_login(self.user_2)
        self.group_2 = PostsFormTests.group_2

    def tearDown(self):
        cache.clear()

    def test_uses_correct_template(self):
        """URL-адреса используют соответствующие шаблоны."""
        group_2 = PostsFormTests.group_2
        template_reverse_names = (
            ('posts/index.html', reverse('posts:index')),
            ('posts/group_list.html', reverse(
                'posts:group_list', kwargs={'slug': group_2.slug})),
            ('posts/profile.html', reverse(
                'posts:profile', kwargs={'username': self.user_1.username})),
            ('posts/post_detail.html', reverse(
                'posts:post_detail', kwargs={'post_id': '1'})),
            ('posts/create_post.html', reverse('posts:post_create')),
            ('posts/create_post.html', reverse(
                'posts:post_edit', kwargs={'post_id': '1'})),
        )
        for template, reverse_name in template_reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client_1.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблоны сформированы с правильным контекстом."""
        group_1 = PostsFormTests.group_1
        first_post = PostsFormTests.first_post
        response = self.guest_client.get(reverse(
            'posts:index') + '?page=3')
        post_0 = response.context.get('page_obj').object_list[3]
        post_author_0 = post_0.author
        post_text_0 = post_0.text
        post_group_0 = post_0.group
        post_image_0 = post_0.image
        self.assertEqual(post_author_0, self.user_1)
        self.assertEqual(post_text_0, first_post.text)
        self.assertEqual(post_group_0, group_1)
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        group_1 = PostsFormTests.group_1
        posts = PostsFormTests.posts
        response = self.guest_client.get(reverse(
            'posts:group_list', kwargs={'slug': group_1.slug}))
        self.assertEqual(response.context.get('group').title, group_1.title)
        self.assertEqual(response.context.get('group').slug, group_1.slug)
        self.assertEqual(
            response.context.get('group').description, group_1.description
        )
        for i in range(4):
            with self.subTest(post=i):
                post = response.context.get('page_obj').object_list[i]
                self.assertEqual(post.author, self.user_2)
                self.assertEqual(post.text, posts[1].text)
                self.assertEqual(post.group, group_1)
        response = self.guest_client.get(reverse(
            'posts:group_list', kwargs={'slug': group_1.slug}) + '?page=2')
        post_0 = response.context.get('page_obj').object_list[1]
        post_image_0 = post_0.image
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        posts = PostsFormTests.posts
        group_2 = PostsFormTests.group_2
        response = self.guest_client.get(reverse(
            'posts:profile', kwargs={'username': self.user_1}))
        self.assertEqual(response.context.get('author'), self.user_1)
        for i in range(10)[::2]:
            with self.subTest(post=i):
                post = response.context.get('page_obj').object_list[i]
                self.assertEqual(post.author, self.user_1)
                self.assertEqual(post.text, posts[1].text)
                self.assertEqual(post.group, group_2)
        response = self.guest_client.get(reverse(
            'posts:profile', kwargs={'username': self.user_1}) + '?page=2')
        post_0 = response.context.get('page_obj').object_list[1]
        post_image_0 = post_0.image
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': '1'}))
        post = response.context.get('post')
        self.assertEqual(post.id, 1)
        self.assertEqual(post.image, 'posts/small.gif')

    def test_post_create_show_correct_form(self):
        """Шаблон post_create сформирован с правильной формой."""
        response = self.authorized_client_1.get(
            reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            form_field = response.context.get('form').fields.get(value)
            self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_form(self):
        """Шаблон post_edit сформирован с правильной формой."""
        response = self.authorized_client_1.get(reverse(
            'posts:post_edit', kwargs={'post_id': '1'}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            form_field = response.context.get('form').fields.get(value)
            self.assertIsInstance(form_field, expected)
        self.assertTrue(response.context.get('is_edit'))

    def test_post_is_created_correct(self):
        """Пост создан и отображен на страницах: index, group_list, profile"""
        group_2 = PostsFormTests.group_2
        new_post = Post.objects.create(
            author=self.user_1,
            text='Новый пост',
            group=group_2
        )
        reverse_names = (
            (reverse('posts:index')),
            (reverse('posts:group_list', kwargs={'slug': group_2.slug})),
            (reverse('posts:profile', kwargs={
                'username': self.user_1.username
            })),
        )
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertIn(new_post, response.context.get('page_obj'))

    def test_post_doesnt_show_on_page_another_group(self):
        """Пост не отобразился на странице другой группы"""
        group_1 = PostsFormTests.group_1
        reverse_name = (
            reverse('posts:group_list', kwargs={'slug': group_1.slug}))
        response = self.guest_client.get(reverse_name)
        self.assertNotIn(group_1, response.context.get('page_obj'))

    def test_paginator(self):
        """Пагинатор отображает правильное количество постов"""
        number_of_posts_on_page = (10, 10, 4)
        for page in range(3):
            with self.subTest(page=page + 1):
                response = self.guest_client.get(reverse(
                    'posts:index') + '?page=' + str(page + 1))
                self.assertEqual(len(
                    response.context.get('page_obj')),
                    number_of_posts_on_page[page])

    def test_cache(self):
        """Тестирование работы кэша index"""
        posts = PostsFormTests.posts
        last_post = posts[0]
        last_post.text = 'Пост для проверки кэша'
        last_post.save()
        response_one = self.guest_client.get(reverse(
            'posts:index') + '?page=1')
        last_post.delete()
        self.assertContains(response_one, last_post.text)
        cache.clear()
        response_two = self.guest_client.get(reverse(
            'posts:index') + '?page=1')
        self.assertNotContains(response_two, last_post.text)

    def test_new_post_shows_for_sub(self):
        """Новая запись автора появляется в ленте тех, у подписчиков """
        group_2 = PostsFormTests.group_2
        Follow.objects.create(
            user=self.user_1,
            author=self.user_2
        )
        new_post = Post.objects.create(
            author=self.user_2,
            text='Новый пост',
            group=group_2
        )
        response = self.authorized_client_1.get(reverse('posts:follow_index'))
        self.assertIn(new_post, response.context.get('page_obj'))

    def test_new_post_doesnt_show_for_unsub(self):
        """Новая запись автора не появляется в ленте у пользователей
        без подписки"""
        group_2 = PostsFormTests.group_2
        Follow.objects.create(
            user=self.user_1,
            author=self.user_2
        )
        new_post = Post.objects.create(
            author=self.user_2,
            text='Новый пост',
            group=group_2
        )
        response = self.authorized_client_2.get(reverse('posts:follow_index'))
        self.assertNotIn(new_post, response.context.get('page_obj'))

    def follow_is_created_correct(self):
        """Тестирование подписки"""
        follow_count = Follow.objects.all().count()
        self.authorized_client_1.get(reverse(
            'posts: profile_follow',
            kwargs={'username': self.user_1.username}
        ))
        self.assertEqual(Follow.objects.all().count(), follow_count + 1)

    def unfollow_is_created_correct(self):
        """Тестирование отписки"""
        self.authorized_client_1.get(reverse(
            'posts: profile_follow',
            kwargs={'username': self.user_1.username}
        ))
        follow_count = Follow.objects.all().count()
        self.authorized_client_1.get(reverse(
            'posts: profile_unfollow',
            kwargs={'username': self.user_1.username}
        ))
        self.assertEqual(Follow.objects.all().count(), follow_count - 1)
