from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class WorkshopProfile(models.Model):
    """A single automobile workshop, tied 1:1 to a Django auth User."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='workshop')
    shop_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20)
    latitude = models.FloatField(
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
        help_text='Decimal degrees, e.g. 18.5204'
    )
    longitude = models.FloatField(
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
        help_text='Decimal degrees, e.g. 73.8567'
    )
    address = models.TextField(blank=True)

    def __str__(self):
        return self.shop_name



class InventoryItem(models.Model):
    """A single part/SKU held in a workshop's stock ledger."""

    workshop = models.ForeignKey(
        WorkshopProfile, on_delete=models.CASCADE, related_name='inventory'
    )
    part_name = models.CharField(max_length=150)
    sku = models.CharField(max_length=60, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    b2b_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['part_name']

    def __str__(self):
        return f'{self.part_name} ({self.quantity})'


class JobCard(models.Model):
    """A vehicle repair job flowing through the workshop's workflow."""

    class Status(models.TextChoices):
        RECEIVED = 'RECEIVED', 'Received'
        IN_PROGRESS = 'IN_PROGRESS', 'In-Progress'
        WAITING_FOR_PARTS = 'WAITING_FOR_PARTS', 'Waiting-for-Parts'
        READY = 'READY', 'Ready'

    workshop = models.ForeignKey(
        WorkshopProfile, on_delete=models.CASCADE, related_name='job_cards'
    )
    vehicle_number = models.CharField(max_length=20)
    customer_complaint = models.TextField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.RECEIVED
    )
    total_bill = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.vehicle_number} [{self.get_status_display()}]'

    def recalculate_total(self):
        """Recalculate total bill from all line items and save."""
        from django.db.models import F, Sum
        total = self.line_items.aggregate(
            total=Sum(F('quantity') * F('unit_price'), output_field=models.DecimalField())
        )['total'] or 0
        self.total_bill = total
        self.save(update_fields=['total_bill'])

    def delete(self, *args, **kwargs):
        from django.db import transaction
        with transaction.atomic():
            for item in self.line_items.all():
                if item.inventory_item:
                    from django.db.models import F
                    InventoryItem.objects.filter(pk=item.inventory_item.pk).update(
                        quantity=F('quantity') + item.quantity
                    )
            super().delete(*args, **kwargs)


class JobCardLineItem(models.Model):
    """A single inventory item/part consumed on a vehicle's JobCard."""

    job_card = models.ForeignKey(
        JobCard, on_delete=models.CASCADE, related_name='line_items'
    )
    inventory_item = models.ForeignKey(
        InventoryItem, on_delete=models.SET_NULL, null=True, related_name='line_items'
    )
    part_name = models.CharField(max_length=150)
    sku = models.CharField(max_length=60, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.part_name} (x{self.quantity}) on {self.job_card.vehicle_number}'

    @property
    def total_price(self):
        return self.quantity * self.unit_price

    def delete(self, *args, **kwargs):
        from django.db import transaction
        with transaction.atomic():
            if self.inventory_item:
                from django.db.models import F
                InventoryItem.objects.filter(pk=self.inventory_item.pk).update(
                    quantity=F('quantity') + self.quantity
                )
            super().delete(*args, **kwargs)


