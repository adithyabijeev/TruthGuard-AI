from rest_framework import serializers
from .models import Scan

class ScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scan
        fields = ['id', 'title', 'content', 'source', 'risk_score', 'severity', 'verdict', 'analysis', 'created_at']

class AnalyzeSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True, max_length=300)
    content = serializers.CharField()
    source = serializers.CharField(required=False, allow_blank=True, max_length=120)
