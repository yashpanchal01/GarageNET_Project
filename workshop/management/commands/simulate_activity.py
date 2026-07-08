import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import User
from workshop.models import WorkshopProfile, InventoryItem, JobCard, JobCardLineItem, AdditionalCharge, JobCardActivity

# Mock Data Templates
VEHICLE_NUMBERS = [
    "MH-12-PQ-5678", "MH-12-XY-1234", "MH-02-AB-9999", "MH-14-CC-4321",
    "KA-03-MM-7890", "KA-51-AB-4567", "DL-03-CD-8888", "DL-10-XY-2345",
    "HR-26-BC-1122", "GJ-01-AA-9990", "TS-09-EF-4433", "UP-16-TR-6789"
]

COMPLAINTS_TEMPLATES = [
    "Periodic maintenance service, oil change, cabin air filter replacement, check fluid levels.",
    "AC not cooling, front wiper blades replacement, door lock noise on front passenger side.",
    "Suspension sound on rough roads, replacement of shock absorber bushings, front link rods check.",
    "Brake pad replacement and brake bleeding. Squeaking sound on sudden braking.",
    "Clutch pedal feels hard, vehicle slips in 2nd and 3rd gears, suspect clutch plate wear.",
    "Engine temperature gauge rising high after 15 mins of driving, suspect coolant leak or fan issue.",
    "Engine misfiring under acceleration, spark plugs replacement and ignition coil inspection.",
    "Car battery dying, dashboard showing battery warning lamp. Needs replacement or charging.",
    "Starter motor making grinding noise but engine does not crank. Starter overhaul needed.",
    "Power steering fluid leakage, heavy steering wheel response, steering rack boot replacement."
]

PARTS_TEMPLATES = [
    {"part_name": "Engine Oil 5W-30", "sku": "EO-5W30-1L", "quantity_range": (15, 30), "price_range": (400, 550)},
    {"part_name": "Oil Filter", "sku": "OF-GEN-01", "quantity_range": (10, 20), "price_range": (150, 220)},
    {"part_name": "Brake Pads Front", "sku": "BP-FR-02", "quantity_range": (5, 12), "price_range": (900, 1500)},
    {"part_name": "Air Filter", "sku": "AF-GEN-03", "quantity_range": (10, 25), "price_range": (200, 320)},
    {"part_name": "Spark Plug Platinum", "sku": "SP-PL-04", "quantity_range": (4, 15), "price_range": (300, 450)},
    {"part_name": "Clutch Plate Assembly", "sku": "CP-ASSY-05", "quantity_range": (2, 5), "price_range": (3200, 4500)},
    {"part_name": "Car Battery 12V", "sku": "BATT-12V-35AH", "quantity_range": (1, 6), "price_range": (3800, 4600)},
    {"part_name": "Wiper Blades Set", "sku": "WB-SET-1820", "quantity_range": (8, 20), "price_range": (250, 400)},
    {"part_name": "Coolant Red 1L", "sku": "CLNT-RD-1L", "quantity_range": (10, 30), "price_range": (250, 350)},
    {"part_name": "Brake Fluid DOT4", "sku": "BF-DT4-500", "quantity_range": (5, 15), "price_range": (180, 280)}
]

CHARGES_TEMPLATES = [
    ("General Service Labor", 600, 1200),
    ("Brake System Overhaul & Bleeding Labor", 400, 800),
    ("Clutch Replacement Labor Charge", 1500, 2500),
    ("Engine Diagnostic & Scanning Fee", 500, 900),
    ("AC Servicing & Gas Charging Charge", 1200, 1800),
    ("Suspension Bushings Replacement Labor", 800, 1500),
    ("Electrical Diagnosis & Wiring Repair", 350, 700),
    ("Vehicle Exterior Wash & Interior Vacuuming", 300, 500)
]

class Command(BaseCommand):
    help = "Simulates historical and active workshop activity in the database."

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of historical days to simulate activity over (default: 7)'
        )
        parser.add_argument(
            '--jobs-per-day',
            type=int,
            default=2,
            help='Average number of job cards to create per workshop per day (default: 2)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing database transactions (JobCards, InventoryItems, etc.) before running simulation'
        )

    def handle(self, *args, **options):
        days = options['days']
        jobs_per_day = options['jobs_per_day']
        clear = options['clear']

        self.stdout.write(self.style.WARNING("Starting GarageNET activity simulation..."))

        if clear:
            self.stdout.write(self.style.NOTICE("Clearing transactional database tables..."))
            JobCardActivity.objects.all().delete()
            JobCardLineItem.objects.all().delete()
            AdditionalCharge.objects.all().delete()
            JobCard.objects.all().delete()
            # Do NOT delete Users/WorkshopProfiles, but we can delete/reset inventory items
            InventoryItem.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Database transactions cleared."))

        # Check workshops
        workshops = WorkshopProfile.objects.all()
        if not workshops.exists():
            self.stdout.write(self.style.NOTICE("No workshops found. Seeding default demo workshops..."))
            # Create a demo user & profile if they don't exist
            demo_user, _ = User.objects.get_or_create(username='demo_user')
            demo_user.set_password('password123')
            demo_user.save()

            demo_profile, _ = WorkshopProfile.objects.get_or_create(
                user=demo_user,
                defaults={
                    'shop_name': 'GarageNET Demo Shop',
                    'phone_number': '+91 90000 00000',
                    'latitude': 18.5300,
                    'longitude': 73.8400,
                    'address': 'Aundh, Pune, Maharashtra 411007'
                }
            )

            pune_user, _ = User.objects.get_or_create(username='pune_garage')
            pune_user.set_password('password123')
            pune_user.save()

            pune_profile, _ = WorkshopProfile.objects.get_or_create(
                user=pune_user,
                defaults={
                    'shop_name': 'Pune Premium Garage',
                    'phone_number': '+91 98765 43210',
                    'latitude': 18.5204,
                    'longitude': 73.8567,
                    'address': 'Senapati Bapat Road, Shivajinagar, Pune, Maharashtra 411016'
                }
            )

            mumbai_user, _ = User.objects.get_or_create(username='mumbai_motors')
            mumbai_user.set_password('password123')
            mumbai_user.save()

            mumbai_profile, _ = WorkshopProfile.objects.get_or_create(
                user=mumbai_user,
                defaults={
                    'shop_name': 'Mumbai Elite Motors',
                    'phone_number': '+91 98765 43211',
                    'latitude': 19.0760,
                    'longitude': 72.8777,
                    'address': 'Bandra West, Mumbai, Maharashtra 400050'
                }
            )
            workshops = WorkshopProfile.objects.all()

        # Ensure all workshops have standard inventory items
        for ws in workshops:
            inv_count = InventoryItem.objects.filter(workshop=ws).count()
            if inv_count == 0:
                self.stdout.write(self.style.NOTICE(f"Seeding inventory for '{ws.shop_name}'..."))
                for part in PARTS_TEMPLATES:
                    quantity = random.randint(*part["quantity_range"])
                    price = round(random.uniform(*part["price_range"]), 2)
                    InventoryItem.objects.create(
                        workshop=ws,
                        part_name=part["part_name"],
                        sku=f"{part['sku']}-{ws.id}",
                        quantity=quantity,
                        b2b_price=price
                    )

        # Simulation timeline loop
        now = timezone.now()
        start_date = now - timedelta(days=days)
        total_jobs_created = 0
        total_activities_created = 0

        self.stdout.write(self.style.NOTICE(f"Simulating activity from {start_date.date()} to {now.date()}..."))

        for day_offset in range(days + 1):
            simulated_date = start_date + timedelta(days=day_offset)
            # Make sure we vary the hours randomly throughout the simulated day
            self.stdout.write(f"Generating events for {simulated_date.date()}...")

            for ws in workshops:
                # Number of jobs to create on this day for this workshop
                jobs_to_create = max(0, int(random.normalvariate(jobs_per_day, 1)))

                for _ in range(jobs_to_create):
                    vehicle_number = random.choice(VEHICLE_NUMBERS)
                    # Add a random unique component to license plate to avoid duplicate collisions
                    vehicle_number = f"{vehicle_number[:-4]}{random.randint(1000, 9999)}"
                    customer_complaint = random.choice(COMPLAINTS_TEMPLATES)

                    # Create a JobCard
                    with transaction.atomic():
                        job_card = JobCard.objects.create(
                            workshop=ws,
                            vehicle_number=vehicle_number,
                            customer_complaint=customer_complaint,
                            status=JobCard.Status.RECEIVED,
                            total_bill=0
                        )
                        # Override auto_now_add using .update
                        JobCard.objects.filter(pk=job_card.pk).update(created_at=simulated_date)
                        
                        # Refresh from db to get overridden date
                        job_card.refresh_from_db()

                        activity = JobCardActivity.log(
                            job_card,
                            JobCardActivity.EventType.CREATED,
                            f"Job card created for {job_card.vehicle_number} at reception."
                        )
                        JobCardActivity.objects.filter(pk=activity.pk).update(created_at=simulated_date)
                        total_jobs_created += 1
                        total_activities_created += 1

                        # Simulate workflow progression immediately or in steps
                        # We can decide what status the job card should end up at
                        final_status = random.choice([
                            JobCard.Status.RECEIVED,
                            JobCard.Status.IN_PROGRESS,
                            JobCard.Status.WAITING_FOR_PARTS,
                            JobCard.Status.READY
                        ])

                        current_date = simulated_date

                        # 1. Transition to IN_PROGRESS (if final status is beyond RECEIVED)
                        if final_status != JobCard.Status.RECEIVED:
                            current_date += timedelta(hours=random.randint(1, 4))
                            job_card.status = JobCard.Status.IN_PROGRESS
                            job_card.save(update_fields=['status'])
                            JobCard.objects.filter(pk=job_card.pk).update(created_at=current_date)
                            
                            act_status = JobCardActivity.log(
                                job_card,
                                JobCardActivity.EventType.STATUS_CHANGED,
                                "Status changed from Received to In-Progress."
                            )
                            JobCardActivity.objects.filter(pk=act_status.pk).update(created_at=current_date)
                            total_activities_created += 1

                            # 2. Add parts to the job card
                            num_parts = random.randint(1, 3)
                            available_parts = list(InventoryItem.objects.filter(workshop=ws, quantity__gt=0))
                            
                            if available_parts:
                                parts_to_add = random.sample(available_parts, min(num_parts, len(available_parts)))
                                for part in parts_to_add:
                                    qty = random.randint(1, 2)
                                    if part.quantity >= qty:
                                        part.quantity -= qty
                                        part.save(update_fields=['quantity'])
                                        
                                        line_item = JobCardLineItem.objects.create(
                                            job_card=job_card,
                                            inventory_item=part,
                                            part_name=part.part_name,
                                            sku=part.sku,
                                            quantity=qty,
                                            unit_price=part.b2b_price
                                        )
                                        JobCardLineItem.objects.filter(pk=line_item.pk).update(created_at=current_date)
                                        
                                        act_part = JobCardActivity.log(
                                            job_card,
                                            JobCardActivity.EventType.PART_ADDED,
                                            f"Added part \"{part.part_name}\" (x{qty} @ ₹{part.b2b_price})."
                                        )
                                        JobCardActivity.objects.filter(pk=act_part.pk).update(created_at=current_date)
                                        total_activities_created += 1

                            # 3. Add Labor/Diagnostic charges
                            num_charges = random.randint(1, 2)
                            charges_to_add = random.sample(CHARGES_TEMPLATES, num_charges)
                            for desc, min_p, max_p in charges_to_add:
                                amt = round(random.uniform(min_p, max_p), 2)
                                charge = AdditionalCharge.objects.create(
                                    job_card=job_card,
                                    description=desc,
                                    amount=amt
                                )
                                AdditionalCharge.objects.filter(pk=charge.pk).update(created_at=current_date)
                                
                                act_charge = JobCardActivity.log(
                                    job_card,
                                    JobCardActivity.EventType.CHARGE_ADDED,
                                    f"Added charge \"{desc}\" (₹{amt})."
                                )
                                JobCardActivity.objects.filter(pk=act_charge.pk).update(created_at=current_date)
                                total_activities_created += 1

                            # Recalculate bill total after parts and charges added
                            job_card.recalculate_total()

                        # 3. Handle transition to WAITING_FOR_PARTS or READY
                        if final_status == JobCard.Status.WAITING_FOR_PARTS:
                            current_date += timedelta(hours=random.randint(1, 3))
                            job_card.status = JobCard.Status.WAITING_FOR_PARTS
                            job_card.save(update_fields=['status'])
                            
                            act_status = JobCardActivity.log(
                                job_card,
                                JobCardActivity.EventType.STATUS_CHANGED,
                                "Status changed from In-Progress to Waiting-for-Parts."
                            )
                            JobCardActivity.objects.filter(pk=act_status.pk).update(created_at=current_date)
                            total_activities_created += 1

                        elif final_status == JobCard.Status.READY:
                            current_date += timedelta(hours=random.randint(2, 6))
                            job_card.status = JobCard.Status.READY
                            job_card.save(update_fields=['status'])
                            
                            act_status = JobCardActivity.log(
                                job_card,
                                JobCardActivity.EventType.STATUS_CHANGED,
                                "Status changed from In-Progress to Ready."
                            )
                            JobCardActivity.objects.filter(pk=act_status.pk).update(created_at=current_date)
                            total_activities_created += 1

                            # Generate invoice activity
                            act_invoice = JobCardActivity.log(
                                job_card,
                                JobCardActivity.EventType.INVOICE_GENERATED,
                                f"Bill generated. Total: ₹{job_card.total_bill}."
                            )
                            JobCardActivity.objects.filter(pk=act_invoice.pk).update(created_at=current_date)
                            total_activities_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully simulated workshop operations!\n"
            f"Generated:\n"
            f"  - {total_jobs_created} Job Cards\n"
            f"  - {total_activities_created} Job Card Activities\n"
            f"across {workshops.count()} workshops over {days} days."
        ))
