from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import InventoryItem, JobCard, JobCardLineItem
from .tests import make_workshop


class JobCardDetailAndSnapshotTests(TestCase):
    """Gap-filling coverage for slices 4-6: detail page, junction billing,
    transactional stock deduction, and invoice snapshot integrity.

    Mirrors the seams already exercised by ``JobCardBillingAndStockTests`` in
    ``workshop/tests.py`` but targets the untested boundary, accumulation,
    dropdown-filtering and finer-grained snapshot behaviours.
    """

    def setUp(self):
        self.user, self.workshop = make_workshop('shop_a', 18.52, 73.85)
        self.client.login(username='shop_a', password='pass12345')
        self.inventory_item = InventoryItem.objects.create(
            workshop=self.workshop,
            part_name='Spark Plug',
            sku='SP1',
            quantity=10,
            b2b_price=99.50,
        )
        self.job_card = JobCard.objects.create(
            workshop=self.workshop,
            vehicle_number='MH12A1',
            customer_complaint='Spark plug issue',
            status=JobCard.Status.RECEIVED,
        )

    def _add_part(self, item, quantity):
        return self.client.post(
            reverse('job_card_detail', args=[self.job_card.pk]),
            {'action': 'add_part', 'inventory_item': item.pk, 'quantity': str(quantity)},
        )

    # ------------------------------------------------------------------
    # Slice 4 - Job Card Detail page & junction billing
    # ------------------------------------------------------------------
    def test_get_detail_page_returns_200_and_lists_line_items(self):
        self._add_part(self.inventory_item, 2)

        resp = self.client.get(reverse('job_card_detail', args=[self.job_card.pk]))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['line_items']), 1)
        self.assertEqual(resp.context['line_items'][0].part_name, 'Spark Plug')
        self.assertContains(resp, 'Spark Plug')
        self.assertContains(resp, self.job_card.vehicle_number)

    def test_inventory_dropdown_excludes_zero_quantity_items(self):
        zero_item = InventoryItem.objects.create(
            workshop=self.workshop, part_name='Out Of Stock Belt',
            sku='OOS1', quantity=0, b2b_price=250,
        )

        resp = self.client.get(reverse('job_card_detail', args=[self.job_card.pk]))

        dropdown_pks = [i.pk for i in resp.context['inventory_items']]
        self.assertIn(self.inventory_item.pk, dropdown_pks)
        self.assertNotIn(zero_item.pk, dropdown_pks)
        self.assertNotContains(resp, 'Out Of Stock Belt')

    def test_accessing_another_workshops_job_card_returns_404(self):
        _, other_workshop = make_workshop('shop_b', 19.0, 72.8)
        other_job = JobCard.objects.create(
            workshop=other_workshop,
            vehicle_number='MH14ZZ9999',
            customer_complaint='Not yours',
            status=JobCard.Status.RECEIVED,
        )

        resp = self.client.get(reverse('job_card_detail', args=[other_job.pk]))

        self.assertEqual(resp.status_code, 404)

    def test_detail_redirects_to_dashboard_when_profile_missing(self):
        User.objects.create_user('noshop_temp', password='pass12345')
        self.client.login(username='noshop_temp', password='pass12345')

        resp = self.client.get(reverse('job_card_detail', args=[self.job_card.pk]))

        # dashboard itself bounces a profile-less user on to /profile/.
        self.assertRedirects(resp, reverse('dashboard'), target_status_code=302)

    def test_adding_two_different_parts_accumulates_total_bill(self):
        other_item = InventoryItem.objects.create(
            workshop=self.workshop, part_name='Brake Pad',
            sku='BP1', quantity=5, b2b_price=50.00,
        )

        self._add_part(self.inventory_item, 2)   # 2 * 99.50 = 199.00
        self._add_part(other_item, 3)            # 3 * 50.00 = 150.00

        self.job_card.refresh_from_db()
        self.assertEqual(self.job_card.line_items.count(), 2)
        self.assertEqual(float(self.job_card.total_bill), 349.00)

    def test_removing_one_of_several_line_items_recalculates_to_remaining_sum(self):
        other_item = InventoryItem.objects.create(
            workshop=self.workshop, part_name='Brake Pad',
            sku='BP1', quantity=5, b2b_price=50.00,
        )
        self._add_part(self.inventory_item, 2)   # 199.00
        self._add_part(other_item, 3)            # 150.00

        brake_line = self.job_card.line_items.get(part_name='Brake Pad')
        self.client.post(
            reverse('job_card_detail', args=[self.job_card.pk]),
            {'action': 'remove_part', 'line_item_id': brake_line.pk},
        )

        self.job_card.refresh_from_db()
        other_item.refresh_from_db()
        self.assertEqual(self.job_card.line_items.count(), 1)
        self.assertEqual(float(self.job_card.total_bill), 199.00)  # not zero
        self.assertEqual(other_item.quantity, 5)  # brake stock replenished

    def test_adding_same_part_twice_creates_two_line_items_and_deducts_stock_twice(self):
        self._add_part(self.inventory_item, 2)
        self._add_part(self.inventory_item, 3)

        self.inventory_item.refresh_from_db()
        self.job_card.refresh_from_db()
        self.assertEqual(self.job_card.line_items.count(), 2)
        self.assertEqual(self.inventory_item.quantity, 5)  # 10 - 2 - 3
        self.assertEqual(float(self.job_card.total_bill), 497.50)  # 5 * 99.50

    # ------------------------------------------------------------------
    # Slice 5 - Transactional stock deduction & validation boundaries
    # ------------------------------------------------------------------
    def test_adding_exactly_available_stock_zeroes_quantity_and_drops_from_dropdown(self):
        self._add_part(self.inventory_item, 10)  # exactly all of it

        self.inventory_item.refresh_from_db()
        self.job_card.refresh_from_db()
        self.assertEqual(self.inventory_item.quantity, 0)
        self.assertEqual(self.job_card.line_items.count(), 1)
        self.assertEqual(float(self.job_card.total_bill), 995.00)  # 10 * 99.50

        # A now-zero item must vanish from the add dropdown.
        resp = self.client.get(reverse('job_card_detail', args=[self.job_card.pk]))
        dropdown_pks = [i.pk for i in resp.context['inventory_items']]
        self.assertNotIn(self.inventory_item.pk, dropdown_pks)

    def test_add_part_with_zero_quantity_is_rejected_and_changes_nothing(self):
        resp = self._add_part(self.inventory_item, 0)

        self.inventory_item.refresh_from_db()
        self.job_card.refresh_from_db()
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.inventory_item.quantity, 10)
        self.assertEqual(self.job_card.line_items.count(), 0)
        self.assertEqual(float(self.job_card.total_bill), 0.0)

    def test_add_part_with_negative_quantity_is_rejected_and_changes_nothing(self):
        self._add_part(self.inventory_item, -3)

        self.inventory_item.refresh_from_db()
        self.job_card.refresh_from_db()
        self.assertEqual(self.inventory_item.quantity, 10)
        self.assertEqual(self.job_card.line_items.count(), 0)
        self.assertEqual(float(self.job_card.total_bill), 0.0)

    def test_add_part_with_non_numeric_quantity_is_rejected_and_changes_nothing(self):
        self.client.post(
            reverse('job_card_detail', args=[self.job_card.pk]),
            {'action': 'add_part', 'inventory_item': self.inventory_item.pk,
             'quantity': 'abc'},
        )

        self.inventory_item.refresh_from_db()
        self.job_card.refresh_from_db()
        self.assertEqual(self.inventory_item.quantity, 10)
        self.assertEqual(self.job_card.line_items.count(), 0)
        self.assertEqual(float(self.job_card.total_bill), 0.0)

    # ------------------------------------------------------------------
    # Slice 6 - Snapshot integrity (part_name / sku / unit_price frozen)
    # ------------------------------------------------------------------
    def test_renaming_catalog_item_leaves_snapshot_and_total_unchanged(self):
        self._add_part(self.inventory_item, 2)  # 199.00

        # Rename ONLY (price untouched) after the line item was snapshotted.
        self.inventory_item.part_name = 'Iridium Spark Plug'
        self.inventory_item.save()

        line_item = self.job_card.line_items.first()
        self.job_card.refresh_from_db()
        self.assertEqual(line_item.part_name, 'Spark Plug')  # frozen, not renamed
        self.assertEqual(float(self.job_card.total_bill), 199.00)

    def test_deleting_catalog_item_nulls_fk_but_preserves_full_snapshot(self):
        self._add_part(self.inventory_item, 2)  # 199.00

        # Pure delete (no prior price change) - SET_NULL on the FK.
        self.inventory_item.delete()

        line_item = self.job_card.line_items.first()
        self.job_card.refresh_from_db()
        self.assertIsNotNone(line_item)
        self.assertIsNone(line_item.inventory_item)
        self.assertEqual(line_item.part_name, 'Spark Plug')
        self.assertEqual(line_item.sku, 'SP1')
        self.assertEqual(float(line_item.unit_price), 99.50)
        self.assertEqual(float(self.job_card.total_bill), 199.00)
