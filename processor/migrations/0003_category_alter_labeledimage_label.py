# Generated by Django 5.1 on 2024-08-11 03:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("processor", "0002_labeledimage"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
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
                ("key", models.CharField(db_index=True, max_length=50, unique=True)),
                ("count", models.IntegerField(default=0)),
            ],
        ),
        migrations.AlterField(
            model_name="labeledimage",
            name="label",
            field=models.CharField(max_length=50),
        ),
    ]