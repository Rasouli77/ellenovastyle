from django.contrib import admin
from .models import BlogPost, Comment

class BlogPostAdmin(admin.ModelAdmin):
    exclude = ["date_created", "modified_date"]
    search_fields = ["title"]
    list_filter = ["date_created"]
    list_display = ["title", "slug"]

class CommentAdmin(admin.ModelAdmin):
    exclude = ["date_created"]
    list_display = ["name", "phone_number", "approved"]
    list_filter = ["approved", "date_created"]

admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(Comment, CommentAdmin)