
from django.contrib import admin
from django.urls import path, include

from core.views import index, inventory, bills, job_list

urlpatterns = [
    path('', index, name = 'index'),
    path('inventory/', inventory, name = 'inventory'),
    path('admin/', admin.site.urls),
]
