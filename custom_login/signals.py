from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MyUser, Profile, Province, City

@receiver(post_save, sender=MyUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(
            user=instance,
            province=None,
            city=None,
            name='نامشخص',
            address='نامشخص'
        )

