from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    AdditionalChargeForm,
    InventoryItemForm,
    JobCardForm,
    JobCardStatusForm,
    RegistrationForm,
    WorkshopProfileForm,
)
from .models import (
    AdditionalCharge,
    InventoryItem,
    JobCard,
    JobCardActivity,
    JobCardLineItem,
    WorkshopProfile,
)
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


def _build_job_distribution(total, in_progress, ready, others):
    """Turn raw status counts into donut-chart segments.

    The SVG donut uses a circle of r=15.915 (circumference ~= 100), so each
    segment's ``dash``/``gap``/``offset`` are expressed directly as percentages.
    ``offset = 25 - cumulative`` rotates drawing to start at the 12 o'clock mark.
    """
    segments = [
        ('In-progress', '#0d6efd', in_progress),
        ('Ready', '#198754', ready),
        ('Others', '#6c757d', others),
    ]
    result = []
    cumulative = 0.0
    for label, color, count in segments:
        percent = (count / total * 100) if total else 0
        result.append({
            'label': label,
            'color': color,
            'count': count,
            'percent': round(percent, 1),
            'dash': round(percent, 2),
            'gap': round(100 - percent, 2),
            'offset': round((25 - cumulative) % 100, 2),
        })
        cumulative += percent
    return result


@login_required
def dashboard(request):
    workshop = _get_workshop(request)
    if workshop is None:
        messages.warning(request, 'Set up your workshop profile to get started.')
        return redirect('profile')

    low_stock = workshop.inventory.filter(quantity__lt=LOW_STOCK_THRESHOLD)

    jobs = workshop.job_cards
    total_jobs = jobs.count()
    in_progress = jobs.filter(status=JobCard.Status.IN_PROGRESS).count()
    ready = jobs.filter(status=JobCard.Status.READY).count()
    others = total_jobs - in_progress - ready

    context = {
        'workshop': workshop,
        'active_job_cards': jobs.exclude(status=JobCard.Status.READY).count(),
        'low_stock_items': low_stock.count(),
        'low_stock_list': low_stock[:8],
        'inventory_count': workshop.inventory.count(),
        'low_stock_threshold': LOW_STOCK_THRESHOLD,
        'recent_jobs': jobs.all()[:5],
        'total_jobs': total_jobs,
        'job_distribution': _build_job_distribution(total_jobs, in_progress, ready, others),
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
            JobCardActivity.log(
                job, JobCardActivity.EventType.CREATED,
                f'Job card created for {job.vehicle_number}. '
                f'Initial status: {job.get_status_display()}.'
            )
            messages.success(request, f'Created job card for {job.vehicle_number}.')
            return redirect('job_cards')
    elif request.method == 'POST' and action == 'update_status':
        job = get_object_or_404(JobCard, pk=request.POST.get('job_id'), workshop=workshop)
        previous = job.get_status_display()
        status_form = JobCardStatusForm(request.POST, instance=job)
        if status_form.is_valid():
            status_form.save()
            JobCardActivity.log(
                job, JobCardActivity.EventType.STATUS_CHANGED,
                f'Status changed from {previous} to {job.get_status_display()}.'
            )
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
    radius_str = request.GET.get('radius', '50').strip()
    try:
        radius = float(radius_str)
    except ValueError:
        radius = 50.0

    results = []
    if query:
        import math
        center_lat = workshop.latitude
        center_lon = workshop.longitude

        # Bounding box coordinates calculation
        delta_lat = radius / 111.0
        # Protect against division by zero/invalid cos arguments at poles
        cos_lat = math.cos(math.radians(center_lat))
        delta_lon = radius / (111.0 * cos_lat) if abs(cos_lat) > 0.001 else 360.0

        min_lat = center_lat - delta_lat
        max_lat = center_lat + delta_lat
        min_lon = center_lon - delta_lon
        max_lon = center_lon + delta_lon

        # Build database expression for Haversine distance in SQL
        from django.db.models import F
        from django.db.models.functions import ASin, Cos, Radians, Sin, Sqrt

        dlat = Radians(F('workshop__latitude') - center_lat)
        dlon = Radians(F('workshop__longitude') - center_lon)
        lat1 = Radians(center_lat)
        lat2 = Radians(F('workshop__latitude'))

        # a = sin^2(dlat/2) + cos(lat1)*cos(lat2)*sin^2(dlon/2)
        a = (
            Sin(dlat / 2.0) * Sin(dlat / 2.0) +
            Cos(lat1) * Cos(lat2) * Sin(dlon / 2.0) * Sin(dlon / 2.0)
        )
        distance_expr = 2.0 * 6371.0 * ASin(Sqrt(a))

        matches = (
            InventoryItem.objects.filter(
                part_name__icontains=query,
                quantity__gt=0,
                workshop__latitude__range=(min_lat, max_lat),
                workshop__longitude__range=(min_lon, max_lon),
            )
            .exclude(workshop=workshop)
            .select_related('workshop')
            .annotate(distance_km=distance_expr)
            .filter(distance_km__lte=radius)
            .order_by('distance_km')
        )

        for item in matches:
            results.append({
                'item': item,
                'profile': item.workshop,
                'distance_km': round(item.distance_km, 1)
            })

    context = {
        'workshop': workshop,
        'query': query,
        'radius': radius,
        'results': results,
    }
    return render(request, 'workshop/part_search.html', context)


@login_required
def job_card_detail(request, pk):
    """View details of a single Job Card, including line items and adding/removing parts."""
    workshop = _get_workshop(request)
    if workshop is None:
        return redirect('dashboard')

    job_card = get_object_or_404(JobCard, pk=pk, workshop=workshop)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_part':
            inventory_item_id = request.POST.get('inventory_item')
            qty_str = request.POST.get('quantity', '1').strip()
            try:
                quantity = int(qty_str)
                if quantity <= 0:
                    raise ValueError
            except ValueError:
                messages.error(request, 'Please enter a valid positive quantity.')
                return redirect('job_card_detail', pk=pk)

            try:
                with transaction.atomic():
                    # Lock inventory item using select_for_update
                    inventory_item = get_object_or_404(
                        InventoryItem.objects.select_for_update(),
                        pk=inventory_item_id,
                        workshop=workshop
                    )

                    if inventory_item.quantity < quantity:
                        raise ValidationError(
                            f'Cannot add part. Only {inventory_item.quantity} items available in stock, but {quantity} were requested.'
                        )

                    # Deduct stock
                    inventory_item.quantity -= quantity
                    inventory_item.save(update_fields=['quantity'])

                    # Create line item snapshot
                    JobCardLineItem.objects.create(
                        job_card=job_card,
                        inventory_item=inventory_item,
                        part_name=inventory_item.part_name,
                        sku=inventory_item.sku,
                        quantity=quantity,
                        unit_price=inventory_item.b2b_price
                    )

                    # Recalculate bill total
                    job_card.recalculate_total()
                    JobCardActivity.log(
                        job_card, JobCardActivity.EventType.PART_ADDED,
                        f'Added part "{inventory_item.part_name}" '
                        f'(x{quantity} @ ₹{inventory_item.b2b_price}).'
                    )
                    messages.success(request, f'Added "{inventory_item.part_name}" to the job card.')
            except ValidationError as e:
                messages.error(request, e.message)
            return redirect('job_card_detail', pk=pk)

        elif action == 'remove_part':
            line_item_id = request.POST.get('line_item_id')
            try:
                with transaction.atomic():
                    line_item = get_object_or_404(
                        JobCardLineItem,
                        pk=line_item_id,
                        job_card=job_card
                    )
                    part_name = line_item.part_name
                    part_qty = line_item.quantity
                    # Stock replenishment is handled automatically inside JobCardLineItem.delete()
                    line_item.delete()

                    # Recalculate bill total
                    job_card.recalculate_total()
                    JobCardActivity.log(
                        job_card, JobCardActivity.EventType.PART_REMOVED,
                        f'Removed part "{part_name}" (x{part_qty}); stock replenished.'
                    )
                    messages.success(request, f'Removed "{part_name}" from the job card.')
            except Exception:
                messages.error(request, 'Failed to remove part.')
            return redirect('job_card_detail', pk=pk)

        elif action == 'update_status':
            previous = job_card.get_status_display()
            status_form = JobCardStatusForm(request.POST, instance=job_card)
            if status_form.is_valid():
                status_form.save()
                JobCardActivity.log(
                    job_card, JobCardActivity.EventType.STATUS_CHANGED,
                    f'Status changed from {previous} to {job_card.get_status_display()}.'
                )
                messages.success(request, f'{job_card.vehicle_number} -> {job_card.get_status_display()}.')
            return redirect('job_card_detail', pk=pk)

    # Active inventory items only (quantity > 0)
    inventory_items = workshop.inventory.filter(quantity__gt=0)
    context = {
        'workshop': workshop,
        'job_card': job_card,
        'line_items': job_card.line_items.all(),
        'additional_charges': job_card.additional_charges.all(),
        'inventory_items': inventory_items,
        'status_form': JobCardStatusForm(instance=job_card),
        'activities': job_card.activities.all(),
        'is_ready': job_card.status == JobCard.Status.READY,
    }
    return render(request, 'workshop/job_card_detail.html', context)


@login_required
def job_card_bill(request, pk):
    """Render the printable bill/invoice and manage additional (labour) charges."""
    workshop = _get_workshop(request)
    if workshop is None:
        return redirect('dashboard')

    job_card = get_object_or_404(JobCard, pk=pk, workshop=workshop)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_charge':
            form = AdditionalChargeForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    charge = form.save(commit=False)
                    charge.job_card = job_card
                    charge.save()
                    job_card.recalculate_total()
                    JobCardActivity.log(
                        job_card, JobCardActivity.EventType.CHARGE_ADDED,
                        f'Added charge "{charge.description}" (₹{charge.amount}).'
                    )
                messages.success(request, f'Added charge "{charge.description}".')
                return redirect('job_card_bill', pk=pk)
            # Fall through and re-render the bill with the bound (invalid) form.
        elif action == 'remove_charge':
            charge = get_object_or_404(
                AdditionalCharge, pk=request.POST.get('charge_id'), job_card=job_card
            )
            description = charge.description
            with transaction.atomic():
                charge.delete()
                job_card.recalculate_total()
                JobCardActivity.log(
                    job_card, JobCardActivity.EventType.CHARGE_REMOVED,
                    f'Removed charge "{description}".'
                )
            messages.success(request, f'Removed charge "{description}".')
            return redirect('job_card_bill', pk=pk)
        else:
            form = AdditionalChargeForm()
    else:
        form = AdditionalChargeForm()

    # Record the first time a bill is generated for this job card.
    if not job_card.activities.filter(
        event_type=JobCardActivity.EventType.INVOICE_GENERATED
    ).exists():
        JobCardActivity.log(
            job_card, JobCardActivity.EventType.INVOICE_GENERATED,
            f'Bill generated. Total: ₹{job_card.total_bill}.'
        )

    context = {
        'workshop': workshop,
        'job_card': job_card,
        'line_items': job_card.line_items.all(),
        'additional_charges': job_card.additional_charges.all(),
        'charge_form': form,
    }
    return render(request, 'workshop/job_card_bill.html', context)


