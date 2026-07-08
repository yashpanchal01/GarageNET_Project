from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import InventoryItem, JobCard, WorkshopProfile
from .utils import haversine_km


def make_workshop(username, lat, lon, shop_name=None):
    user = User.objects.create_user(username, password='pass12345')
    profile = WorkshopProfile.objects.create(
        user=user,
        shop_name=shop_name or username,
        phone_number='9999999999',
        latitude=lat,
        longitude=lon,
        address='Test address',
    )
    return user, profile


class HaversineTests(TestCase):
    def test_pune_to_mumbai_is_about_120_km(self):
        d = haversine_km(18.5204, 73.8567, 19.0760, 72.8777)
        self.assertTrue(100 < d < 160, d)

    def test_zero_distance_for_same_point(self):
        self.assertEqual(haversine_km(10.0, 20.0, 10.0, 20.0), 0.0)


class AuthFlowTests(TestCase):
    def test_registration_creates_user_and_profile_and_logs_in(self):
        resp = self.client.post(reverse('register'), {
            'username': 'newshop',
            'password1': 'str0ng-pass-123',
            'password2': 'str0ng-pass-123',
            'shop_name': 'New Shop',
            'phone_number': '1234567890',
            'latitude': '18.5',
            'longitude': '73.8',
            'address': 'Somewhere',
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        user = User.objects.get(username='newshop')
        self.assertEqual(user.workshop.shop_name, 'New Shop')
        self.assertTrue(resp.context['user'].is_authenticated)

    def test_registration_rejects_bad_latitude(self):
        self.client.post(reverse('register'), {
            'username': 'badshop',
            'password1': 'str0ng-pass-123',
            'password2': 'str0ng-pass-123',
            'shop_name': 'Bad Shop',
            'phone_number': '1234567890',
            'latitude': '95',
            'longitude': '73.8',
            'address': '',
        })
        self.assertFalse(User.objects.filter(username='badshop').exists())

    def test_user_without_profile_is_sent_to_profile_setup(self):
        User.objects.create_user('noshop', password='pass12345')
        self.client.login(username='noshop', password='pass12345')
        resp = self.client.get(reverse('dashboard'))
        self.assertRedirects(resp, reverse('profile'))

    def test_anonymous_is_redirected_to_login(self):
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('login'), resp.url)

    def test_authenticated_user_visiting_login_is_redirected_to_dashboard(self):
        User.objects.create_user('already_in', password='pass12345')
        self.client.login(username='already_in', password='pass12345')
        resp = self.client.get(reverse('login'))
        self.assertRedirects(resp, reverse('dashboard'), target_status_code=302)

    def test_registration_rejects_duplicate_username(self):
        User.objects.create_user('dupshop', password='pass12345')
        resp = self.client.post(reverse('register'), {
            'username': 'dupshop',
            'password1': 'str0ng-pass-123',
            'password2': 'str0ng-pass-123',
            'shop_name': 'Dup Shop',
            'phone_number': '1234567890',
            'latitude': '18.5',
            'longitude': '73.8',
            'address': 'Somewhere',
        })
        # Re-renders the form (no redirect); the original user is untouched and
        # no profile is created for the rejected signup.
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(User.objects.filter(username='dupshop').count(), 1)
        self.assertFalse(WorkshopProfile.objects.filter(shop_name='Dup Shop').exists())
        self.assertTrue(resp.context['user_form'].errors)

    def test_registration_rejects_password_mismatch(self):
        resp = self.client.post(reverse('register'), {
            'username': 'mismatch',
            'password1': 'str0ng-pass-123',
            'password2': 'different-pass-456',
            'shop_name': 'Mismatch Shop',
            'phone_number': '1234567890',
            'latitude': '18.5',
            'longitude': '73.8',
            'address': 'Somewhere',
        })
        # No user or profile is created when the two passwords disagree.
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username='mismatch').exists())
        self.assertFalse(WorkshopProfile.objects.filter(shop_name='Mismatch Shop').exists())
        self.assertTrue(resp.context['user_form'].errors)


class DashboardTests(TestCase):
    def setUp(self):
        self.user, self.workshop = make_workshop('shop_a', 18.52, 73.85)
        self.client.login(username='shop_a', password='pass12345')

    def test_counts_active_jobs_and_low_stock(self):
        JobCard.objects.create(workshop=self.workshop, vehicle_number='MH12A1',
                               customer_complaint='x', status=JobCard.Status.IN_PROGRESS)
        JobCard.objects.create(workshop=self.workshop, vehicle_number='MH12A2',
                               customer_complaint='x', status=JobCard.Status.READY)
        InventoryItem.objects.create(workshop=self.workshop, part_name='Oil Filter',
                                     quantity=1, b2b_price=100)
        InventoryItem.objects.create(workshop=self.workshop, part_name='Brake Pad',
                                     quantity=9, b2b_price=100)
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.context['active_job_cards'], 1)
        self.assertEqual(resp.context['low_stock_items'], 1)
        self.assertContains(resp, 'Oil Filter')

    def test_job_distribution_reflects_real_status_counts(self):
        # 2 in-progress, 1 ready, 1 received (=> "Others") : total 4
        JobCard.objects.create(workshop=self.workshop, vehicle_number='A1',
                               customer_complaint='x', status=JobCard.Status.IN_PROGRESS)
        JobCard.objects.create(workshop=self.workshop, vehicle_number='A2',
                               customer_complaint='x', status=JobCard.Status.IN_PROGRESS)
        JobCard.objects.create(workshop=self.workshop, vehicle_number='A3',
                               customer_complaint='x', status=JobCard.Status.READY)
        JobCard.objects.create(workshop=self.workshop, vehicle_number='A4',
                               customer_complaint='x', status=JobCard.Status.RECEIVED)

        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.context['total_jobs'], 4)
        dist = {s['label']: s for s in resp.context['job_distribution']}
        self.assertEqual(dist['In-progress']['count'], 2)
        self.assertEqual(dist['Ready']['count'], 1)
        self.assertEqual(dist['Others']['count'], 1)
        # Shares are proportional, not the old hardcoded 60/25.
        self.assertEqual(dist['In-progress']['percent'], 50.0)
        self.assertEqual(dist['Ready']['percent'], 25.0)

    def test_job_distribution_empty_when_no_jobs(self):
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.context['total_jobs'], 0)
        for seg in resp.context['job_distribution']:
            self.assertEqual(seg['count'], 0)
            self.assertEqual(seg['percent'], 0)

    def test_restock_message_when_inventory_is_empty(self):
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.context['inventory_count'], 0)
        self.assertContains(resp, 'No items in the inventory yet.')
        self.assertNotContains(resp, 'All parts sufficiently stocked.')

    def test_restock_message_when_all_stocked(self):
        InventoryItem.objects.create(workshop=self.workshop, part_name='Well Stocked',
                                     quantity=50, b2b_price=100)
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.context['inventory_count'], 1)
        self.assertContains(resp, 'All parts sufficiently stocked.')
        self.assertNotContains(resp, 'No items in the inventory yet.')


class InventoryTests(TestCase):
    def setUp(self):
        self.user, self.workshop = make_workshop('shop_a', 18.52, 73.85)
        self.client.login(username='shop_a', password='pass12345')

    def test_add_item(self):
        self.client.post(reverse('inventory'), {
            'part_name': 'Spark Plug', 'sku': 'SP1',
            'quantity': '4', 'b2b_price': '99.50',
        })
        item = InventoryItem.objects.get(part_name='Spark Plug')
        self.assertEqual(item.workshop, self.workshop)

    def test_edit_item(self):
        item = InventoryItem.objects.create(workshop=self.workshop, part_name='Clutch',
                                            quantity=2, b2b_price=500)
        self.client.post(reverse('inventory'), {
            'edit': item.pk, 'part_name': 'Clutch Plate', 'sku': '',
            'quantity': '7', 'b2b_price': '450',
        })
        item.refresh_from_db()
        self.assertEqual((item.part_name, item.quantity), ('Clutch Plate', 7))

    def test_delete_item(self):
        item = InventoryItem.objects.create(workshop=self.workshop, part_name='Bulb',
                                            quantity=3, b2b_price=40)
        self.client.post(reverse('inventory'), {'action': 'delete', 'item_id': item.pk})
        self.assertFalse(InventoryItem.objects.filter(pk=item.pk).exists())

    def test_cannot_touch_another_workshops_item(self):
        _, other = make_workshop('shop_b', 19.0, 72.8)
        item = InventoryItem.objects.create(workshop=other, part_name='Theirs',
                                            quantity=3, b2b_price=40)
        resp = self.client.post(reverse('inventory'),
                                {'action': 'delete', 'item_id': item.pk})
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(InventoryItem.objects.filter(pk=item.pk).exists())


class JobCardTests(TestCase):
    def setUp(self):
        self.user, self.workshop = make_workshop('shop_a', 18.52, 73.85)
        self.client.login(username='shop_a', password='pass12345')

    def test_create_and_update_status(self):
        self.client.post(reverse('job_cards'), {
            'action': 'create', 'vehicle_number': 'MH12AB1234',
            'customer_complaint': 'Brake noise', 'status': 'RECEIVED',
            'total_bill': '0',
        })
        job = JobCard.objects.get(vehicle_number='MH12AB1234')
        self.client.post(reverse('job_cards'), {
            'action': 'update_status', 'job_id': job.pk, 'status': 'READY',
        })
        job.refresh_from_db()
        self.assertEqual(job.status, JobCard.Status.READY)

    def test_cannot_transition_status_of_another_workshops_job_card(self):
        # Create another workshop and a job card belonging to it
        _, other_workshop = make_workshop('shop_b', 19.0, 72.8)
        other_job = JobCard.objects.create(
            workshop=other_workshop,
            vehicle_number='MH14ZZ9999',
            customer_complaint='Engine check light',
            status=JobCard.Status.RECEIVED
        )
        
        # Logged in as shop_a, try to transition shop_b's job card status
        response = self.client.post(reverse('job_cards'), {
            'action': 'update_status', 'job_id': other_job.pk, 'status': 'READY'
        })
        
        # Verify it returns 404
        self.assertEqual(response.status_code, 404)
        
        # Verify the status did not change
        other_job.refresh_from_db()
        self.assertEqual(other_job.status, JobCard.Status.RECEIVED)

    def test_create_job_card_with_invalid_data_fails(self):
        # Post to create with empty vehicle number
        response = self.client.post(reverse('job_cards'), {
            'action': 'create',
            'vehicle_number': '',
            'customer_complaint': 'Squeaking noise'
        })
        
        # Verify it doesn't redirect (since it re-renders the form with errors)
        self.assertEqual(response.status_code, 200)
        
        # Verify no JobCard is created in the database
        self.assertEqual(JobCard.objects.count(), 0)
        
        # Verify form errors exist in context
        self.assertTrue('form' in response.context)
        self.assertTrue(response.context['form'].errors)

    def test_job_cards_view_redirects_if_profile_missing(self):
        # Create a user without workshop profile
        User.objects.create_user('noshop_temp', password='pass12345')
        self.client.login(username='noshop_temp', password='pass12345')
        
        # Access job cards page
        response = self.client.get(reverse('job_cards'))
        
        # Should redirect to dashboard, which redirects to profile
        self.assertRedirects(response, reverse('dashboard'), target_status_code=302)

    def test_job_cards_page_lists_only_own_jobs(self):
        # Create a job card for self (shop_a)
        JobCard.objects.create(
            workshop=self.workshop,
            vehicle_number='MH12AA1111',
            customer_complaint='Engine tune-up',
            status=JobCard.Status.RECEIVED
        )
        
        # Create another workshop and a job card belonging to it
        _, other_workshop = make_workshop('shop_b', 19.0, 72.8)
        JobCard.objects.create(
            workshop=other_workshop,
            vehicle_number='MH14BB2222',
            customer_complaint='Air conditioning repair',
            status=JobCard.Status.RECEIVED
        )
        
        # Get the job cards page
        response = self.client.get(reverse('job_cards'))
        self.assertEqual(response.status_code, 200)
        
        # Verify that own job is in jobs context, but other shop's job is not
        jobs_in_context = response.context['jobs']
        self.assertTrue(any(j.vehicle_number == 'MH12AA1111' for j in jobs_in_context))
        self.assertFalse(any(j.vehicle_number == 'MH14BB2222' for j in jobs_in_context))


class PartSearchTests(TestCase):
    def setUp(self):
        self.user, self.pune = make_workshop('pune', 18.5204, 73.8567, 'Pune Auto')
        _, self.mumbai = make_workshop('mumbai', 19.0760, 72.8777, 'Mumbai Motors')
        _, self.nashik = make_workshop('nashik', 19.9975, 73.7898, 'Nashik Garage')
        self.client.login(username='pune', password='pass12345')

    def test_results_sorted_nearest_first(self):
        InventoryItem.objects.create(workshop=self.nashik, part_name='Brake Pad',
                                     quantity=2, b2b_price=1100)
        InventoryItem.objects.create(workshop=self.mumbai, part_name='Brake Pad',
                                     quantity=5, b2b_price=1200)
        resp = self.client.get(reverse('part_search'), {'q': 'brake', 'radius': '200'})
        results = resp.context['results']
        self.assertEqual(len(results), 2)
        # Mumbai (~120 km) is closer to Pune than Nashik (~165 km).
        self.assertEqual(results[0]['item'].workshop, self.mumbai)
        self.assertLess(results[0]['distance_km'], results[1]['distance_km'])

    def test_excludes_own_stock_and_zero_quantity(self):
        InventoryItem.objects.create(workshop=self.pune, part_name='Brake Pad',
                                     quantity=5, b2b_price=1000)
        InventoryItem.objects.create(workshop=self.mumbai, part_name='Brake Pad',
                                     quantity=0, b2b_price=1200)
        resp = self.client.get(reverse('part_search'), {'q': 'brake', 'radius': '200'})
        self.assertEqual(resp.context['results'], [])


class JobCardBillingAndStockTests(TestCase):
    def setUp(self):
        self.user, self.workshop = make_workshop('shop_a', 18.52, 73.85)
        self.client.login(username='shop_a', password='pass12345')
        self.inventory_item = InventoryItem.objects.create(
            workshop=self.workshop,
            part_name='Spark Plug',
            sku='SP1',
            quantity=10,
            b2b_price=99.50
        )
        self.job_card = JobCard.objects.create(
            workshop=self.workshop,
            vehicle_number='MH12A1',
            customer_complaint='Spark plug issue',
            status=JobCard.Status.RECEIVED
        )

    def test_add_part_deducts_stock_and_calculates_bill(self):
        # Add 3 spark plugs
        self.client.post(
            reverse('job_card_detail', args=[self.job_card.pk]),
            {'action': 'add_part', 'inventory_item': self.inventory_item.pk, 'quantity': '3'}
        )
        self.inventory_item.refresh_from_db()
        self.job_card.refresh_from_db()

        self.assertEqual(self.inventory_item.quantity, 7)
        self.assertEqual(float(self.job_card.total_bill), 298.50)  # 3 * 99.50

        # Verify line item was created with snapshot values
        line_item = self.job_card.line_items.first()
        self.assertEqual(line_item.part_name, 'Spark Plug')
        self.assertEqual(float(line_item.unit_price), 99.50)

    def test_out_of_stock_validation_blocks_and_rolls_back(self):
        # Try adding 11 spark plugs (only 10 in stock)
        self.client.post(
            reverse('job_card_detail', args=[self.job_card.pk]),
            {'action': 'add_part', 'inventory_item': self.inventory_item.pk, 'quantity': '11'}
        )
        self.inventory_item.refresh_from_db()
        self.job_card.refresh_from_db()

        self.assertEqual(self.inventory_item.quantity, 10)
        self.assertEqual(float(self.job_card.total_bill), 0.0)
        self.assertEqual(self.job_card.line_items.count(), 0)

    def test_remove_part_replenishes_stock_and_recalculates_bill(self):
        # First, add a part
        self.client.post(
            reverse('job_card_detail', args=[self.job_card.pk]),
            {'action': 'add_part', 'inventory_item': self.inventory_item.pk, 'quantity': '4'}
        )
        self.inventory_item.refresh_from_db()
        self.assertEqual(self.inventory_item.quantity, 6)

        line_item = self.job_card.line_items.first()

        # Remove the part
        self.client.post(
            reverse('job_card_detail', args=[self.job_card.pk]),
            {'action': 'remove_part', 'line_item_id': line_item.pk}
        )
        self.inventory_item.refresh_from_db()
        self.job_card.refresh_from_db()

        self.assertEqual(self.inventory_item.quantity, 10)
        self.assertEqual(float(self.job_card.total_bill), 0.0)
        self.assertEqual(self.job_card.line_items.count(), 0)

    def test_billing_snapshot_preserves_invoice_integrity(self):
        # Add 2 spark plugs at 99.50
        self.client.post(
            reverse('job_card_detail', args=[self.job_card.pk]),
            {'action': 'add_part', 'inventory_item': self.inventory_item.pk, 'quantity': '2'}
        )

        # Change the master catalog price in inventory
        self.inventory_item.b2b_price = 150.00
        self.inventory_item.save()

        self.job_card.refresh_from_db()
        self.assertEqual(float(self.job_card.total_bill), 199.00)  # Should still be 2 * 99.50

        # Delete catalog item entirely
        self.inventory_item.delete()

        self.job_card.refresh_from_db()
        # Bill total should still be 199.00 and line item should still exist
        self.assertEqual(float(self.job_card.total_bill), 199.00)
        line_item = self.job_card.line_items.first()
        self.assertIsNotNone(line_item)
        self.assertIsNone(line_item.inventory_item)
        self.assertEqual(line_item.part_name, 'Spark Plug')


class ProfileModelTests(TestCase):
    def test_model_validates_latitude_range(self):
        user = User.objects.create_user('test_validator_user', password='pass12345')
        profile = WorkshopProfile(
            user=user,
            shop_name='Test Shop',
            phone_number='1234',
            latitude=95.0,  # Invalid latitude
            longitude=73.0,
            address='Addr'
        )
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            profile.full_clean()

    def test_model_validates_longitude_range(self):
        user = User.objects.create_user('test_validator_user2', password='pass12345')
        profile = WorkshopProfile(
            user=user,
            shop_name='Test Shop',
            phone_number='1234',
            latitude=18.0,
            longitude=190.0,  # Invalid longitude
            address='Addr'
        )
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            profile.full_clean()


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user, self.profile = make_workshop('shop_a', 18.52, 73.85)
        self.client.login(username='shop_a', password='pass12345')

    def test_get_profile_page_returns_populated_form(self):
        resp = self.client.get(reverse('profile'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'shop_a')
        self.assertContains(resp, '18.52')
        self.assertContains(resp, '73.85')

    def test_post_profile_updates_data_and_redirects(self):
        resp = self.client.post(reverse('profile'), {
            'shop_name': 'Updated Shop Name',
            'phone_number': '9999999999',
            'latitude': '19.0760',
            'longitude': '72.8777',
            'address': 'Bandra, Mumbai',
        })
        self.assertRedirects(resp, reverse('dashboard'))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.shop_name, 'Updated Shop Name')
        self.assertEqual(self.profile.latitude, 19.0760)

    def test_get_profile_page_for_user_without_profile_renders_blank_form(self):
        # A freshly-registered user sent here to set up their workshop should
        # see an empty, unsaved form rather than someone else's data.
        User.objects.create_user('fresh', password='pass12345')
        self.client.login(username='fresh', password='pass12345')
        resp = self.client.get(reverse('profile'))
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.context['workshop'])
        form = resp.context['form']
        self.assertFalse(form.is_bound)
        self.assertIsNone(form.instance.pk)

    def test_post_profile_with_invalid_coords_fails(self):
        resp = self.client.post(reverse('profile'), {
            'shop_name': 'Updated Shop Name',
            'phone_number': '9999999999',
            'latitude': '120.0',  # invalid
            'longitude': '72.8777',
            'address': 'Bandra, Mumbai',
        })
        self.assertEqual(resp.status_code, 200)  # Form errors, re-renders page
        self.profile.refresh_from_db()
        self.assertNotEqual(self.profile.latitude, 120.0)  # Not updated


