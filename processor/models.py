from django.db import models

class ImageUpload(models.Model):
    image = models.ImageField(upload_to='uploads/')

class LabeledImage(models.Model):
    image_path = models.CharField(max_length=255)
    label = models.CharField(max_length=10)  # 'Yes' or 'No'