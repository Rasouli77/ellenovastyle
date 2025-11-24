from django.db import models
from tinymce.models import HTMLField
from django.utils import timezone

# Create your models here.

class BlogPost(models.Model):
    title = models.CharField(max_length=255, verbose_name="عنوان")
    seo_title = models.CharField(max_length=255, verbose_name='عنوان سئو', null=True)
    meta = models.CharField(max_length=255, verbose_name="متا")
    slug = models.SlugField(null=True, unique=True, verbose_name='لینک')
    canonical = models.CharField(max_length=255, null=True, verbose_name="کنونیکال", blank=True)
    image = models.ImageField(upload_to='image/blog', verbose_name='تصویر گالری')
    content = HTMLField(verbose_name="محتوا")
    date_created = models.DateTimeField(default=timezone.now, verbose_name='تاریخ ساخت', null=True, blank=True)
    modified_date = models.DateTimeField(auto_now=True, verbose_name='تاریخ تغییر', null=True, blank=True)

    class Meta:
        verbose_name = "بلاگ"
        verbose_name_plural = "بلاگ"

    def __str__(self):
        return f"{self.title}"
    
class Comment(models.Model):
    blog = models.ForeignKey(BlogPost, on_delete=models.CASCADE, verbose_name="بلاگ")
    name = models.CharField(max_length=255, verbose_name="نام")
    phone_number = models.CharField(max_length=255, verbose_name="شماره تلفن")
    comment = models.TextField(max_length=900, verbose_name="نظر")
    approved = models.BooleanField(default=False, verbose_name="تاییده شده")
    date_created = models.DateTimeField(default=timezone.now, verbose_name='تاریخ ساخت', null=True, blank=True)

    class Meta:
        verbose_name = "نظر"
        verbose_name_plural = "نظر"

    def __str__(self):
        return self.comment
    