# Generated by Django 4.1.10 on 2024-05-17 07:08

from django.db import migrations


def populate_deployed_classifier(apps, schema_editor):
    Source = apps.get_model('sources', 'Source')
    Classifier = apps.get_model('vision_backend', 'Classifier')

    for source in Source.objects.all():
        # Inlining the implementation of the last_accepted_classifier property,
        # which isn't available in migrations.
        try:
            classifier = source.classifier_set.filter(status='AC').latest('pk')
        except Classifier.DoesNotExist:
            classifier = None

        if classifier:
            source.deployed_classifier = classifier
            # The custom save() method should also populate
            # deployed_source_id.
            source.save()


class Migration(migrations.Migration):
    """
    This migration assumes the deployed_classifier field was just added
    and that no one got the chance to use it yet.
    """

    dependencies = [
        ('sources', '0009_add_deployed_classifier_and_more'),
    ]

    operations = [
        migrations.RunPython(
            populate_deployed_classifier, migrations.RunPython.noop),
    ]
