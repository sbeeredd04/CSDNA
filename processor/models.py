from django.db import models

class ImageUpload(models.Model):
    image = models.ImageField(upload_to='uploads/')
