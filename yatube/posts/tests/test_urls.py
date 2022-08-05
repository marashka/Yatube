from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from .utils import YatubeTestConstructor


class PostsFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        test_shell = YatubeTestConstructor()
        test_shell.create_users(2)
        test_shell.create_groups(2)
        test_shell.create_posts(5)
        cls.user_1, cls.user_2 = test_shell.get_users()
        cls.group_1, cls.group_2 = test_shell.get_groups()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_1 = Client()
        self.authorized_client_2 = Client()
        self.user_1 = PostsFormTests.user_1
        self.user_2 = PostsFormTests.user_2
        self.authorized_client_1.force_login(self.user_1)
        self.authorized_client_2.force_login(self.user_2)
        self.group_2 = PostsFormTests.group_2
        cache.clear()

    def test_url_correct(self):
        """Проверка доступности адресов."""
        group_1 = PostsFormTests.group_1
        client_url_names = (
            (self.guest_client, reverse('posts:index')),
            (self.guest_client, reverse(
                'posts:group_list', kwargs={'slug': group_1.slug})),
            (self.guest_client, reverse(
                'posts:profile', kwargs={'username': self.user_1})),
            (self.guest_client, reverse(
                'posts:post_detail', kwargs={'post_id': '1'})),
            (self.authorized_client_1, reverse('posts:post_create')),
            (self.authorized_client_1, reverse(
                'posts:post_edit', kwargs={'post_id': '1'})),
            (self.authorized_client_1, reverse('posts:follow_index')),
        )
        for client, url in client_url_names:
            with self.subTest(url=url):
                response = client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_page_not_found(self):
        """Проверка запроса к несуществующей странице."""
        client_url_names = (
            (self.guest_client, reverse(
                'posts:group_list', kwargs={'slug': 'test_slug_3'})),
            (self.guest_client, reverse(
                'posts:profile', kwargs={'username': 'HasNoName_3'})),
            (self.guest_client, reverse(
                'posts:post_detail', kwargs={'post_id': '11'})),
        )
        for client, url in client_url_names:
            with self.subTest(url=url):
                response = client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_postedit_redirect_if_wrong_author(self):
        """Проверка редиретка при попытке редактировании чужого поста"""
        response = self.authorized_client_2.get(reverse(
            'posts:post_edit', kwargs={'post_id': '1'}), follow=True)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': '1'}))

    def test_postedit_create_redirect_unauthorized_client(self):
        """"Проверка редиректа неавторизованного пользователя"""
        url_redirect_names = (
            (reverse('posts:post_create'), reverse(
                'users:login') + '?next=/create/'),
            (reverse('posts:post_edit', kwargs={'post_id': '1'}), reverse(
                'users:login') + '?next=/posts/1/edit/')
        )
        for url, redirect in url_redirect_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
            self.assertRedirects(response, redirect)

    def test_urls_uses_correct_template(self):
        """Проверка шаблонов для адресов."""
        group_1 = PostsFormTests.group_1
        template_url_names = (
            ('posts/index.html', reverse('posts:index')),
            ('posts/group_list.html', reverse(
                'posts:group_list', kwargs={'slug': group_1.slug})),
            ('posts/profile.html', reverse(
                'posts:profile', kwargs={'username': self.user_1})),
            ('posts/post_detail.html', reverse(
                'posts:post_detail', kwargs={'post_id': '1'})),
            ('posts/create_post.html', reverse('posts:post_create')),
            ('posts/create_post.html', reverse(
                'posts:post_edit', kwargs={'post_id': '1'})),
            ('posts/follow.html', reverse('posts:follow_index'))
        )
        for template, url in template_url_names:
            with self.subTest(url=url):
                response = self.authorized_client_1.get(url)
                self.assertTemplateUsed(response, template)
