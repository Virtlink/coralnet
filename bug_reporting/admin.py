from bug_reporting.models import Feedback
from django.contrib import admin

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('comment', 'type', 'user', 'date', 'error_id')
    #TODO: limit comment display to some number of characters
