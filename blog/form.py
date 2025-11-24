from django import forms
from blog.models import Comment
from django.forms import ModelForm

class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['name', 'phone_number', 'comment']