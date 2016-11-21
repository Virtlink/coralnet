# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2016-11-21 10:20
from __future__ import unicode_literals

from django.db import migrations
from accounts.models import get_random_gravatar_hash


def make_distinct_gravatar_hashes(apps, schema_editor):
    # The migration 0007_avatar_additions added the gravatar hash field,
    # specifying a function to run to fill in default values for existing rows.
    # The idea was to generate a random hash for each profile. Unfortunately,
    # what actually happened was that the random hash function was run only
    # once, and the result value was applied to all profiles, thus giving every
    # profile the same gravatar.
    #
    # This function properly generates a new hash for each profile.
    Profile = apps.get_model('accounts', 'Profile')
    profiles = Profile.objects.all()
    profile_count = profiles.count()

    for num, profile in enumerate(profiles, 1):
        profile.random_gravatar_hash = get_random_gravatar_hash()
        profile.save()

        # Give progress updates every so often.
        if num % 100 == 0:
            print("Updated {num} of {count} DB entries...".format(
                num=num, count=profile_count))


def do_nothing(apps, schema_editor):
    # There isn't really a reverse operation that makes sense here.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_update_avatar_filepaths'),
    ]

    operations = [
        migrations.RunPython(
            make_distinct_gravatar_hashes, do_nothing),
    ]
