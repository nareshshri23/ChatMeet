# Generated by Django 3.2.19 on 2025-01-24 10:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_auto_20250123_1609'),
    ]

    operations = [
        migrations.AddField(
            model_name='guestuser',
            name='about',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='guestuser',
            name='emoji',
            field=models.CharField(default='😊', max_length=10),
        ),
        migrations.AddField(
            model_name='guestuser',
            name='preferences',
            field=models.TextField(blank=True),
        ),
    ]
