from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.dashboard, name='dashboard'),

    path('jobcards/', views.jobcards, name='jobcards'),
    path('jobcards/add/', views.add_jobcard, name='add_jobcard'),

    path('inventory/', views.inventory, name='inventory'),
    path('billing/', views.billing, name='billing'),
]
