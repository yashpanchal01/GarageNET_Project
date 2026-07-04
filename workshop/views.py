from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    InventoryItemForm,
    JobCardForm,
    JobCardStatusForm,
    RegistrationForm,
    WorkshopProfileForm,
)
from .models import InventoryItem, JobCard, WorkshopProfile
from .utils import haversine_km

LOW_STOCK_THRESHOLD = 2


def _get_workshop(request):
    """Return the logged-in user's WorkshopProfile, or None if not set up yet."""
    return WorkshopProfile.objects.filter(user=request.user).first()


def register(request):
    """Self-service signup: creates the User and their WorkshopProfile together."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        user_form = RegistrationForm(request.POST)
        profile_form = WorkshopProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user = user_form.save()
                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()
            login(request, user)
            messages.success(request, f'Welcome to GarageNET, {profile.shop_name}!')
            return redirect('dashboard')
    else:
        user_form = RegistrationForm()
        profile_form = WorkshopProfileForm()

    return render(request, 'registration/register.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


@login_required
def profile(request):
    """Create or edit the logged-in user's workshop profile."""
    workshop = _get_workshop(request)

    if request.method == 'POST':
        form = WorkshopProfileForm(request.POST, instance=workshop)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, 'Workshop profile saved.')
            return redirect('dashboard')
    else:
        form = WorkshopProfileForm(instance=workshop)

    return render(request, 'workshop/profile.html', {'workshop': workshop, 'form': form})


@login_required
def dashboard(request):
    workshop = _get_workshop(request)
    if workshop is None:
        messages.warning(request, 'Set up your workshop profile to get started.')
        return redirect('profile')

    low_stock = workshop.inventory.filter(quantity__lt=LOW_STOCK_THRESHOLD)
    context = {
        'workshop': workshop,
        'active_job_cards': workshop.job_cards.exclude(
            status=JobCard.Status.READY
        ).count(),
        'low_stock_items': low_stock.count(),
        'low_stock_list': low_stock[:8],
        'low_stock_threshold': LOW_STOCK_THRESHOLD,
        'recent_jobs': workshop.job_cards.all()[:5],
    }
    return render(request, 'workshop/dashboard.html', context)


@login_required
def inventory_ledger(request):
    workshop = _get_workshop(request)
    if workshop is None:
        return redirect('dashboard')

    if request.method == 'POST' and request.POST.get('action') == 'delete':
        item = get_object_or_404(
            InventoryItem, pk=request.POST.get('item_id'), workshop=workshop
        )
        item.delete()
        messages.success(request, f'Removed "{item.part_name}" from the ledger.')
        return redirect('inventory')

    # Add a new item, or update an existing one when ?edit=<id> is in play.
    edit_id = request.GET.get('edit') or request.POST.get('edit')
    instance = None
    if edit_id:
        instance = get_object_or_404(InventoryItem, pk=edit_id, workshop=workshop)

    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=instance)
        if form.is_valid():
            item = form.save(commit=False)
            item.workshop = workshop
            item.save()
            messages.success(request, f'Saved "{item.part_name}".')
            return redirect('inventory')
    else:
        form = InventoryItemForm(instance=instance)

    context = {
        'workshop': workshop,
        'items': workshop.inventory.all(),
        'form': form,
        'editing': instance,
        'low_stock_threshold': LOW_STOCK_THRESHOLD,
    }
    return render(request, 'workshop/inventory.html', context)


@login_required
def job_cards(request):
    workshop = _get_workshop(request)
    if workshop is None:
        return redirect('dashboard')

    action = request.POST.get('action')
    if request.method == 'POST' and action == 'create':
        form = JobCardForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.workshop = workshop
            job.save()
            messages.success(request, f'Created job card for {job.vehicle_number}.')
            return redirect('job_cards')
    elif request.method == 'POST' and action == 'update_status':
        job = get_object_or_404(JobCard, pk=request.POST.get('job_id'), workshop=workshop)
        status_form = JobCardStatusForm(request.POST, instance=job)
        if status_form.is_valid():
            status_form.save()
            messages.success(request, f'{job.vehicle_number} -> {job.get_status_display()}.')
        return redirect('job_cards')
    else:
        form = JobCardForm()

    context = {
        'workshop': workshop,
        'form': form,
        'jobs': workshop.job_cards.all(),
        'status_form': JobCardStatusForm(),
    }
    return render(request, 'workshop/job_cards.html', context)


@login_required
def part_search(request):
    """P2P part search: find the part in *other* workshops, nearest first."""
    workshop = _get_workshop(request)
    if workshop is None:
        return redirect('dashboard')

    query = request.GET.get('q', '').strip()
    results = []
    if query:
        matches = (
            InventoryItem.objects.filter(part_name__icontains=query, quantity__gt=0)
            .exclude(workshop=workshop)
            .select_related('workshop')
        )
        for item in matches:
            distance = haversine_km(
                workshop.latitude,
                workshop.longitude,
                item.workshop.latitude,
                item.workshop.longitude,
            )
            results.append({
                'item': item,
                'profile': item.workshop,
                'distance_km': round(distance, 1)
            })
        results.sort(key=lambda r: r['distance_km'])

    context = {'workshop': workshop, 'query': query, 'results': results}
    return render(request, 'workshop/part_search.html', context)
