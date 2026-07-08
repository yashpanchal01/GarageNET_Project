from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('inventory/', views.inventory_ledger, name='inventory'),
    path('job-cards/', views.job_cards, name='job_cards'),
    path('job-cards/<int:pk>/', views.job_card_detail, name='job_card_detail'),
    path('job-cards/<int:pk>/bill/', views.job_card_bill, name='job_card_bill'),
    path('part-search/', views.part_search, name='part_search'),
]
