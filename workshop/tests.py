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
        resp = self.client.get(reverse('part_search'), {'q': 'brake'})
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
        resp = self.client.get(reverse('part_search'), {'q': 'brake'})
        self.assertEqual(resp.context['results'], [])
