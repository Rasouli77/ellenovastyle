from django.db import models
from django.contrib.auth.models import AbstractUser
from .myusermanager import MyUserManager

class MyUser(AbstractUser):
    username : None
    is_vendor = models.BooleanField(default=False, null=True)
    mobile = models.CharField(max_length=11, unique=True)
    otp = models.PositiveIntegerField(blank=True, null=True)
    otp_create_date = models.DateTimeField(auto_now=True)

    objects = MyUserManager()

    USERNAME_FIELD = 'mobile'

    REQUIRED_FIELDS = []

    backend = 'custom_login.mybackend.ModelBackend'

class Province(models.Model):
    title = models.CharField(max_length=255, unique=True, verbose_name='استان')

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'استان'
        verbose_name_plural = 'استان'

class City(models.Model):
    title = models.CharField(max_length=255, verbose_name='شهر')
    province = models.ForeignKey(Province, on_delete=models.CASCADE, verbose_name='استان')
  
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'شهر'
        verbose_name_plural = 'شهر'

class Profile(models.Model):
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE, verbose_name='کاربر')
    province = models.ForeignKey(Province, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='استان')
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='شهر')
    name = models.CharField(max_length=500, default='enter', null=True, blank=True, verbose_name='نام')
    address = models.TextField(max_length=500, default='enter', verbose_name='آدرس')

    def __str__(self):
        return str(self.user)
    
    class Meta:
        verbose_name = 'حساب کاربری'
        verbose_name_plural = 'حساب کاربری'

