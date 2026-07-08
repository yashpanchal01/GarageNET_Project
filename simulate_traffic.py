import requests
import re
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def extract_csrf(html):
    """Extract CSRF token from form hidden input."""
    match = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', html)
    if not match:
        match = re.search(r'value="([^"]+)"\s+name="csrfmiddlewaretoken"', html)
    return match.group(1) if match else None

def extract_job_card_ids(html):
    """Find job card detail links like /job-cards/12/"""
    return re.findall(r'/job-cards/(\d+)/', html)

def main():
    print("=" * 60)
    print("       GarageNET HTTP Traffic Simulator")
    print("=" * 60)
    print(f"Target Server: {BASE_URL}")
    
    session = requests.Session()
    
    # 1. Fetch Login Page
    print("\n[Step 1] Fetching login page...")
    t0 = time.time()
    try:
        r = session.get(f"{BASE_URL}/login/")
    except requests.exceptions.ConnectionError:
        print("[-] Error: Could not connect to Django development server.")
        print("    Please ensure the server is running on http://127.0.0.1:8000/")
        sys.exit(1)
        
    duration = time.time() - t0
    print(f"[+] Status: {r.status_code} | Time: {duration:.3f}s")
    
    csrf_token = extract_csrf(r.text)
    if not csrf_token:
        print("[-] Error: CSRF token not found on login page.")
        sys.exit(1)
    print(f"[+] CSRF Token: {csrf_token[:15]}...")

    # 2. Authenticate
    print("\n[Step 2] Logging in as 'demo_user'...")
    login_data = {
        "username": "demo_user",
        "password": "password123",
        "csrfmiddlewaretoken": csrf_token
    }
    t0 = time.time()
    r = session.post(
        f"{BASE_URL}/login/",
        data=login_data,
        headers={"Referer": f"{BASE_URL}/login/"}
    )
    duration = time.time() - t0
    # On successful login, Django redirects to '/' (status code 200 after redirect follow)
    print(f"[+] Status: {r.status_code} | Time: {duration:.3f}s")
    if "logout" not in r.text.lower():
        print("[-] Login failed. Please check seed credentials.")
        sys.exit(1)
    print("[+] Login Successful! Session established.")

    # 3. Fetch Dashboard Page
    print("\n[Step 3] Fetching main dashboard...")
    t0 = time.time()
    r = session.get(BASE_URL)
    duration = time.time() - t0
    print(f"[+] Status: {r.status_code} | Time: {duration:.3f}s")
    # Parse dashboard stats if present
    jobs_match = re.search(r'(\d+)\s+Active Job Card', r.text)
    if jobs_match:
        print(f"[+] Dashboard Stats: Active Job Cards = {jobs_match.group(1)}")

    # 4. Fetch Inventory Ledger
    print("\n[Step 4] Fetching inventory ledger page...")
    t0 = time.time()
    r = session.get(f"{BASE_URL}/inventory/")
    duration = time.time() - t0
    print(f"[+] Status: {r.status_code} | Time: {duration:.3f}s")
    
    # 5. Add a new item to inventory
    print("\n[Step 5] Adding a new item to inventory ledger...")
    csrf_token = extract_csrf(r.text)
    new_item_data = {
        "part_name": "Brake Caliper Gold Edition",
        "sku": "BC-GLD-99",
        "quantity": "5",
        "b2b_price": "2499.00",
        "csrfmiddlewaretoken": csrf_token
    }
    t0 = time.time()
    r = session.post(
        f"{BASE_URL}/inventory/",
        data=new_item_data,
        headers={"Referer": f"{BASE_URL}/inventory/"}
    )
    duration = time.time() - t0
    print(f"[+] Status: {r.status_code} | Time: {duration:.3f}s")
    if "Brake Caliper Gold Edition" in r.text:
        print("[+] Success: 'Brake Caliper Gold Edition' is verified in the stock list.")

    # 6. Test B2B Part Search
    print("\n[Step 6] Searching for 'Engine Oil' (radius 50km)...")
    t0 = time.time()
    r = session.get(f"{BASE_URL}/part-search/?q=Engine+Oil&radius=50")
    duration = time.time() - t0
    print(f"[+] Status: {r.status_code} | Time: {duration:.3f}s")
    # Look for matching locations in results
    matches = re.findall(r'([\d\.]+)\s*km\s*away', r.text)
    print(f"[+] Found {len(matches)} results from neighboring workshops inside 50km radius.")

    # 7. Create a new Job Card
    print("\n[Step 7] Creating a new Job Card...")
    r = session.get(f"{BASE_URL}/job-cards/")
    csrf_token = extract_csrf(r.text)
    job_data = {
        "action": "create",
        "vehicle_number": "MH-05-AA-7777",
        "customer_complaint": "Simulated traffic user: front squeaking brakes, check rotor surface.",
        "status": "RECEIVED",
        "csrfmiddlewaretoken": csrf_token
    }
    t0 = time.time()
    r = session.post(
        f"{BASE_URL}/job-cards/",
        data=job_data,
        headers={"Referer": f"{BASE_URL}/job-cards/"}
    )
    duration = time.time() - t0
    print(f"[+] Status: {r.status_code} | Time: {duration:.3f}s")

    # 8. Retrieve Job Card Details & Bill
    print("\n[Step 8] Reading Job Card details and billing invoice...")
    job_card_ids = extract_job_card_ids(r.text)
    if job_card_ids:
        newest_id = job_card_ids[0]
        print(f"[+] Accessing newly created Job Card #{newest_id}...")
        
        # Detail view
        t0 = time.time()
        r_detail = session.get(f"{BASE_URL}/job-cards/{newest_id}/")
        duration = time.time() - t0
        print(f"    - Detail status: {r_detail.status_code} | Time: {duration:.3f}s")
        
        # Bill view
        t0 = time.time()
        r_bill = session.get(f"{BASE_URL}/job-cards/{newest_id}/bill/")
        duration = time.time() - t0
        print(f"    - Bill status: {r_bill.status_code} | Time: {duration:.3f}s")
    else:
        print("[-] Warning: No job card detail links found on job cards list page.")

    # 9. Logout
    print("\n[Step 9] Logging out...")
    r = session.get(f"{BASE_URL}/")
    csrf_token = extract_csrf(r.text)
    t0 = time.time()
    r = session.post(
        f"{BASE_URL}/logout/",
        data={"csrfmiddlewaretoken": csrf_token},
        headers={"Referer": BASE_URL}
    )
    duration = time.time() - t0
    print(f"[+] Status: {r.status_code} | Time: {duration:.3f}s")
    print("[+] Logout Completed successfully.")
    
    print("\n" + "=" * 60)
    print("       Traffic Simulation Completed Successfully! (OK)")
    print("=" * 60)

if __name__ == "__main__":
    main()
