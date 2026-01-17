from django.shortcuts import render, redirect
from .models import JobCard

def dashboard(request):
    return render(request, 'core/index.html', {'active_page': 'dashboard'})

def inventory(request):
    return render(request, 'core/inventory.html', {'active_page': 'inventory'})

def billing(request):
    return render(request, 'core/bills.html', {'active_page': 'billing'})

def jobcards(request):
    jobcards = JobCard.objects.all()
    return render(request, 'core/jobcards.html', {
        'jobcards': jobcards,
        'active_page': 'jobcards'
    })

def add_jobcard(request):
    if request.method == 'POST':
        JobCard.objects.create(
            customer_name=request.POST.get('customer_name'),
            vehicle_number=request.POST.get('vehicle_number'),
            issue=request.POST.get('issue'),
        )
        return redirect('jobcards')

    return render(request, 'core/add_jobcard.html', {'active_page': 'jobcards'})
