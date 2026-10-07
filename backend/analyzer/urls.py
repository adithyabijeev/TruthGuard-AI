from django.urls import path
from . import views
urlpatterns = [
    path('health/', views.health),
    path('analyze/', views.analyze_view),
    path('scans/', views.scans),
    path('stats/', views.stats),
]
