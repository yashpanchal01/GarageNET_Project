from django.shortcuts import render


def index(request):
    return render(request, 'core/index.html')


def inventory(request):
    return render(request, 'core/inventory.html')
    

def bills(request):
    pass
     

def job_list(request):
    pass
     




#Following is the list of functions we GEMINI told us to have. 
'''
# --- Auth ---
def signup(request):
    pass
def login_view(request):
    pass
def logout_view(request):
    pass
# --- Dashboard ---
@login_required
def dashboard(request):
    pass
# --- Inventory ---
@login_required
def inventory_list(request):
    pass
@login_required
def inventory_add(request):
    pass
@login_required
def inventory_edit(request, id):
    pass
@login_required
def inventory_delete(request, id):
    pass
# --- Jobs ---
@login_required
def job_list(request):
    pass
@login_required
def job_create(request):
    pass
@login_required
def job_update_status(request, id):
    pass
# --- Billing ---
@login_required
def bill_create(request, job_id):
    pass
@login_required
def bill_detail(request, id):
    pass
# --- Search ---
def search(request):
    pass'''