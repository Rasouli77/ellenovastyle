from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.mobile_login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('account-verify/', views.verify, name='account-verify'),
]