from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [migrations.CreateModel(name='Scan', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('title', models.CharField(blank=True, max_length=300)),
        ('content', models.TextField()),
        ('source', models.CharField(blank=True, max_length=120)),
        ('risk_score', models.PositiveSmallIntegerField(default=0)),
        ('severity', models.CharField(default='LOW', max_length=30)),
        ('verdict', models.CharField(default='No strong fraud pattern detected', max_length=120)),
        ('analysis', models.JSONField(default=dict)),
        ('created_at', models.DateTimeField(auto_now_add=True)),
    ], options={'ordering': ['-created_at']}),]
