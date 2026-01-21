from django.db import models
from django.contrib.auth.models import User

class GarageProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='garage_profile')
    garage_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address = models.TextField()

    def __str__(self):
        return self.garage_name

class InventoryItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory')
    part_name = models.CharField(max_length=255)
    part_number = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    supplier = models.CharField(max_length=255)
    quantity = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    min_stock = models.IntegerField(default=5)

    def __str__(self):
        return f"{self.part_name} ({self.part_number})"

    @property
    def is_low_stock(self):
        return self.quantity <= self.min_stock

class Bill(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bills')
    bill_number = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=255)
    vehicle_number = models.CharField(max_length=50)
    date = models.DateField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return self.bill_number

class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    part_name = models.CharField(max_length=255) # Storing name to preserve history even if part deleted
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.part_name} x {self.quantity}"

class JobCard(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in-progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_cards')
    job_number = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=255)
    vehicle_number = models.CharField(max_length=50)
    vehicle_model = models.CharField(max_length=100)
    issue = models.TextField()
    assigned_to = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    start_date = models.DateField()
    estimated_completion = models.DateField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.job_number
