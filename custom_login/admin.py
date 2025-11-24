from django.contrib import admin
from .models import MyUser, Province, City, Profile

# Register your models here.

class ProvinceAdmin(admin.ModelAdmin):
    search_fields = ["title"]

class CityAdmin(admin.ModelAdmin):
    search_fields = ["title", "province"]
    list_display = ["title", "province"]
    list_filter = ["province"]

class MyUserAdmin(admin.ModelAdmin):
    search_fields = ["mobile"]

class ProfileAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "province", "city"]
    search_fields = ["name", "user__mobile"]
    list_filter = ["province", "city"]


admin.site.register(MyUser, MyUserAdmin)
admin.site.register(Province, ProvinceAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(Profile, ProfileAdmin)