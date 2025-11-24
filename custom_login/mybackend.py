from typing import Any
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest
from .models import MyUser

class MobileBackend(ModelBackend):
    def authenticate(self, request: HttpRequest, username: str | None = ..., password: str | None = ..., **kwargs: Any):
        
        mobile = kwargs['mobile']

        try:
            user = MyUser.objects.get(mobile=mobile)
        except MyUser.DoesNotExist:
            pass
          