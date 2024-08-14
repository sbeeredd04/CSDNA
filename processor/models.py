from django.db import models

class ImageUpload(models.Model):
    image = models.ImageField(upload_to='uploads/')

class LabeledImage(models.Model):
    image_path = models.CharField(max_length=255)
    label = models.CharField(max_length=50)  # Allow for different categories

class Category(models.Model):
    key = models.CharField(max_length=50, unique=True, db_index=True)  # The key (e.g., "1", "2", etc.)
    name = models.CharField(max_length=100, default='Category')  # The default name
    count = models.IntegerField(default=0)

    @classmethod
    def update_category_count(cls, key, increment_by):
        # Fetch the category object or create it if it doesn't exist
        category, created = cls.objects.get_or_create(key=key)
        # Increment the existing count
        if not created:
            category.count += increment_by
        else:
            category.count = increment_by  # Initialize count if created
        # Save the updated category
        category.save()
        print(f"Category {key} Updated: Count - {category.count}, Name - {category.name}")

