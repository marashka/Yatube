from django.contrib.auth import get_user_model
from django.test import TestCase

from .utils import YatubeTestConstructor

User = get_user_model()


class PostGroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        test_shell = YatubeTestConstructor()
        test_shell.create_users()
        test_shell.create_groups()
        test_shell.create_posts(text='Test post' * 15)
        cls.group, = test_shell.get_groups()
        cls.post, = test_shell.get_posts()

    def test_models_have_correct_object_names(self):
        """Правильно ли отображается __str__ в объектах моделей."""
        post = PostGroupModelTest.post
        expected_name_post = post.text[:15]
        group = PostGroupModelTest.group
        expected_name_group = group
        compared_names = (
            (expected_name_post, str(post)),
            (expected_name_group, group)
        )
        for expected_name, test_model in compared_names:
            with self.subTest(expected_name=expected_name):
                self.assertEqual(expected_name, test_model)
