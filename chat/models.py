from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.user)


class ChatMessage(models.Model):
    message = models.TextField()
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    from_user = models.BooleanField(default=True)

    def __str__(self):
        return str(self.author)
