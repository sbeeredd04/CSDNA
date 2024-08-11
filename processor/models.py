from django.db import models

class ImageUpload(models.Model):
    image = models.ImageField(upload_to='uploads/')

class LabeledImage(models.Model):
    image_path = models.CharField(max_length=255)
    label = models.CharField(max_length=50)  # Allow for different categories

class Category(models.Model):
    key = models.CharField(max_length=50, unique=True, db_index=True)  # db_index added for faster lookups
    count = models.IntegerField(default=0)

    @classmethod
    def update_category_count(cls, key, count):
        # Update or create the count for the given category key
        category, created = cls.objects.get_or_create(key=key)
        category.count = count
        category.save()
