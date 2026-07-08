from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import JobCard
from .tests import make_workshop


class JobCardCreationDefaultsTests(TestCase):
    """Slice 3 / Story 5: creating a job card via the job_cards view."""

    def setUp(self):
        self.user, self.workshop = make_workshop('shop_a', 18.52, 73.85)
        self.client.login(username='shop_a', password='pass12345')

    def test_created_job_defaults_to_received_and_zero_bill(self):
        # JobCardForm only asks for vehicle_number + customer_complaint; the
        # model must supply the RECEIVED status and a zero opening bill.
        resp = self.client.post(reverse('job_cards'), {
            'action': 'create',
            'vehicle_number': 'MH12CD5678',
            'customer_complaint': 'Clutch slipping',
        })
        self.assertRedirects(resp, reverse('job_cards'))
        job = JobCard.objects.get(vehicle_number='MH12CD5678')
        self.assertEqual(job.status, JobCard.Status.RECEIVED)
        self.assertEqual(float(job.total_bill), 0.0)

    def test_create_ignores_client_supplied_workshop(self):
        # An attacker POSTing a 'workshop' field for someone else's shop must
        # not be able to plant a job in their ledger; the view forces the
        # logged-in workshop regardless of submitted data.
        _, other = make_workshop('shop_b', 19.0, 72.8)
        self.client.post(reverse('job_cards'), {
            'action': 'create',
            'vehicle_number': 'MH12EF9012',
            'customer_complaint': 'Oil leak',
            'workshop': other.pk,
        })
        job = JobCard.objects.get(vehicle_number='MH12EF9012')
        self.assertEqual(job.workshop, self.workshop)
        self.assertEqual(other.job_cards.count(), 0)


class JobCardStatusLifecycleTests(TestCase):
    """Slice 3 / Story 13: transitioning a job card's status."""

    def setUp(self):
        self.user, self.workshop = make_workshop('shop_a', 18.52, 73.85)
        self.client.login(username='shop_a', password='pass12345')

    def _make_job(self, vehicle_number):
        return JobCard.objects.create(
            workshop=self.workshop,
            vehicle_number=vehicle_number,
            customer_complaint='x',
            status=JobCard.Status.RECEIVED,
        )

    def test_each_valid_status_transition_persists(self):
        # Every non-default status reachable from RECEIVED must save through the
        # update_status seam. A fresh job per target keeps the cases isolated.
        targets = [
            JobCard.Status.IN_PROGRESS,
            JobCard.Status.WAITING_FOR_PARTS,
            JobCard.Status.READY,
        ]
        for i, target in enumerate(targets):
            with self.subTest(target=target):
                job = self._make_job(f'MH12TR{i:04d}')
                resp = self.client.post(reverse('job_cards'), {
                    'action': 'update_status',
                    'job_id': job.pk,
                    'status': target,
                })
                self.assertRedirects(resp, reverse('job_cards'))
                job.refresh_from_db()
                self.assertEqual(job.status, target)

    def test_garbage_status_leaves_job_unchanged(self):
        # A status value outside the TextChoices is rejected by
        # JobCardStatusForm validation, so the job keeps its prior status.
        job = self._make_job('MH12GB0001')
        resp = self.client.post(reverse('job_cards'), {
            'action': 'update_status',
            'job_id': job.pk,
            'status': 'NOT_A_REAL_STATUS',
        })
        self.assertRedirects(resp, reverse('job_cards'))
        job.refresh_from_db()
        self.assertEqual(job.status, JobCard.Status.RECEIVED)


class JobCardListingTests(TestCase):
    """The job_cards GET listing surfaces the workshop's jobs newest-first."""

    def setUp(self):
        self.user, self.workshop = make_workshop('shop_a', 18.52, 73.85)
        self.client.login(username='shop_a', password='pass12345')

    def test_jobs_listed_newest_first(self):
        # Meta.ordering = ['-created_at'] should drive the view's job list.
        # created_at is auto_now_add, so stamp explicit times after creation.
        now = timezone.now()
        specs = [
            ('MH12OLD001', now - timedelta(days=2)),
            ('MH12MID002', now - timedelta(days=1)),
            ('MH12NEW003', now),
        ]
        for vehicle_number, created in specs:
            job = JobCard.objects.create(
                workshop=self.workshop,
                vehicle_number=vehicle_number,
                customer_complaint='x',
            )
            JobCard.objects.filter(pk=job.pk).update(created_at=created)

        resp = self.client.get(reverse('job_cards'))
        self.assertEqual(resp.status_code, 200)
        ordered = [j.vehicle_number for j in resp.context['jobs']]
        self.assertEqual(ordered, ['MH12NEW003', 'MH12MID002', 'MH12OLD001'])


class JobCardModelDisplayTests(TestCase):
    """Human-facing rendering of a JobCard's status."""

    def setUp(self):
        self.user, self.workshop = make_workshop('shop_a', 18.52, 73.85)

    def _job(self, status):
        return JobCard.objects.create(
            workshop=self.workshop,
            vehicle_number='MH12DS0001',
            customer_complaint='x',
            status=status,
        )

    def test_get_status_display_maps_codes_to_labels(self):
        expected = {
            JobCard.Status.RECEIVED: 'Received',
            JobCard.Status.IN_PROGRESS: 'In-Progress',
            JobCard.Status.WAITING_FOR_PARTS: 'Waiting-for-Parts',
            JobCard.Status.READY: 'Ready',
        }
        for code, label in expected.items():
            with self.subTest(code=code):
                self.assertEqual(self._job(code).get_status_display(), label)

    def test_str_includes_vehicle_number_and_status_label(self):
        job = self._job(JobCard.Status.IN_PROGRESS)
        self.assertEqual(str(job), 'MH12DS0001 [In-Progress]')
