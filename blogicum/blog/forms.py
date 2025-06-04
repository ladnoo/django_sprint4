from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'text', 'pub_date', 'image', 'category', 'location')
        widgets = {
            'pub_date': forms.DateInput(attrs={'type': 'datetime-local'})
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
