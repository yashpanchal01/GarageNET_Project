from django.shortcuts import render, redirect
from .models import JobCard

def dashboard(request):
    return render(request, 'core/index.html', {
        'active_page': 'dashboard',
        'page_title': 'Dashboard'
    })

def jobcards(request):
    jobcards = JobCard.objects.all()
    return render(request, 'core/jobcards.html', {
        'jobcards': jobcards,
        'active_page': 'jobcards',
        'page_title': 'Job Cards'
    })

def inventory(request):
    return render(request, 'core/inventory.html', {
        'active_page': 'inventory',
        'page_title': 'Inventory'
    })

def billing(request):
    return render(request, 'core/bills.html', {
        'active_page': 'billing',
        'page_title': 'Billing'
    })
    
def login_ui(request):
    return render(request, 'core/login.html', {'active_page': ''})

def register_ui(request):
    return render(request, 'core/register.html', {'active_page': ''})

def gsearch_ui(request):
    return render(request, 'core/gsearch.html', {'active_page': ''})

def create_invoice_ui(request):
    return render(request, 'core/create_invoice.html', {'active_page': 'billing'})




def add_jobcard(request):
    if request.method == 'POST':
        JobCard.objects.create(
            customer_name=request.POST.get('customer_name'),
            vehicle_number=request.POST.get('vehicle_number'),
            issue=request.POST.get('issue'),
        )
        return redirect('jobcards')

    return render(request, 'core/add_jobcard.html', {'active_page': 'jobcards'})
