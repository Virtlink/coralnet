# Generated by Django 4.1.10 on 2024-04-18 09:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('images', '0038_rename_source_table'),
        ('vision_backend', '0022_source_fk_app_change'),
    ]

    operations = [
        # Re-enable sources.source FK constraints.
        migrations.AlterField(
            model_name='classifier',
            name='source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sources.source', db_constraint=True),
        ),
        migrations.AlterField(
            model_name='score',
            name='source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sources.source', db_constraint=True),
        ),
    ]
