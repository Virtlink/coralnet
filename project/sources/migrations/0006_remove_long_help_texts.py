# Generated by Django 4.1.10 on 2024-04-29 19:37

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Remove long help texts from model fields, so that wording edits don't
    need new migrations going forward. Leave long help texts to forms and
    templates instead.
    """

    dependencies = [
        ('sources', '0005_source_contenttype_app_change'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='default_point_generation_method',
            field=models.CharField(default='m_200', max_length=50, verbose_name='Point generation method'),
        ),
        migrations.AlterField(
            model_name='source',
            name='enable_robot_classifier',
            field=models.BooleanField(default=True, verbose_name='Enable robot classifier'),
        ),
        migrations.AlterField(
            model_name='source',
            name='image_annotation_area',
            field=models.CharField(max_length=50, null=True, verbose_name='Default image annotation area'),
        ),
    ]
