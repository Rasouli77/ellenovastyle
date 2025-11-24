from django.forms import ModelForm
from .models import MyUser

class EditUser(ModelForm):
    class Meta:
        model = MyUser
        fields = ['username', 'mobile']

class Register(ModelForm):
    class Meta:
        model = MyUser
        fields = ['mobile']