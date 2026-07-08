from django.template.loader import render_to_string
from django.test import Client, TestCase
from django.urls import reverse


class CustomErrorPageTests(TestCase):
    """The app should show branded, friendly error pages instead of Django's
    default technical ones. Note: the test runner always sets DEBUG=False, so
    the 404 handler and CSRF-failure view use our templates here."""

    def test_404_renders_branded_page(self):
        resp = self.client.get('/this-page-does-not-exist/')
        self.assertEqual(resp.status_code, 404)
        self.assertContains(resp, 'Page not found', status_code=404)
        self.assertContains(resp, 'GarageNET', status_code=404)  # base layout applied

    def test_csrf_failure_renders_branded_page(self):
        # A POST without a CSRF token (e.g. a stale login form from another tab)
        # must land on the friendly security page, not Django's raw 403.
        csrf_client = Client(enforce_csrf_checks=True)
        resp = csrf_client.post(reverse('login'), {'username': 'x', 'password': 'y'})
        self.assertEqual(resp.status_code, 403)
        self.assertContains(resp, 'Security check failed', status_code=403)
        self.assertContains(resp, 'Return to login', status_code=403)

    def test_all_error_templates_render_without_error(self):
        # Guards against template inheritance / tag mistakes in any error page.
        for name, marker in [
            ('400.html', 'Bad request'),
            ('403.html', 'Access denied'),
            ('404.html', 'Page not found'),
            ('403_csrf.html', 'Security check failed'),
            ('500.html', 'Something went wrong on our end'),
        ]:
            html = render_to_string(name)
            self.assertIn(marker, html, f'{name} did not render its message')

    def test_500_template_is_self_contained(self):
        # The 500 handler renders with no context processors, so the page must
        # not depend on {{ request }}, {{ user }} or {% csrf_token %}.
        html = render_to_string('500.html')
        self.assertIn('<!doctype html>', html.lower())
        self.assertIn('500', html)
