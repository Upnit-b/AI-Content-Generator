from django.db import models
from django.contrib.auth.models import User


class BlogPost(models.Model):
    """A "content repurposing" record.

    NOTE: We keep the model name `BlogPost` so existing URLs/views/templates
    remain simple, but the data model is now transcript-driven (no YouTube).
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Input
    title = models.CharField(max_length=300, blank=True, default="")
    transcript = models.TextField()

    # Output pack
    blog_post = models.TextField()
    seo_title = models.CharField(max_length=140)
    meta_description = models.CharField(max_length=170)
    tldr = models.TextField()

    tweets = models.JSONField(default=list)  # list[str]
    linkedin_post = models.TextField()
    outline = models.JSONField(default=list)  # list[str]
    key_takeaways = models.JSONField(default=list)  # list[str]

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Content Pack #{self.pk}"
