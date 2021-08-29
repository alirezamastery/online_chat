from django.db import models
from django.contrib.auth import get_user_model



class ChatMessage(models.Model):
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    from_user = models.BooleanField(default=True)

    def __str__(self):
        return str(self.message)

