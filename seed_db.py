import os
import django

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'garagenet.settings')
django.setup()

from django.contrib.auth.models import User
from workshop.models import WorkshopProfile, InventoryItem, JobCard

def seed():
    print("Clearing database...")
    User.objects.all().delete()
    WorkshopProfile.objects.all().delete()
    InventoryItem.objects.all().delete()
    JobCard.objects.all().delete()

    print("Creating workshops...")
    # Pune Garage
    pune_user = User.objects.create_user(username='pune_garage', password='password123')
    pune_profile = WorkshopProfile.objects.create(
        user=pune_user,
        shop_name='Pune Premium Garage',
        phone_number='+91 98765 43210',
        latitude=18.5204,
        longitude=73.8567,
        address='Senapati Bapat Road, Shivajinagar, Pune, Maharashtra 411016'
    )

    # Mumbai Motors
    mumbai_user = User.objects.create_user(username='mumbai_motors', password='password123')
    mumbai_profile = WorkshopProfile.objects.create(
        user=mumbai_user,
        shop_name='Mumbai Elite Motors',
        phone_number='+91 98765 43211',
        latitude=19.0760,
        longitude=72.8777,
        address='Bandra West, Mumbai, Maharashtra 400050'
    )

    # Nashik Spares
    nashik_user = User.objects.create_user(username='nashik_spares', password='password123')
    nashik_profile = WorkshopProfile.objects.create(
        user=nashik_user,
        shop_name='Nashik Express Garage',
        phone_number='+91 98765 43212',
        latitude=19.9975,
        longitude=73.7898,
        address='College Road, Nashik, Maharashtra 422005'
    )

    # Demo User
    demo_user = User.objects.create_user(username='demo_user', password='password123')
    demo_profile = WorkshopProfile.objects.create(
        user=demo_user,
        shop_name='GarageNET Demo Shop',
        phone_number='+91 90000 00000',
        latitude=18.5300, # Near Pune
        longitude=73.8400,
        address='Aundh, Pune, Maharashtra 411007'
    )

    print("Creating inventory items...")
    # Helper to add items
    parts_template = [
        {"part_name": "Engine Oil 5W-30", "sku": "EO-5W30-1L", "quantity": 15, "b2b_price": 450.00},
        {"part_name": "Oil Filter", "sku": "OF-GEN-01", "quantity": 8, "b2b_price": 180.00},
        {"part_name": "Brake Pads Front", "sku": "BP-FR-02", "quantity": 4, "b2b_price": 1200.00},
        {"part_name": "Air Filter", "sku": "AF-GEN-03", "quantity": 10, "b2b_price": 250.00},
        {"part_name": "Spark Plug Platinum", "sku": "SP-PL-04", "quantity": 2, "b2b_price": 350.00}, # Low stock
        {"part_name": "Clutch Plate Assembly", "sku": "CP-ASSY-05", "quantity": 1, "b2b_price": 3800.00}, # Low stock
        {"part_name": "Car Battery 12V", "sku": "BATT-12V-35AH", "quantity": 0, "b2b_price": 4200.00}, # Out of stock
        {"part_name": "Wiper Blades Set", "sku": "WB-SET-1820", "quantity": 12, "b2b_price": 300.00},
    ]

    for profile in [pune_profile, mumbai_profile, nashik_profile, demo_profile]:
        # Slightly vary price and quantity for each workshop
        for i, part in enumerate(parts_template):
            price_variance = float(part["b2b_price"]) * (1.0 + (i % 3 - 1) * 0.05)
            qty_variance = max(0, part["quantity"] + (i % 2 - 1) * 2)
            InventoryItem.objects.create(
                workshop=profile,
                part_name=part["part_name"],
                sku=f"{part['sku']}-{profile.id}",
                quantity=qty_variance,
                b2b_price=round(price_variance, 2)
            )

    print("Creating job cards for demo shop...")
    JobCard.objects.create(
        workshop=demo_profile,
        vehicle_number="MH-12-PQ-5678",
        customer_complaint="Periodic maintenance service, oil change, brake inspection, engine noise checking.",
        status=JobCard.Status.IN_PROGRESS,
        total_bill=0
    )
    JobCard.objects.create(
        workshop=demo_profile,
        vehicle_number="MH-12-XY-1234",
        customer_complaint="AC not cooling, front wiper blades replacement, door lock noise.",
        status=JobCard.Status.RECEIVED,
        total_bill=0
    )
    JobCard.objects.create(
        workshop=demo_profile,
        vehicle_number="MH-02-AB-9999",
        customer_complaint="Suspension sound on rough roads, replacement of shock absorber bushings.",
        status=JobCard.Status.WAITING_FOR_PARTS,
        total_bill=5400.00
    )
    JobCard.objects.create(
        workshop=demo_profile,
        vehicle_number="MH-14-CC-4321",
        customer_complaint="Brake pad replacement and brake bleeding.",
        status=JobCard.Status.READY,
        total_bill=1750.00
    )

    print("Seeding completed successfully!")
    print("\n--- Demo Login Details ---")
    print("Username: demo_user")
    print("Password: password123")
    print("--------------------------")

if __name__ == "__main__":
    seed()
