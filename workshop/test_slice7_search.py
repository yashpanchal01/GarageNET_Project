"""Slice 7 - Hyperlocal Search & Radar Map (PRD Stories 14-17).

Audit / fill-gaps TDD pass. Tests ONLY at two seams:
  * the ``part_search`` view (context['results'] contract), and
  * the ``haversine_km`` util.

Expectations for the haversine util are INDEPENDENT known-good geographic
reference values (1 degree of latitude ~ 111 km; symmetry as a property),
never the formula restated. Does NOT duplicate coverage already in
workshop.tests (HaversineTests / PartSearchTests).
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import InventoryItem
from .tests import make_workshop
from .utils import haversine_km


class HaversineSlice7Tests(TestCase):
    """Extra haversine coverage using independent reference values only."""

    def test_one_degree_of_latitude_is_about_111_km(self):
        # A well-known geographic fact: one degree of latitude along a
        # meridian is ~111 km, independent of the haversine formula itself.
        d = haversine_km(0.0, 0.0, 1.0, 0.0)
        self.assertTrue(110.0 < d < 112.5, d)

    def test_distance_is_symmetric(self):
        # Property, not the formula: A->B must equal B->A.
        pune_to_mumbai = haversine_km(18.5204, 73.8567, 19.0760, 72.8777)
        mumbai_to_pune = haversine_km(19.0760, 72.8777, 18.5204, 73.8567)
        self.assertAlmostEqual(pune_to_mumbai, mumbai_to_pune, places=9)


class PartSearchSlice7Tests(TestCase):
    def setUp(self):
        self.user, self.pune = make_workshop('pune', 18.5204, 73.8567, 'Pune Auto')
        _, self.mumbai = make_workshop('mumbai', 19.0760, 72.8777, 'Mumbai Motors')
        _, self.nashik = make_workshop('nashik', 19.9975, 73.7898, 'Nashik Garage')
        self.client.login(username='pune', password='pass12345')

    # --- Story 14: radius filtering -------------------------------------

    def test_shop_outside_radius_is_excluded_until_radius_widened(self):
        # Mumbai (~120 km) sits outside a 50 km radius but inside 200 km.
        InventoryItem.objects.create(workshop=self.mumbai, part_name='Brake Pad',
                                     quantity=5, b2b_price=1200)
        near = self.client.get(reverse('part_search'), {'q': 'brake', 'radius': '50'})
        self.assertEqual(near.context['results'], [])

        wide = self.client.get(reverse('part_search'), {'q': 'brake', 'radius': '200'})
        self.assertEqual(len(wide.context['results']), 1)
        self.assertEqual(wide.context['results'][0]['item'].workshop, self.mumbai)

    def test_empty_query_returns_empty_results_without_crashing(self):
        InventoryItem.objects.create(workshop=self.mumbai, part_name='Brake Pad',
                                     quantity=5, b2b_price=1200)
        resp = self.client.get(reverse('part_search'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['results'], [])

    # --- Story 16: contact details inline -------------------------------

    def test_results_expose_shop_contact_details(self):
        self.mumbai.phone_number = '9820011111'
        self.mumbai.address = 'Bandra West, Mumbai'
        self.mumbai.save()
        InventoryItem.objects.create(workshop=self.mumbai, part_name='Brake Pad',
                                     quantity=5, b2b_price=1200)

        resp = self.client.get(reverse('part_search'), {'q': 'brake', 'radius': '200'})
        profile = resp.context['results'][0]['profile']
        self.assertEqual(profile.shop_name, 'Mumbai Motors')
        self.assertEqual(profile.phone_number, '9820011111')
        self.assertEqual(profile.address, 'Bandra West, Mumbai')
        # And the same details are rendered inline on the page.
        self.assertContains(resp, 'Mumbai Motors')
        self.assertContains(resp, '9820011111')
        self.assertContains(resp, 'Bandra West, Mumbai')

    # --- Story 14: matching semantics -----------------------------------

    def test_search_is_case_insensitive_and_partial(self):
        InventoryItem.objects.create(workshop=self.mumbai, part_name='Brake Pad',
                                     quantity=5, b2b_price=1200)
        lower = self.client.get(reverse('part_search'), {'q': 'brake', 'radius': '200'})
        upper = self.client.get(reverse('part_search'), {'q': 'BRAKE', 'radius': '200'})
        self.assertEqual(len(lower.context['results']), 1)
        self.assertEqual(len(upper.context['results']), 1)

    def test_non_matching_part_is_excluded(self):
        InventoryItem.objects.create(workshop=self.mumbai, part_name='Oil Filter',
                                     quantity=5, b2b_price=300)
        resp = self.client.get(reverse('part_search'), {'q': 'brake', 'radius': '200'})
        self.assertEqual(resp.context['results'], [])

    # --- radius fallback behavior ---------------------------------------

    def test_default_radius_is_50_when_param_omitted(self):
        resp = self.client.get(reverse('part_search'), {'q': 'brake'})
        self.assertEqual(resp.context['radius'], 50.0)

    def test_default_radius_is_50_when_param_non_numeric(self):
        resp = self.client.get(reverse('part_search'), {'q': 'brake', 'radius': 'abc'})
        self.assertEqual(resp.context['radius'], 50.0)

    # --- profile guard --------------------------------------------------

    def test_redirects_to_dashboard_when_user_has_no_profile(self):
        User.objects.create_user('noprofile', password='pass12345')
        self.client.login(username='noprofile', password='pass12345')
        resp = self.client.get(reverse('part_search'))
        self.assertRedirects(resp, reverse('dashboard'), target_status_code=302)
