from images.models import Source, Image, Metadata
from django.contrib import admin
from guardian.admin import GuardedModelAdmin

@admin.register(Source)
class SourceAdmin(GuardedModelAdmin):
    list_display = ('name', 'visibility', 'create_date')

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('original_file', 'source', 'metadata')

@admin.register(Metadata)
class MetadataAdmin(admin.ModelAdmin):
    list_display = ('name', 'value1', 'value2', 'value3', 'value4', 'value5')
