from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('inventory/', views.inventory_ledger, name='inventory'),
    path('job-cards/', views.job_cards, name='job_cards'),
    path('part-search/', views.part_search, name='part_search'),
]
