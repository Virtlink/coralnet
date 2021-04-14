# Generated by Django 1.11.22 on 2019-07-30 19:24
from django.conf import settings
from django.db import migrations


def set_site_name(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')

    # By default, Django creates one Site, initializing it to pk=SITE_ID
    # (or 1 if no SITE_ID) and a default name/domain of example.com.
    # Here we set the name/domain to our own, using a data migration, as
    # suggested by the Django docs:
    # https://docs.djangoproject.com/en/dev/ref/contrib/sites/#enabling-the-sites-framework
    #
    # Before running this migration, your database's Site object should have
    # a pk matching the SITE_ID. You can check this from manage.py shell:
    # `from django.contrib.sites.models import Site`
    # `Site.objects.all()[0].pk`
    # If it doesn't match, change the pk of your database's Site to SITE_ID.
    site = Site.objects.get(pk=settings.SITE_ID)
    site.name = "CoralNet"
    site.domain = 'coralnet.ucsd.edu'
    site.save()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
    ]

    # Reverse operation is a no-op. The forward operation doesn't care if the
    # site name is already set correctly.
    operations = [
        migrations.RunPython(set_site_name, migrations.RunPython.noop),
    ]
