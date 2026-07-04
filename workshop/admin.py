from django.contrib import admin

from .models import InventoryItem, JobCard, WorkshopProfile


@admin.register(WorkshopProfile)
class WorkshopProfileAdmin(admin.ModelAdmin):
    list_display = ('shop_name', 'user', 'phone_number', 'latitude', 'longitude')
    search_fields = ('shop_name', 'user__username')


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('part_name', 'workshop', 'sku', 'quantity', 'b2b_price')
    list_filter = ('workshop',)
    search_fields = ('part_name', 'sku')


@admin.register(JobCard)
class JobCardAdmin(admin.ModelAdmin):
    list_display = ('vehicle_number', 'workshop', 'status', 'total_bill', 'created_at')
    list_filter = ('status', 'workshop')
    search_fields = ('vehicle_number',)
