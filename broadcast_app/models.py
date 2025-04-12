from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    USER_TYPE_CHOICES = (
        ('viewer', 'Viewer'),
        ('broadcaster', 'Broadcaster'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    authorization_id = models.ImageField(upload_to='authorization_ids/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_user_type_display()})"


class Broadcast(models.Model):
    broadcaster = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    stream_url = models.URLField()
    is_live = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.broadcaster.username}"

    def clean(self):
        if self.broadcaster.profile.user_type != 'broadcaster':
            raise ValidationError("Only broadcasters can create broadcasts.")

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
