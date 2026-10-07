from django.db import models

class Scan(models.Model):
    title = models.CharField(max_length=300, blank=True)
    content = models.TextField()
    source = models.CharField(max_length=120, blank=True)
    risk_score = models.PositiveSmallIntegerField(default=0)
    severity = models.CharField(max_length=30, default='LOW')
    verdict = models.CharField(max_length=120, default='No strong fraud pattern detected')
    analysis = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.severity} {self.risk_score} - {self.title or "Untitled"}'
