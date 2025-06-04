from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from blogicum import settings

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, \
    ListView, UpdateView

from ..forms import CommentForm, PostForm
from ..models import Category, Post
from ..utils import filter_posts_for_reader, is_available

User = get_user_model()


class ProfileRedirectMixin(LoginRequiredMixin):
    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostWriteMixin:
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'


class CreatePostView(ProfileRedirectMixin, PostWriteMixin, CreateView):
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostListView(ListView):
    model = Post
    paginate_by = settings.POSTS_PER_PAGE
    template_name = 'blog/index.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('author', 'location', 'category')
        return filter_posts_for_reader(queryset)


class CategoryPostView(ListView):
    model = Post
    paginate_by = settings.POSTS_PER_PAGE
    template_name = 'blog/category.html'

    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        category = get_object_or_404(
            Category,
            slug=category_slug,
            is_published=True
        )
        self.category = category

        queryset = super().get_queryset()
        queryset = queryset.select_related('author', 'location', 'category')

        queryset = filter_posts_for_reader(
            queryset=queryset,
            category=category
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'category': self.category
        })
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('author', 'location', 'category')
        return queryset

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if (
            not is_available(obj)
            and not (
                self.request.user.is_authenticated
                and obj.author == self.request.user
            )
        ):
            raise Http404()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        comments = post.comments.all().select_related('author')
        context.update({
            'form': CommentForm(),
            'comments': comments
        })
        return context


class EditPostView(PostWriteMixin, UpdateView):
    def get_queryset(self):
        return Post.objects.all()

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if not request.user.is_authenticated or post.author != request.user:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.pk}
        )


class DeletePostView(ProfileRedirectMixin, PostWriteMixin, DeleteView):
    def get_queryset(self):
        return self.request.user.posts
