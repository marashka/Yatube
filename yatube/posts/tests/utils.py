from itertools import cycle

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Group, Post

User = get_user_model()


class YatubeTestConstructor:
    def __init__(self):
        self._users = None
        self._groups = None
        self._posts = None
        self._gif = None

    def create_users(self, users=1):
        self._users = [
            User.objects.create_user(
                username='HasNoName_' + str(user + 1)
            )
            for user in range(users)]

    def create_groups(self, groups=1):
        groups = [
            Group(
                title='Test group_' + str(group + 1),
                slug='test_slug_' + str(group + 1),
                description='Test description',
            )
            for group in range(groups)
        ]
        Group.objects.bulk_create(groups)
        self._groups = Group.objects.all()

    def create_posts(self, posts_each_user=1, text='Test post'):
        if self._groups:
            group = cycle(self._groups)
            posts = [
                Post(
                    author=user,
                    text=text,
                    group=next(group)
                )
                for user in self._users
                for post in range(posts_each_user)]
        else:
            posts = [
                Post(
                    author=user,
                    text=text,
                )
                for user in self._users_models
                for post in range(posts_each_user)]
        Post.objects.bulk_create(posts)
        self._posts = Post.objects.all()

    def uploaded_test_gif(self):
        test_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self._gif = SimpleUploadedFile(
            name='small.gif',
            content=test_gif,
            content_type='image/gif'
        )

    def get_users(self):
        return self._users

    def get_groups(self):
        return self._groups

    def get_posts(self):
        return self._posts

    def get_test_gif(self):
        return self._gif
