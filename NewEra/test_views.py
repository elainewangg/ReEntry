from django.contrib.auth.models import User
from django.contrib.messages import constants, get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import reverse
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

# from NewEra.forms import StudentForm, StudentQuarterlyUpdateForm, StudentWeeklyUpdateForm
# from NewEra.models import Organization, Student, StudentQuarterlyUpdate, StudentWeeklyUpdate, User
from NewEra.models import Organization, User
# from NewEra.views import get_student, student

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
        self.assertTrue('sows' in response.context)
        self.assertTrue('orgs' in response.context)
        self.assertTrue('supervisors' in response.context)
        self.assertTrue('form' in response.context)
        self.assertTrue('user' in response.context)
        self.assertTrue('safe_passage_coordinators' in response.context)
        self.assertTrue('safe_passage_coordinator_supervisors' in response.context)

        # Assert that the superuser condition is met
        self.assertEqual(response.context['user'], self.superuser)
        self.assertTrue(response.context['admins'].exists())

    def test_dashboard_non_superuser(self):
        # Create a regular user for testing
        regular_user = User.objects.create_user(
            username='user',
            password='userpassword',
            email='user@example.com'
        )

        # Login as the regular user
        self.client.login(username='user', password='userpassword')

        # Make a GET request to the dashboard
        response = self.client.get(self.dashboard_url)

        # Assert that the response is a 404 (HTTP 404 Error)
        self.assertEqual(response.status_code, 404)

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

# region Student tests

# class StudentViewTestCase(TestCase):
#     def setUp(self):
#         self.factory = RequestFactory()
#         self.organization = Organization.objects.create(name='Test School')
#         self.superuser = User.objects.create_superuser(username='admin', password='password')
#         self.coordinator_supervisor = User.objects.create_user(username='coordinator_supervisor', password='password', is_safe_passage_coordinator_supervisor=True, organization_id=self.organization.id)
#         self.coordinator = User.objects.create_user(username='coordinator', password='password', is_safe_passage_coordinator=True, organization_id=self.organization.id)
#         self.inactive_staff = User.objects.create_user(username='inactive_staff', password='password', is_active=False)
#         self.student_form_data = {
#             'staff_id': self.coordinator.id,
#             'first_name': 'John',
#             'last_name': 'Doe',
#             'phone': '5135551212',
#             'graduation_year': 2023
#         }
#         self.invalid_student_form_data = {
#             'first_name': '',
#             'last_name': '',
#             'phone': ''
#         }

#     def test_valid_form_submission(self):
#         request = self.factory.post('/student/', data=self.student_form_data)
#         request.user = self.coordinator
#         setattr(request, 'session', 'session')
#         messages = FallbackStorage(request)
#         setattr(request, '_messages', messages)

#         response = student(request)
#         actual_messages = [msg.message for msg in messages._loaded_data]
        
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(Student.objects.count(), 1)
#         self.assertIn('Successfully added John Doe to Students.', actual_messages)

#     def test_superuser_view(self):
#         self.client.login(username=self.superuser.username, password='password')
#         response = self.client.get('/schools/student/')

#         # Assert that the response is successful (HTTP 200) and the expected context variables exist
#         self.assertEqual(response.status_code, 200)
#         self.assertQuerysetEqual(response.context['students'], Student.objects.all(), transform=lambda x: x)
#         self.assertQuerysetEqual(response.context['staff'], User.objects.filter(is_safe_passage_coordinator=True, is_active=True).order_by('first_name', 'last_name'), transform=lambda x: x)
#         self.assertIsInstance(response.context['form'], StudentForm)

#     def test_coordinator_supervisor_view(self):
#         self.client.login(username=self.coordinator_supervisor.username, password='password')
#         response = self.client.get('/schools/student/')

#         self.assertEqual(response.status_code, 200)
#         self.assertQuerysetEqual(response.context['students'], Student.objects.filter(user__in=User.objects.filter(organization=self.coordinator_supervisor.organization)).order_by('first_name', 'last_name'), transform=lambda x: x)
#         self.assertIsInstance(response.context['form'], StudentForm)

#     def test_coordinator_view(self):
#         self.client.login(username=self.coordinator.username, password='password')
#         response = self.client.get('/schools/student/')

#         self.assertEqual(response.status_code, 200)
#         self.assertQuerysetEqual(response.context['students'], Student.objects.filter(user=self.coordinator).order_by('first_name', 'last_name'), transform=lambda x: x)
#         self.assertIsInstance(response.context['form'], StudentForm)

#     def test_unauthenticated_user_view(self):
#         response = self.client.get('/student/')

#         self.assertIn(response.status_code, [302, 404])  # Adjust as per desired behavior

#     def test_unauthorized_user_raises_http404(self):
#         request = self.factory.get('/student/')
#         request.user = User.objects.create_user(username='unauthorized', password='password')

#         with self.assertRaises(Http404):
#             student(request)

#     def test_student_creation_without_phone_or_email(self):
#         form_data = {
#             'first_name': 'John',
#             'last_name': 'Doe',
#             'graduation_year': 2023,
#             'email': '',
#             'phone': '',
#             'parent_first_name': 'Jane',
#             'parent_last_name': 'Doe',
#             'parent_email': '',
#             'parent_phone': '',
#             'is_active': True,
#             'user': None,
#             'date_created': None,
#         }
#         form = StudentForm(data=form_data)
#         self.assertFalse(form.is_valid())
#         self.assertIn('You must input either a phone number or an email address for this student.', form.errors['__all__'])

# class GetStudentViewTestCase(TestCase):
#     def setUp(self):
#         self.client = Client()
#         self.factory = RequestFactory()
#         self.organization1 = Organization.objects.create(name='Test School')
#         self.organization2 = Organization.objects.create(name='Test School 2')
#         self.coordinator = User.objects.create_user(username='coordinator', password='password', is_safe_passage_coordinator=True, organization_id=self.organization1.id)
#         self.student = Student.objects.create(first_name='John', last_name='Doe', user_id=self.coordinator.id, graduation_year=2023)
#         self.user = User.objects.create_user(username='testuser', password='password')
#         self.superuser = User.objects.create_superuser(username='admin', password='password')
#         self.coordinator_supervisor = User.objects.create_user(username='coordinator_supervisor', password='password', is_safe_passage_coordinator_supervisor=True, organization_id=self.organization1.id)
#         self.coordinator_supervisor2 = User.objects.create_user(username='coordinator_supervisor2', password='password', is_safe_passage_coordinator_supervisor=True, organization_id=self.organization2.id)
#         self.other_user = User.objects.create_user(username='other_user', password='password', is_safe_passage_coordinator=True, organization_id=self.organization2.id)

#     def test_get_student_authenticated_user(self):
#         # Test for an authenticated user who is the owner of the student
#         request = self.factory.get(reverse('Show Student', args=[self.student.id]))
#         request.user = self.user

#         with self.assertRaises(PermissionDenied):
#             get_student(request, self.student.id)

#     def test_get_student_superuser(self):
#         # Test for a superuser
#         self.client.login(username=self.superuser.username, password='password')
#         response = self.client.get(reverse('Show Student', args=[self.student.id]))
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'NewEra/get_student.html')
#         self.assertEqual(response.context['student'], self.student)

#     def test_get_student_coordinator_supervisor_same_organization(self):
#         # Test for a coordinator supervisor who belongs to the same organization as the student
#         self.client.login(username=self.coordinator_supervisor.username, password='password')
#         response = self.client.get(reverse('Show Student', args=[self.student.id]))
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'NewEra/get_student.html')
#         self.assertEqual(response.context['student'], self.student)

#     def test_get_student_coordinator_supervisor_different_organization(self):
#         # Test for a coordinator supervisor who does not belong to the same organization as the student
#         request = self.factory.get(reverse('Show Student', args=[self.student.id]))
#         request.user = self.coordinator_supervisor2

#         with self.assertRaises(PermissionDenied):
#             get_student(request, self.student.id)

#     def test_get_student_unauthenticated_user(self):
#         # Test for an unauthenticated user
#         response = self.client.get(reverse('Show Student', args=[self.student.id]))

#         self.assertEqual(response.status_code, 302)

#     def test_get_student_other_user(self):
#         # Test for a user who is not the owner of the student
#         request = self.factory.get(reverse('Show Student', args=[self.student.id]))
#         request.user = self.other_user

#         with self.assertRaises(PermissionDenied):
#             get_student(request, self.student.id)

#     def test_get_student_invalid_id(self):
#         # Test for an invalid student ID
#         invalid_id = 9999
#         self.client.login(username=self.coordinator.username, password='password')

#         response = self.client.get(reverse('Show Student', args=[invalid_id]))
#         self.assertEqual(response.status_code, 404)

# class EditStudentViewTestCase(TestCase):
#     def setUp(self):
#         self.client = Client()
#         self.factory = RequestFactory()
#         self.organization = Organization.objects.create(name='Test School')
#         self.coordinator = User.objects.create_user(username='coordinator', password='password', is_safe_passage_coordinator=True, organization_id=self.organization.id)
#         self.student = Student.objects.create(first_name='John', last_name='Doe', user_id=self.coordinator.id, graduation_year=2023)
#         self.user = User.objects.create_user(username='testuser', password='password')
#         self.superuser = User.objects.create_superuser(username='admin', password='password')
#         self.coordinator_supervisor = User.objects.create_user(username='coordinator_supervisor', password='password', is_safe_passage_coordinator_supervisor=True, organization_id=self.organization.id)

#     def test_edit_student_authenticated_owner(self):
#         # Test editing a student by the owner (authenticated user)
#         self.client.login(username=self.coordinator.username, password='password')

#         # Edit Student view
#         response = self.client.get(reverse('Edit Student', args=[self.student.id]))
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'NewEra/edit_student.html')
#         self.assertIsInstance(response.context['form'], StudentForm)
#         self.assertEqual(response.context['student'], self.student)
#         self.assertEqual(response.context['action'], 'Edit')

#         # Submitting a valid form
#         form_data = {
#             'first_name': 'John',
#             'last_name': 'Doe',
#             'email': 'user@domain.com',
#             'parent_first_name': 'Parent',
#             'parent_last_name': 'Name',
#             'graduation_year': 2023
#         }
#         response = self.client.post(reverse('Edit Student', args=[self.student.id]), data=form_data)
#         self.assertEqual(response.status_code, 302)

#         # Fetch the updated student object from the database
#         updated_student = Student.objects.get(id=self.student.id)
#         # Verify the changes in the database
#         self.assertEqual(updated_student.parent_first_name, 'Parent')
#         self.assertEqual(updated_student.parent_last_name, 'Name')

#         # Verify the success message
#         messages = list(get_messages(response.wsgi_request))
#         self.assertEqual(len(messages), 1)
#         self.assertEqual(str(messages[0]), 'John Doe successfully edited.')

#         # Get Student view to verify the changes
#         response = self.client.get(reverse('Show Student', args=[self.student.id]))
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'NewEra/get_student.html')
#         self.assertEqual(response.context['student'].parent_first_name, 'Parent')
#         self.assertEqual(response.context['student'].parent_last_name, 'Name')

#     def test_edit_student_superuser(self):
#         # Test editing a student by a superuser
#         self.client.login(username=self.superuser.username, password='password')
        
#         # Edit Student view
#         response = self.client.get(reverse('Edit Student', args=[self.student.id]))
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'NewEra/edit_student.html')
#         self.assertIsInstance(response.context['form'], StudentForm)
#         self.assertEqual(response.context['student'], self.student)
#         self.assertEqual(response.context['action'], 'Edit')

#         # Submitting a valid form
#         form_data = {
#             'first_name': 'John',
#             'last_name': 'Doe',
#             'email': 'user@domain.com',
#             'parent_first_name': 'Parent',
#             'parent_last_name': 'Name',
#             'graduation_year': 2023
#         }
#         response = self.client.post(reverse('Edit Student', args=[self.student.id]), data=form_data)
#         self.assertEqual(response.status_code, 302)

#         # Fetch the updated student object from the database
#         updated_student = Student.objects.get(id=self.student.id)
#         # Verify the changes in the database
#         self.assertEqual(updated_student.parent_first_name, 'Parent')
#         self.assertEqual(updated_student.parent_last_name, 'Name')

#         # Verify the success message
#         messages = list(get_messages(response.wsgi_request))
#         self.assertEqual(len(messages), 1)
#         self.assertEqual(str(messages[0]), 'John Doe successfully edited.')

#         # Get Student view to verify the changes
#         response = self.client.get(reverse('Show Student', args=[self.student.id]))
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'NewEra/get_student.html')
#         self.assertEqual(response.context['student'].parent_first_name, 'Parent')
#         self.assertEqual(response.context['student'].parent_last_name, 'Name')

#     def test_edit_student_coordinator_supervisor(self):
#         # Test editing a student by a coordinator supervisor of the same organization
#         self.client.login(username=self.coordinator_supervisor.username, password='password')
        
#         # Edit Student view
#         response = self.client.get(reverse('Edit Student', args=[self.student.id]))
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'NewEra/edit_student.html')
#         self.assertIsInstance(response.context['form'], StudentForm)
#         self.assertEqual(response.context['student'], self.student)
#         self.assertEqual(response.context['action'], 'Edit')

#         # Submitting a valid form
#         form_data = {
#             'first_name': 'John',
#             'last_name': 'Doe',
#             'email': 'user@domain.com',
#             'parent_first_name': 'Parent',
#             'parent_last_name': 'Name',
#             'graduation_year': 2023
#         }
#         response = self.client.post(reverse('Edit Student', args=[self.student.id]), data=form_data)
#         self.assertEqual(response.status_code, 302)

#         # Fetch the updated student object from the database
#         updated_student = Student.objects.get(id=self.student.id)
#         # Verify the changes in the database
#         self.assertEqual(updated_student.parent_first_name, 'Parent')
#         self.assertEqual(updated_student.parent_last_name, 'Name')

#         # Verify the success message
#         messages = list(get_messages(response.wsgi_request))
#         self.assertEqual(len(messages), 1)
#         self.assertEqual(str(messages[0]), 'John Doe successfully edited.')

#         # Get Student view to verify the changes
#         response = self.client.get(reverse('Show Student', args=[self.student.id]))
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'NewEra/get_student.html')
#         self.assertEqual(response.context['student'].parent_first_name, 'Parent')
#         self.assertEqual(response.context['student'].parent_last_name, 'Name')

#     def test_edit_student_unauthenticated_user(self):
#         # Test editing a student by an unauthenticated user
#         response = self.client.get(reverse('Edit Student', args=[self.student.id]))
#         self.assertEqual(response.status_code, 302)
        
#     def test_edit_student_unauthorized_user(self):
#         # Test editing a student by a user without sufficient privileges
#         self.client.login(username=self.user.username, password='password')
#         response = self.client.get(reverse('Edit Student', args=[self.student.id]))
#         self.assertEqual(response.status_code, 404)

# class DeleteStudentViewTestCase(TestCase):
#     def setUp(self):
#         self.organization = Organization.objects.create(name='Test School')
#         self.coordinator = User.objects.create_user(username='coordinator', password='password', is_safe_passage_coordinator=True, organization_id=self.organization.id)
#         self.student = Student.objects.create(first_name='John', last_name='Doe', user_id=self.coordinator.id, graduation_year=2023)
        
#     def test_delete_student_authenticated_owner(self):
#         # Log in as the student owner
#         self.client.login(username=self.coordinator.username, password='password')
        
#         # Delete Student view
#         response = self.client.get(reverse('Delete Student', args=[self.student.id]))
        
#         # Check if the response status code is 200 and the correct template is used
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'NewEra/delete_student.html')
        
#         # Check if the student is passed to the context
#         self.assertEqual(response.context['student'], self.student)
        
#         # Submitting the delete form
#         response = self.client.post(reverse('Delete Student', args=[self.student.id]))
        
#         # Fetch the updated student object from the database
#         updated_student = Student.objects.get(id=self.student.id)
        
#         # Check if the student is made inactive
#         self.assertFalse(updated_student.is_active)
        
#         # Check if the success message is displayed
#         messages = list(get_messages(response.wsgi_request))
#         self.assertEqual(len(messages), 1)
#         self.assertEqual(str(messages[0]), 'John Doe was made inactive.')
        
#         # Check if the redirection to the student details page is performed
#         self.assertRedirects(response, reverse('Show Student', args=[self.student.id]))

# # endregion 

# # region Student Weekly Update tests

# class StudentWeeklyUpdateViewTest(TestCase):
#     def setUp(self):
#         self.factory = RequestFactory()
#         self.user = User.objects.create_user(username='testuser', password='password', is_safe_passage_coordinator=True)
#         self.student = Student.objects.create(
#             user=self.user,
#             first_name='John',
#             last_name='Doe',
#             email='john.doe@example.com',
#             phone='1234567890',
#             parent_first_name='Jane',
#             parent_last_name='Doe',
#             parent_email='jane.doe@example.com',
#             parent_phone='9876543210',
#             is_active=True, 
#             graduation_year=2023
#         )

#     def test_student_weekly_update_view_post_valid_form(self):
#         data = {
#             'weekly_absences': 2,
#             'extra_curricular': 'Football',
#             'special_needs': 'None',
#             'notes': 'Some notes',
#             'is_active': True,
#             'id_student': self.student.id,
#             'date': '2023-07-03',
#         }

#         self.client.login(username=self.user.username, password='password')

#         # Access the student_weekly_update view
#         response = self.client.post(reverse('Weekly Student Update'), data)
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'NewEra/student_weekly_update.html')
#         self.assertIn('form', response.context)
#         self.assertIsInstance(response.context['form'], StudentWeeklyUpdateForm)
#         self.assertTrue(StudentWeeklyUpdate.objects.filter(student=self.student).exists())

#         # Verify the success message
#         messages = list(get_messages(response.wsgi_request))
#         self.assertEqual(len(messages), 1)
#         self.assertEqual(str(messages[0]), f"Successfully added {self.student.get_full_name()} to the Weekly Student Updates.")

#     def test_student_weekly_update_view_post_invalid_form(self):
#         data = {}  # Empty data to trigger form validation error

#         self.client.login(username=self.user.username, password='password')

#         # Access the student_weekly_update view
#         response = self.client.post(reverse('Weekly Student Update'), data)

#         self.assertEqual(response.status_code, 404)
#         self.assertFalse(StudentWeeklyUpdate.objects.filter(student=self.student).exists())

#     def test_student_weekly_update_view_get(self):
#         self.client.login(username=self.user.username, password='password')

#         # Access the student_weekly_update view
#         response = self.client.get(reverse('Weekly Student Update'))

#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'NewEra/student_weekly_update.html')
#         self.assertIn('form', response.context)
#         self.assertIsInstance(response.context['form'], StudentWeeklyUpdateForm)
#         self.assertIn('students', response.context)
#         expected_students = Student.objects.filter(user=self.user).order_by('first_name', 'last_name').values_list('pk', flat=True)
#         actual_students = response.context['students'].values_list('pk', flat=True)
#         self.assertListEqual(list(actual_students), list(expected_students))

# class GetStudentWeeklyUpdateViewTest(TestCase):
#     def setUp(self):
#         self.user = User.objects.create_user(username='testuser', password='password', is_safe_passage_coordinator=True)
#         self.student = Student.objects.create(
#             user=self.user,
#             first_name='John',
#             last_name='Doe',
#             email='john.doe@example.com',
#             phone='1234567890',
#             parent_first_name='Jane',
#             parent_last_name='Doe',
#             parent_email='jane.doe@example.com',
#             parent_phone='9876543210',
#             is_active=True,
#             date_created=timezone.now(), 
#             graduation_year=2023
#         )
#         self.weekly_update = StudentWeeklyUpdate.objects.create(
#             student=self.student,
#             weekly_absences=2,
#             extra_curricular='Sports',
#             special_needs='None',
#             notes='Some notes',
#             is_active=True,
#             date_created=timezone.now()
#         )
        
#     def test_get_student_weekly_update(self):
#         self.client.login(username=self.user.username, password='password')
        
#         url = reverse('Show Weekly Student Update', args=[self.weekly_update.id])
        
#         response = self.client.get(url)
        
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'NewEra/get_student_weekly_update.html')
#         self.assertContains(response, self.student.get_full_name())
#         self.assertContains(response, self.weekly_update.student.user.get_full_name())
#         self.assertContains(response, self.weekly_update.weekly_absences)
#         self.assertContains(response, self.weekly_update.extra_curricular)
#         self.assertContains(response, self.weekly_update.special_needs)
#         self.assertContains(response, self.weekly_update.notes)
        
#     def test_get_student_weekly_update_unauthorized(self):
#         unauthorized_user = User.objects.create_user(username='unauthorized', password='password')
        
#         self.client.login(username=unauthorized_user.username, password='password')
        
#         response = self.client.get(reverse('Show Weekly Student Update', args=[self.weekly_update.id]))
        
#         self.assertEqual(response.status_code, 404)

# class EditStudentWeeklyUpdateViewTest(TestCase):
#     def setUp(self):
#         self.client = Client()
#         self.user = User.objects.create_user(username='testuser', password='testpassword', is_safe_passage_coordinator=True)
#         self.student = Student.objects.create(
#             user=self.user,
#             first_name='John',
#             last_name='Doe',
#             email='john.doe@example.com',
#             phone='1234567890',
#             parent_first_name='Jane',
#             parent_last_name='Doe',
#             parent_email='jane.doe@example.com',
#             parent_phone='9876543210', 
#             graduation_year=2023
#         )
#         self.weekly_update = StudentWeeklyUpdate.objects.create(
#             student=self.student,
#             weekly_absences=2,
#             extra_curricular='Sports',
#             special_needs='None',
#             notes='No additional notes',
#             is_active=True
#         )

#     def test_edit_student_weekly_update_view(self):
#         self.client.force_login(self.user)

#         response = self.client.get(reverse('Edit Weekly Student Update', args=[self.weekly_update.id]))

#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'NewEra/edit_student_weekly_update.html')
#         self.assertContains(response, 'Edit Student Weekly Update')

#     def test_edit_student_weekly_update_view_post(self):
#         data = {
#             'weekly_absences': 3,
#             'extra_curricular': 'Music',
#             'special_needs': 'None',
#             'notes': 'No additional notes',
#             'is_active': True,
#             'id_student': self.student.id
#         }
#         self.client.force_login(self.user)

#         response = self.client.post(reverse('Edit Weekly Student Update', args=[self.weekly_update.id]), data)

#         updated_weekly_update = StudentWeeklyUpdate.objects.get(id=self.weekly_update.id)
        
#         self.assertEqual(response.status_code, 302)  # Redirect after successful form submission
#         self.assertEqual(updated_weekly_update.weekly_absences, 3)
#         self.assertEqual(updated_weekly_update.extra_curricular, 'Music')
#         self.assertEqual(updated_weekly_update.special_needs, 'None')
#         self.assertEqual(updated_weekly_update.notes, 'No additional notes')
#         self.assertEqual(updated_weekly_update.is_active, True)

# class DeleteStudentWeeklyUpdateViewTest(TestCase):
#     def setUp(self):
#         self.client = Client()
#         self.organization1 = Organization.objects.create(name='Test School 1')
#         self.organization2 = Organization.objects.create(name='Test School 2')
#         self.user = User.objects.create_user(username='testuser', password='testpassword', organization=self.organization1, is_safe_passage_coordinator=True)
#         self.user2 = User.objects.create_user(username='testuser2', password='testpassword', organization=self.organization2, is_safe_passage_coordinator=True)
#         self.student = Student.objects.create(user=self.user, first_name='John', last_name='Doe', graduation_year=2023)
#         self.weekly_update = StudentWeeklyUpdate.objects.create(student=self.student, is_active=True, weekly_absences=0)

#     def test_delete_student_weekly_update_view(self):
#         self.client.force_login(self.user)
#         response = self.client.get(reverse('Delete Weekly Student Update', args=[self.weekly_update.id]))
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'NewEra/delete_student_weekly_update.html')
#         self.assertEqual(response.context['weekly_update'], self.weekly_update)

#     def test_delete_student_weekly_update_view_post(self):
#         self.client.force_login(self.user)
#         response = self.client.post(reverse('Delete Weekly Student Update', args=[self.weekly_update.id]))
#         self.assertEqual(response.status_code, 302)
#         self.assertTrue(StudentWeeklyUpdate.objects.filter(id=self.weekly_update.id, is_active=False).exists())

#     def test_delete_student_weekly_update_view_unauthenticated(self):
#         response = self.client.get(reverse('Delete Weekly Student Update', args=[self.weekly_update.id]), follow=True)
#         redirect_target = reverse('Login') + '?next=' + reverse('Delete Weekly Student Update', args=[self.weekly_update.id])
#         self.assertRedirects(response, redirect_target)
#         self.assertTemplateUsed(response, 'NewEra/login.html')

#     def test_delete_student_weekly_update_view_different_user(self):
#         other_user = User.objects.create_user(username='otheruser', password='testpassword')
#         self.client.force_login(other_user)
#         response = self.client.get(reverse('Delete Weekly Student Update', args=[self.weekly_update.id]))
#         self.assertEqual(response.status_code, 404)

#     def test_delete_student_weekly_update_view_superuser(self):
#         super_user = User.objects.create_superuser(
#             username='admin',
#             password='adminpassword',
#             email='admin@example.com'
#         )
#         self.client.force_login(super_user)
#         response = self.client.get(reverse('Delete Weekly Student Update', args=[self.weekly_update.id]))
#         self.assertEqual(response.status_code, 200)  # Superuser can access the view

#     def test_delete_student_weekly_update_view_safe_passage_coordinator_different_organization(self):
#         self.client.force_login(self.user2)
#         response = self.client.get(reverse('Delete Weekly Student Update', args=[self.weekly_update.id]))
#         self.assertEqual(response.status_code, 404)  # Safe Passage Coordinator from a different organization cannot access the view

# # endregion

# # region Student Quarterly Update tests

# class StudentQuarterlyUpdateViewTest(TestCase):
#     def setUp(self):
#         self.factory = RequestFactory()
#         self.user = User.objects.create_user(username='testuser', password='password', is_safe_passage_coordinator=True)
#         self.student = Student.objects.create(
#             user=self.user,
#             first_name='John',
#             last_name='Doe',
#             email='john.doe@example.com',
#             phone='1234567890',
#             parent_first_name='Jane',
#             parent_last_name='Doe',
#             parent_email='jane.doe@example.com',
#             parent_phone='9876543210',
#             is_active=True, 
#             graduation_year=2023
#         )

#     def test_student_quarterly_update_view_post_valid_form(self):
#         data = {
#             'q1_gpa': 2,
#             'q1_behavioral_infractions': 'None',
#             'q2_gpa': 3,
#             'q2_behavioral_infractions': '1 minor fight',
#             'is_active': True,
#             'id_student': self.student.id,
#             'date_created': '2023-07-05',
#         }

#         self.client.login(username=self.user.username, password='password')

#         # Access the student_quarterly_update view
#         response = self.client.post(reverse('Quarterly Student Update'), data)
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'NewEra/student_quarterly_update.html')
#         self.assertIn('form', response.context)
#         self.assertIsInstance(response.context['form'], StudentQuarterlyUpdateForm)
#         self.assertTrue(StudentQuarterlyUpdate.objects.filter(student=self.student).exists())

#         # Verify the success message
#         messages = list(get_messages(response.wsgi_request))
#         self.assertEqual(len(messages), 1)
#         self.assertEqual(str(messages[0]), f"Successfully added {self.student.get_full_name()} to the Quarterly Student Updates.")

#     def test_student_quarterly_update_view_post_invalid_form(self):
#         data = {}  # Empty data to trigger form validation error

#         self.client.login(username=self.user.username, password='password')

#         # Access the student_quarterly_update view
#         response = self.client.post(reverse('Quarterly Student Update'), data)

#         self.assertEqual(response.status_code, 404)
#         self.assertFalse(StudentQuarterlyUpdate.objects.filter(student=self.student).exists())

#     def test_student_quarterly_update_view_get(self):
#         self.client.login(username=self.user.username, password='password')

#         # Access the student_quarterly_update view
#         response = self.client.get(reverse('Quarterly Student Update'))

#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'NewEra/student_quarterly_update.html')
#         self.assertIn('form', response.context)
#         self.assertIsInstance(response.context['form'], StudentQuarterlyUpdateForm)
#         self.assertIn('students', response.context)
#         expected_students = Student.objects.filter(user=self.user).order_by('first_name', 'last_name').values_list('pk', flat=True)
#         actual_students = response.context['students'].values_list('pk', flat=True)
#         self.assertListEqual(list(actual_students), list(expected_students))

# class GetStudentQuarterlyUpdateViewTest(TestCase):
#     def setUp(self):
#         self.user = User.objects.create_user(username='testuser', password='password', is_safe_passage_coordinator=True)
#         self.student = Student.objects.create(
#             user=self.user,
#             first_name='John',
#             last_name='Doe',
#             email='john.doe@example.com',
#             phone='1234567890',
#             parent_first_name='Jane',
#             parent_last_name='Doe',
#             parent_email='jane.doe@example.com',
#             parent_phone='9876543210',
#             is_active=True,
#             date_created=timezone.now(), 
#             graduation_year=2023
#         )
#         self.quarterly_update = StudentQuarterlyUpdate.objects.create(
#             student=self.student,
#             q1_gpa=2,
#             q1_behavioral_infractions='None',
#             q2_gpa=3,
#             q2_behavioral_infractions='1 minor fight',
#             is_active=True,
#             date_created=timezone.now()
#         )
        
#     def test_get_student_quarterly_update(self):
#         self.client.login(username=self.user.username, password='password')
        
#         url = reverse('Show Quarterly Student Update', args=[self.quarterly_update.id])
        
#         response = self.client.get(url)
        
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'NewEra/get_student_quarterly_update.html')
#         self.assertContains(response, self.student.get_full_name())
#         self.assertContains(response, self.quarterly_update.student.user.get_full_name())
#         self.assertContains(response, self.quarterly_update.q1_gpa)
#         self.assertContains(response, self.quarterly_update.q1_behavioral_infractions)
#         self.assertContains(response, self.quarterly_update.q2_gpa)
#         self.assertContains(response, self.quarterly_update.q2_behavioral_infractions)
#         self.assertContains(response, self.quarterly_update.q3_gpa)
#         self.assertContains(response, self.quarterly_update.q3_behavioral_infractions)
#         self.assertContains(response, self.quarterly_update.q4_gpa)
#         self.assertContains(response, self.quarterly_update.q4_behavioral_infractions)
        
#     def test_get_student_quarterly_update_unauthorized(self):
#         unauthorized_user = User.objects.create_user(username='unauthorized', password='password')
        
#         self.client.login(username=unauthorized_user.username, password='password')
        
#         response = self.client.get(reverse('Show Quarterly Student Update', args=[self.quarterly_update.id]))
        
#         self.assertEqual(response.status_code, 404)

# class EditStudentQuarterlyUpdateViewTest(TestCase):
#     def setUp(self):
#         self.client = Client()
#         self.user = User.objects.create_user(username='testuser', password='testpassword', is_safe_passage_coordinator=True)
#         self.student = Student.objects.create(
#             user=self.user,
#             first_name='John',
#             last_name='Doe',
#             email='john.doe@example.com',
#             phone='1234567890',
#             parent_first_name='Jane',
#             parent_last_name='Doe',
#             parent_email='jane.doe@example.com',
#             parent_phone='9876543210', 
#             graduation_year=2023
#         )
#         self.quarterly_update = StudentQuarterlyUpdate.objects.create(
#             student=self.student,
#             q1_gpa=2,
#             q1_behavioral_infractions='None',
#             q2_gpa=3,
#             q2_behavioral_infractions='1 minor fight',
#             is_active=True,
#             date_created=timezone.now()
#         )

#     def test_edit_student_quarterly_update_view(self):
#         self.client.force_login(self.user)

#         response = self.client.get(reverse('Edit Quarterly Student Update', args=[self.quarterly_update.id]))

#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'NewEra/edit_student_quarterly_update.html')
#         self.assertContains(response, 'Edit Student Quarterly Update')

#     def test_edit_student_quarterly_update_view_post(self):
#         data = {
#             'q1_gpa': 2,
#             'q1_behavioral_infractions': 'Minor',
#             'q2_gpa': 2.75,
#             'q2_behavioral_infractions': '1 minor fight',
#             'is_active': True,
#             'id_student': self.student.id,
#             'date_created': '2023-07-05',
#         }
#         self.client.force_login(self.user)

#         response = self.client.post(reverse('Edit Quarterly Student Update', args=[self.quarterly_update.id]), data)

#         updated_quarterly_update = StudentQuarterlyUpdate.objects.get(id=self.quarterly_update.id)
        
#         self.assertEqual(response.status_code, 302)  # Redirect after successful form submission
#         self.assertEqual(updated_quarterly_update.q1_gpa, '2')
#         self.assertEqual(updated_quarterly_update.q1_behavioral_infractions, 'Minor')
#         self.assertEqual(updated_quarterly_update.q2_gpa, '2.75')
#         self.assertEqual(updated_quarterly_update.q2_behavioral_infractions, '1 minor fight')
#         self.assertEqual(updated_quarterly_update.is_active, True)

# class DeleteStudentQuarterlyUpdateViewTest(TestCase):
#     def setUp(self):
#         self.client = Client()
#         self.organization1 = Organization.objects.create(name='Test School 1')
#         self.organization2 = Organization.objects.create(name='Test School 2')
#         self.user = User.objects.create_user(username='testuser', password='testpassword', organization=self.organization1, is_safe_passage_coordinator=True)
#         self.user2 = User.objects.create_user(username='testuser2', password='testpassword', organization=self.organization2, is_safe_passage_coordinator=True)
#         self.student = Student.objects.create(user=self.user, first_name='John', last_name='Doe', graduation_year=2023)
#         self.quarterly_update = StudentQuarterlyUpdate.objects.create(
#             student=self.student,
#             q1_gpa=2,
#             q1_behavioral_infractions='None',
#             q2_gpa=3,
#             q2_behavioral_infractions='1 minor fight',
#             is_active=True,
#             date_created=timezone.now()
#         )

#     def test_delete_student_quarterly_update_view(self):
#         self.client.force_login(self.user)
#         response = self.client.get(reverse('Delete Quarterly Student Update', args=[self.quarterly_update.id]))
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'NewEra/delete_student_quarterly_update.html')
#         self.assertEqual(response.context['quarterly_update'], self.quarterly_update)

#     def test_delete_student_quarterly_update_view_post(self):
#         self.client.force_login(self.user)
#         response = self.client.post(reverse('Delete Quarterly Student Update', args=[self.quarterly_update.id]))
#         self.assertEqual(response.status_code, 302)
#         self.assertTrue(StudentQuarterlyUpdate.objects.filter(id=self.quarterly_update.id, is_active=False).exists())

#     def test_delete_student_quarterly_update_view_unauthenticated(self):
#         response = self.client.get(reverse('Delete Quarterly Student Update', args=[self.quarterly_update.id]), follow=True)
#         redirect_target = reverse('Login') + '?next=' + reverse('Delete Quarterly Student Update', args=[self.quarterly_update.id])
#         self.assertRedirects(response, redirect_target)
#         self.assertTemplateUsed(response, 'NewEra/login.html')

#     def test_delete_student_quarterly_update_view_different_user(self):
#         other_user = User.objects.create_user(username='otheruser', password='testpassword')
#         self.client.force_login(other_user)
#         response = self.client.get(reverse('Delete Quarterly Student Update', args=[self.quarterly_update.id]))
#         self.assertEqual(response.status_code, 404)

#     def test_delete_student_quarterly_update_view_superuser(self):
#         super_user = User.objects.create_superuser(
#             username='admin',
#             password='adminpassword',
#             email='admin@example.com'
#         )
#         self.client.force_login(super_user)
#         response = self.client.get(reverse('Delete Quarterly Student Update', args=[self.quarterly_update.id]))
#         self.assertEqual(response.status_code, 200)  # Superuser can access the view

#     def test_delete_student_quarterly_update_view_safe_passage_coordinator_different_organization(self):
#         self.client.force_login(self.user2)
#         response = self.client.get(reverse('Delete Quarterly Student Update', args=[self.quarterly_update.id]))
#         self.assertEqual(response.status_code, 404)  # Safe Passage Coordinator from a different organization cannot access the view

# endregion