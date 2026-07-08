from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import AdditionalCharge, InventoryItem, JobCard, WorkshopProfile


class RegistrationForm(UserCreationForm):
    """Signup form: creates the auth User; profile fields are collected alongside."""

    class Meta:
        model = User
        fields = ['username']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class WorkshopProfileForm(forms.ModelForm):
    class Meta:
        model = WorkshopProfile
        fields = ['shop_name', 'phone_number', 'latitude', 'longitude', 'address']
        widgets = {
            'shop_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean_latitude(self):
        lat = self.cleaned_data['latitude']
        if not -90 <= lat <= 90:
            raise forms.ValidationError('Latitude must be between -90 and 90.')
        return lat

    def clean_longitude(self):
        lon = self.cleaned_data['longitude']
        if not -180 <= lon <= 180:
            raise forms.ValidationError('Longitude must be between -180 and 180.')
        return lon


class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['part_name', 'sku', 'quantity', 'b2b_price']
        widgets = {
            'part_name': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'b2b_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class JobCardForm(forms.ModelForm):
    class Meta:
        model = JobCard
        fields = ['vehicle_number', 'customer_complaint']
        widgets = {
            'vehicle_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. MH-12-AB-1234'}),
            'customer_complaint': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Describe customer complaints...'}),
        }


class JobCardStatusForm(forms.ModelForm):
    """Lightweight form for updating just the status from the job-card list."""

    class Meta:
        model = JobCard
        fields = ['status']
        widgets = {'status': forms.Select(attrs={'class': 'form-select form-select-sm'})}


class AdditionalChargeForm(forms.ModelForm):
    """Add a non-part charge (labour, diagnostics, consumables) to a bill."""

    class Meta:
        model = AdditionalCharge
        fields = ['description', 'amount']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Labour charge, Diagnostics fee',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00',
            }),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None or amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        return amount
