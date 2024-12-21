from django.db import models
from base.models import BaseModel
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from base.email import send_account_activation_email
from mcqs.models import MCQ
# Create your models here.
class Profile(BaseModel):
    user = models.OneToOneField(User , on_delete=models.CASCADE , related_name="profile", null=True)
    is_email_verified = models.BooleanField(default=False)
    email_token = models.CharField(max_length=100 , null=True , blank=True)
    profile_image = models.ImageField(upload_to='profile/', null=True, blank=True)
    reset_token = models.CharField(max_length=100, null=True, blank=True)  # New field for password reset token
    current_test = models.CharField(max_length=100, null=True, blank=True)  # New field for password reset token

    def __str__(self):
        return self.user.username
    
    
@receiver(post_save , sender = User)
def  send_email_token(sender , instance , created , **kwargs):
    try:
        if created:
            email_token = str(uuid.uuid4())
            Profile.objects.create(user = instance , email_token = email_token)
            email = instance.email
            send_account_activation_email(email , email_token)

    except Exception as e:
        print(e)


