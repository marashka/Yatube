from django.conf import settings
from django.core.paginator import Paginator


def add_paginator(request, posts):
    paginator = Paginator(posts, settings.MAX_PAGE_AMOUNT)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
