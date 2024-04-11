from django.contrib.auth.models import User
from django.contrib.messages import constants, get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import reverse
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from NewEra.models import Organization, User, CaseLoadUser, TempCaseLoadUser
from NewEra.views import sign_up
from NewEra.forms import CaseLoadUserForm

# region Dashboard tests

class DashboardTestCase(TestCase):
    def setUp(self):
        self.dashboard_url = reverse('Dashboard')  # Assuming 'dashboard' is the URL name

        # Create a superuser for testing
        self.superuser = User.objects.create_superuser(
            username='admin',
            password='adminpassword',
            email='admin@example.com'
        )

    def test_dashboard_superuser(self):
        # Login as a superuser
        self.client.login(username='admin', password='adminpassword')

        # Make a GET request to the dashboard
        response = self.client.get(self.dashboard_url)

        # Assert that the response is successful (HTTP 200) and the expected context variables exist

        self.assertEqual(response.status_code, 200)
        self.assertTrue('admins' in response.context)
        self.assertTrue('reentry_coordinators' in response.context)
        self.assertTrue('community_outreach_workers' in response.context)
        self.assertTrue('service_providers' in response.context)
        self.assertTrue('resource_coordinators' in response.context)
        self.assertTrue('orgs' in response.context)
        self.assertTrue('supervisors' in response.context)
        self.assertTrue('form' in response.context)
        self.assertTrue('user' in response.context)

        # Assert that the superuser condition is met
        self.assertEqual(response.context['user'], self.superuser)
        self.assertTrue(response.context['admins'].exists())

    def test_dashboard_post_request(self):
        # Login as a superuser
        self.client.login(username='admin', password='adminpassword')

        # Make a POST request to the dashboard with organization creation data
        response = self.client.post(
            self.dashboard_url,
            {
                'org_name': 'Sample Organization'
            }
        )

        # Assert that the response is successful (HTTP 200) and a new organization is created
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Organization.objects.filter(name='Sample Organization').exists())

        # Assert that the success message is displayed
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, constants.SUCCESS)
        self.assertEqual(messages[0].message, 'Added a new organization to the system.')

        organization = Organization.objects.get(name='Sample Organization')
        organization_id = organization.id

        # Make a POST request to the dashboard with user creation data
        response = self.client.post(
            self.dashboard_url,
            {
                'username': 'newuser',
                'password': 'newpassword',
                'confirm_password': 'newpassword',
                'email': 'newuser@example.com',
                'phone': '1234567890',
                'first_name': 'John',
                'last_name': 'Doe',
                'organization': organization_id,
                'user_type': 'admin'
            }
        )

        # Assert that the response is successful (HTTP 200) and a new user is created
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertTrue(User.objects.get(username='newuser').is_superuser)

        # Assert that the success message is displayed
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, constants.SUCCESS)
        self.assertEqual(messages[0].message, 'Added a new user to the system.')

# endregion

# region Sign Up tests
class SignUpTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # Create a superuser for testing
        self.superuser = User.objects.create_superuser(
            username='admin',
            password='adminpassword',
            email='admin@example.com'
        )

        self.sign_up_form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'hi@gmail.com',
            'phone': '',
            'neighborhood': 'Prefer Not To Say',
            'case_label': 'Other',
        }

        self.no_email_or_phone_sign_up_form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'neighborhood': 'Prefer Not To Say',
            'case_label': 'Other',
            'phone': '',
            'email': ''
        }

    def test_valid_form_submission(self):
        request = self.factory.post('/sign_up/', data=self.sign_up_form_data)
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        response = sign_up(request)
        actual_messages = [m.message for m in messages]
        self.assertEqual(response.status_code, 302)
        self.assertIn('A confirmation message has been sent to you!', actual_messages)
        self.assertEqual(TempCaseLoadUser.objects.count(), 1)

    def test_invalid_form_submission(self):
        request = self.factory.post('/sign_up/', data=self.no_email_or_phone_sign_up_form_data)
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        response = sign_up(request)
        actual_messages = [m.message for m in messages]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TempCaseLoadUser.objects.count(), 0)
        self.assertIn('An error occurred while trying to sign up. Please check your form input', actual_messages)
# endregion