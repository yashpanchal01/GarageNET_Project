from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import InventoryItem
from .tests import make_workshop


class InventoryLedgerGapTests(TestCase):
    """Slice 2 gap-filling coverage for the inventory ledger view/form/model.

    Complements InventoryTests (add/edit/delete + cross-tenant delete) in
    workshop/tests.py without duplicating those cases.
    """

    def setUp(self):
        self.user, self.workshop = make_workshop('shop_a', 18.52, 73.85)
        self.client.login(username='shop_a', password='pass12345')

    def test_add_item_missing_price_is_rejected(self):
        """POST without b2b_price re-renders with form errors and creates nothing."""
        resp = self.client.post(reverse('inventory'), {
            'part_name': 'Air Filter', 'sku': 'AF1', 'quantity': '5',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn('b2b_price', resp.context['form'].errors)
        self.assertFalse(InventoryItem.objects.filter(part_name='Air Filter').exists())

    def test_add_item_non_numeric_quantity_is_rejected(self):
        """A non-numeric quantity re-renders with form errors and creates nothing."""
        resp = self.client.post(reverse('inventory'), {
            'part_name': 'Radiator', 'sku': 'RAD1',
            'quantity': 'abc', 'b2b_price': '250.00',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn('quantity', resp.context['form'].errors)
        self.assertFalse(InventoryItem.objects.filter(part_name='Radiator').exists())

    def test_add_item_with_blank_sku_saves(self):
        """SKU is optional: a new item persists with an empty sku."""
        self.client.post(reverse('inventory'), {
            'part_name': 'Wiper Blade', 'sku': '',
            'quantity': '6', 'b2b_price': '80.00',
        })
        item = InventoryItem.objects.get(part_name='Wiper Blade')
        self.assertEqual(item.sku, '')
        self.assertEqual(item.workshop, self.workshop)

    def test_cannot_edit_another_workshops_item(self):
        """Editing another workshop's item is blocked (404) and leaves it unchanged."""
        _, other = make_workshop('shop_b', 19.0, 72.8)
        item = InventoryItem.objects.create(
            workshop=other, part_name='Theirs', sku='T1', quantity=3, b2b_price=40,
        )
        resp = self.client.post(reverse('inventory'), {
            'edit': item.pk, 'part_name': 'Hijacked', 'sku': 'T1',
            'quantity': '99', 'b2b_price': '1',
        })
        self.assertEqual(resp.status_code, 404)
        item.refresh_from_db()
        self.assertEqual((item.part_name, item.quantity), ('Theirs', 3))

    def test_new_item_ignores_client_supplied_workshop(self):
        """The server assigns the item to the logged-in workshop, not a posted one."""
        _, other = make_workshop('shop_b', 19.0, 72.8)
        self.client.post(reverse('inventory'), {
            'part_name': 'Fan Belt', 'sku': 'FB1',
            'quantity': '3', 'b2b_price': '120.00',
            'workshop': other.pk,  # attacker-supplied; must be ignored
        })
        item = InventoryItem.objects.get(part_name='Fan Belt')
        self.assertEqual(item.workshop, self.workshop)

    def test_inventory_redirects_to_dashboard_without_profile(self):
        """A logged-in user with no WorkshopProfile is bounced off the ledger."""
        User.objects.create_user('noshop', password='pass12345')
        self.client.login(username='noshop', password='pass12345')
        resp = self.client.get(reverse('inventory'))
        # inventory -> dashboard, and dashboard (no profile) -> profile.
        self.assertRedirects(resp, reverse('dashboard'), target_status_code=302)

    def test_ledger_lists_only_own_items(self):
        """GET context exposes only the current workshop's items (tenant isolation)."""
        InventoryItem.objects.create(
            workshop=self.workshop, part_name='Mine', quantity=1, b2b_price=10,
        )
        _, other = make_workshop('shop_b', 19.0, 72.8)
        InventoryItem.objects.create(
            workshop=other, part_name='NotMine', quantity=1, b2b_price=10,
        )
        resp = self.client.get(reverse('inventory'))
        self.assertEqual(resp.status_code, 200)
        names = [i.part_name for i in resp.context['items']]
        self.assertIn('Mine', names)
        self.assertNotIn('NotMine', names)

    def test_items_listed_ordered_by_part_name(self):
        """The ledger returns items alphabetically by part_name."""
        for name in ('Zebra Belt', 'Alpha Coil', 'Mango Hose'):
            InventoryItem.objects.create(
                workshop=self.workshop, part_name=name, quantity=1, b2b_price=10,
            )
        resp = self.client.get(reverse('inventory'))
        names = [i.part_name for i in resp.context['items']]
        self.assertEqual(names, ['Alpha Coil', 'Mango Hose', 'Zebra Belt'])
