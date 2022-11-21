from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required

from .forms import PostForm, CommentForm
from .models import Post, Group, Follow
from .helpers import page_paginator


PAGE_TITLE_LEN = 30
User = get_user_model()


def index(request):
    post_list = Post.objects.all()
    context = {
        'page_obj': page_paginator(post_list, request),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, group_condition):
    group = get_object_or_404(Group, slug=group_condition)
    post_list = group.posts.all()
    context = {
        'group': group,
        'page_obj': page_paginator(post_list, request),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author).exists()
    context = {
        'author': author,
        'posts_count': author.posts.count(),
        'page_obj': page_paginator(post_list, request),
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    page_title = 'Пост ' + post.text[0:PAGE_TITLE_LEN]
    comment_form = CommentForm()
    author_post_number = post.author.posts.count()
    comments_list = post.comments.all()
    context = {
        'page_title': page_title,
        'post': post,
        'author_post_number': author_post_number,
        'comment_form': comment_form,
        'comments': comments_list,
        'user': request.user,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    post = Post.objects.get(pk=post_id)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None,)
    if form.is_valid():
        post = form.save(commit=False)
        author = request.user
        post.author = author
        post.save()
        return redirect('posts:profile', author.username)
    context = {
        'form': form,
        'is_edit': False,
    }
    return render(request, 'posts/create.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES or None,
            instance=post
        )
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post.pk)
        return render(request, 'posts/create.html', {'form': form})
    form = PostForm(instance=post)
    context = {
        'form': form,
        'is_edit': True,
        'post_id': post.pk,
    }
    return render(request, 'posts/create.html', context)


@login_required
def follow_index(request):
    follow_list = request.user.follower.all()
    author_list = User.objects.filter(following__in=follow_list)
    post_list = Post.objects.filter(author__in=author_list)
    context = {
        'page_obj': page_paginator(post_list, request),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    not_me = request.user.username != username
    followed = Follow.objects.filter(user=request.user, author=get_object_or_404(User, username=username)).exists()
    if not_me and not followed:
        Follow.objects.create(
            user=request.user,
            author=get_object_or_404(User, username=username)
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    follow_relation = Follow.objects.filter(
        user=request.user,
        author=get_object_or_404(User, username=username)
    )
    follow_relation.delete()
    return redirect('posts:profile', username)
