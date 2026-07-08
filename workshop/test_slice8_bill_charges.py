from django.test import TestCase
from django.urls import reverse

from .models import (
    AdditionalCharge,
    InventoryItem,
    JobCard,
    JobCardActivity,
)
from .tests import make_workshop


class BillAndAdditionalChargeTests(TestCase):
    """Coverage for the printable bill page, additional (labour) charges, and
    the activity audit trail wired up alongside them."""

    def setUp(self):
        self.user, self.workshop = make_workshop('shop_a', 18.52, 73.85)
        self.client.login(username='shop_a', password='pass12345')
        self.inventory_item = InventoryItem.objects.create(
            workshop=self.workshop, part_name='Spark Plug',
            sku='SP1', quantity=10, b2b_price=99.50,
        )
        self.job_card = JobCard.objects.create(
            workshop=self.workshop, vehicle_number='MH12A1',
            customer_complaint='Spark plug issue', status=JobCard.Status.READY,
        )

    def _add_part(self, quantity):
        return self.client.post(
            reverse('job_card_detail', args=[self.job_card.pk]),
            {'action': 'add_part', 'inventory_item': self.inventory_item.pk,
             'quantity': str(quantity)},
        )

    def _add_charge(self, description, amount):
        return self.client.post(
            reverse('job_card_bill', args=[self.job_card.pk]),
            {'action': 'add_charge', 'description': description, 'amount': str(amount)},
        )

    # ------------------------------------------------------------------
    # Additional charges & total recalculation
    # ------------------------------------------------------------------
    def test_add_charge_creates_charge_and_folds_into_total_with_parts(self):
        self._add_part(2)  # 2 * 99.50 = 199.00
        self._add_charge('Labour', 350)

        self.job_card.refresh_from_db()
        self.assertEqual(self.job_card.additional_charges.count(), 1)
        self.assertEqual(float(self.job_card.parts_total), 199.00)
        self.assertEqual(float(self.job_card.charges_total), 350.00)
        self.assertEqual(float(self.job_card.total_bill), 549.00)

    def test_remove_charge_recalculates_and_replenishes_nothing(self):
        self._add_part(2)             # 199.00
        self._add_charge('Labour', 350)
        charge = self.job_card.additional_charges.first()

        self.client.post(
            reverse('job_card_bill', args=[self.job_card.pk]),
            {'action': 'remove_charge', 'charge_id': charge.pk},
        )

        self.job_card.refresh_from_db()
        self.assertEqual(self.job_card.additional_charges.count(), 0)
        self.assertEqual(float(self.job_card.total_bill), 199.00)  # parts only

    def test_add_charge_with_zero_amount_is_rejected(self):
        self._add_charge('Bad', 0)
        self.job_card.refresh_from_db()
        self.assertEqual(self.job_card.additional_charges.count(), 0)
        self.assertEqual(float(self.job_card.total_bill), 0.0)

    def test_add_charge_with_negative_amount_is_rejected(self):
        self._add_charge('Bad', -50)
        self.job_card.refresh_from_db()
        self.assertEqual(self.job_card.additional_charges.count(), 0)

    def test_cannot_add_charge_to_another_workshops_job_card(self):
        _, other = make_workshop('shop_b', 19.0, 72.8)
        other_job = JobCard.objects.create(
            workshop=other, vehicle_number='MH14ZZ9', customer_complaint='x',
            status=JobCard.Status.READY,
        )
        resp = self.client.post(
            reverse('job_card_bill', args=[other_job.pk]),
            {'action': 'add_charge', 'description': 'Sneaky', 'amount': '100'},
        )
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(other_job.additional_charges.count(), 0)

    # ------------------------------------------------------------------
    # Bill page rendering
    # ------------------------------------------------------------------
    def test_bill_page_renders_parts_and_charges(self):
        self._add_part(2)
        self._add_charge('Labour', 350)

        resp = self.client.get(reverse('job_card_bill', args=[self.job_card.pk]))

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Spark Plug')
        self.assertContains(resp, 'Labour')
        self.assertContains(resp, self.workshop.shop_name)

    def test_bill_page_is_scoped_to_owner(self):
        _, other = make_workshop('shop_b', 19.0, 72.8)
        other_job = JobCard.objects.create(
            workshop=other, vehicle_number='MH14ZZ9', customer_complaint='x',
        )
        resp = self.client.get(reverse('job_card_bill', args=[other_job.pk]))
        self.assertEqual(resp.status_code, 404)

    # ------------------------------------------------------------------
    # Generate-bill affordance on the detail page
    # ------------------------------------------------------------------
    def test_generate_bill_button_shown_when_ready(self):
        resp = self.client.get(reverse('job_card_detail', args=[self.job_card.pk]))
        self.assertTrue(resp.context['is_ready'])
        self.assertContains(resp, reverse('job_card_bill', args=[self.job_card.pk]))
        self.assertContains(resp, 'Generate Bill')

    def test_generate_bill_button_hidden_when_not_ready(self):
        self.job_card.status = JobCard.Status.IN_PROGRESS
        self.job_card.save()
        resp = self.client.get(reverse('job_card_detail', args=[self.job_card.pk]))
        self.assertFalse(resp.context['is_ready'])
        self.assertNotContains(resp, 'Generate Bill')

    # ------------------------------------------------------------------
    # Activity audit trail
    # ------------------------------------------------------------------
    def test_generating_bill_logs_invoice_once(self):
        self.client.get(reverse('job_card_bill', args=[self.job_card.pk]))
        self.client.get(reverse('job_card_bill', args=[self.job_card.pk]))

        invoice_logs = self.job_card.activities.filter(
            event_type=JobCardActivity.EventType.INVOICE_GENERATED
        )
        self.assertEqual(invoice_logs.count(), 1)

    def test_part_and_charge_actions_are_logged(self):
        self._add_part(2)
        self._add_charge('Labour', 350)

        types = list(
            self.job_card.activities.values_list('event_type', flat=True)
        )
        self.assertIn(JobCardActivity.EventType.PART_ADDED, types)
        self.assertIn(JobCardActivity.EventType.CHARGE_ADDED, types)
