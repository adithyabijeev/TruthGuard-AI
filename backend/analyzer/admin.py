from django.contrib import admin
from .models import Scan

@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'severity', 'risk_score', 'source', 'created_at')
    list_filter = ('severity', 'source')
    search_fields = ('title', 'content', 'verdict')
