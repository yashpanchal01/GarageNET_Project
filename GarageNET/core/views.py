from django.shortcuts import render, redirect
from .models import JobCard


# ---------- DASHBOARD ----------
def dashboard(request):
    return render(request, 'core/index.html')


# ---------- INVENTORY ----------
def inventory(request):
    return render(request, 'core/inventory.html')


# ---------- JOB CARDS LIST ----------
def jobcards(request):
    jobcards = JobCard.objects.all()
    return render(request, 'core/jobcards.html', {
        'jobcards': jobcards
    })


# ---------- ADD JOBCARD ----------
def add_jobcard(request):
    if request.method == 'POST':
        JobCard.objects.create(
            customer_name=request.POST.get('customer_name'),
            vehicle_number=request.POST.get('vehicle_number'),
            issue=request.POST.get('issue'),
        )
        return redirect('jobcards')

    # GET request
    return render(request, 'core/add_jobcard.html')


# ---------- BILLING (placeholder) ----------
def bills(request):
    return render(request, 'core/bills.html')
