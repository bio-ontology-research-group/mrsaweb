from django.db import models

from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError


def check_unique_email(sender, instance, **kwargs):
    if instance.email and sender.objects.filter(
            email=instance.email).exclude(username=instance.username).count():
        raise ValidationError(_("The email %(email)s already exists!") % {
            'email': instance.email
        })

pre_save.connect(check_unique_email, sender=User)


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, primary_key=True, on_delete=models.CASCADE)
    organization = models.CharField(max_length=255)


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(
            user=instance)

post_save.connect(create_user_profile, sender=User)
