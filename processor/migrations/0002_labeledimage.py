# Generated by Django 5.0.3 on 2024-03-13 03:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("processor", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LabeledImage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("image_path", models.CharField(max_length=255)),
                ("label", models.CharField(max_length=10)),
            ],
        ),
    ]
