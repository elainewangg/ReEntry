from datetime import timedelta
from django.core.validators import RegexValidator
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core import mail
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from encrypted_model_fields.fields import (EncryptedCharField,
                                           EncryptedIntegerField,
                                           EncryptedTextField)
from twilio.rest import Client

from NewEra import neighborhoods

'''
COMMON NOTES:
- First names have a 30-digit maximum to match Django's maximum for first names
- Last names have a 150-digit maximum to match Django's maximum for last names
- Emails have a 254-digit maximum to reflect the IETF standard (https://stackoverflow.com/questions/386294/what-is-the-maximum-length-of-a-valid-email-address)
- Phone numbers have an 11-digit maximum to match a 1 and 10 subsequent digits at maximum (methods check for a minimum of 10 digits)
'''


# Model for Organization on the case load
class Organization(models.Model):
    # Attributes
    name = models.CharField(max_length=30, blank=False, null=False)
    is_active = models.BooleanField(default=True)

    # Methods
    # Basic string printing
    def __str__(self):
        return self.name

    # Sets ordering parameters and their ordering priority
    class Meta:
        ordering = ['is_active', 'name']


# User model; extends Django's default AbstractUser
class User(AbstractUser):
    '''
    Fields taken care of by base User class in Django:
    - username
    - password
    - email
    - first_name
    - last_name

    Within this model, is_staff represents an SOW; is_superuser represents an admin
    '''

    # Phone number is not provided in AbstractUser
    phone = models.CharField(max_length=11, blank=False, null=False)

    # Team is not provided in AbstractUser
    team = models.CharField(max_length=100, blank=True, null=False)

    # Now is organization so we need to delete the line before this, but make sure it is correct first
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, blank=True, null=True)

    # is_supervisor is a boolean that tells whether the user is a supervisor
    is_supervisor = models.BooleanField(blank=False, null=False, default=False)

    # is_safe_passage_coordinator field
    is_safe_passage_coordinator = models.BooleanField(default=False)

    # is_safe_passage_coordinator_supervisor field
    is_safe_passage_coordinator_supervisor = models.BooleanField(default=False)

    # Methods
    # Basic string printing
    def __str__(self):
        return self.get_username() + " (" + self.get_full_name() + ")"

    # Returns if the user is an active staff member (an SOW or an admin)
    def is_active_staff(self):
        return self.is_active and self.is_staff

    # Returns the case load of the user
    def get_case_load(self):
        return CaseLoadUser.objects.filter(user=self)

    # Returns the referrals made by a user
    def get_referrals(self):
        return Referral.objects.filter(user=self)

    # Returns the student referrals made by a user
    # def get_student_referrals(self):
    #     return StudentReferral.objects.filter(user=self)

    # Returns an array of the user types the user is assigned to
    def get_user_types(self):
        user_type_fields = {
            'is_safe_passage_coordinator': 'safe_passage_coordinator',
            'is_safe_passage_coordinator_supervisor': 'safe_passage_coordinator_supervisor',
            'is_supervisor': 'supervisor',
            'is_superuser': 'admin',
            'is_staff': 'sow'
        }
        keys = list(user_type_fields.keys())
        # Get only the user type fields that are flagged true
        filtered_properties = [x for x in vars(self).items() if x[1] is True and x[0] in keys]

        types = []

        for property_name, property_value in filtered_properties:
            types.append(user_type_fields[property_name])

        return types

    def get_user_type_buttons(self):
        user_type_fields = {
            'is_safe_passage_coordinator': 'SPC (Safe Passage Coordinator)',
            'is_safe_passage_coordinator_supervisor': 'SPC Supervisor',
            'is_supervisor': 'Supervisor',
            'is_superuser': 'Admin',
            'is_staff': 'SOW'
        }
        keys = list(user_type_fields.keys())
        # Get only the user type fields that are flagged true
        filtered_properties = [x for x in vars(self).items() if x[1] is True and x[0] in keys]

        types = {}

        for property_name, property_value in filtered_properties:
            types[property_name] = user_type_fields[property_name]

        return types

    def has_more_than_one_role(self):
        roles = self.get_user_types()
        return len(roles) > 1

    # Sets ordering parameters and their ordering priority
    class Meta:
        ordering = ['-is_active', 'is_superuser', 'is_staff', 'username', 'first_name', 'last_name', 'team']


# Model for individuals on the case load
class CaseLoadUser(models.Model):
    # Attributes
    first_name = models.CharField(max_length=30, blank=False, null=False)
    last_name = models.CharField(max_length=150, blank=False, null=False)
    nickname = models.CharField(max_length=100, default='')
    email = models.EmailField(max_length=254)
    phone = models.CharField(max_length=11)
    neighborhood = models.CharField(max_length=150, blank=True, null=False, default='')
    case_label = models.CharField(max_length=150, blank=False, null=False, default='')
    is_active = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, blank=True, null=True)
    age = models.CharField(max_length=3, blank=True, default='')
    zip_code = models.CharField(max_length=5, blank=True, default='', 
                                validators=[RegexValidator(regex=r'^\d{5}$', message=(u'Must be a 5-digit zipcode'))])
    education = models.CharField(max_length=150, blank=True, null=False, default='')
    is_vote_registered = models.CharField(max_length=20, blank=True, null=False, default='')

    # Methods
    # Basic string printing
    def __str__(self):
        return self.get_full_name() + ", phone number " + self.phone

    # Prints the case load user's full name, prettified
    def get_full_name(self):
        return self.first_name + " " + self.last_name

    # Grabs all referrals made containing a case load user
    def get_referrals(self):
        return Referral.objects.filter(caseUser=self)

    # Sets ordering parameters and their ordering priority
    class Meta:
        ordering = ['user', 'first_name', 'last_name']


# Model for an entire referral
class Referral(models.Model):
    # Attributes
    email = models.EmailField(max_length=254)
    phone = models.CharField(max_length=11, blank=False, null=False)
    referral_date = models.DateTimeField(default=timezone.now)
    date_accessed = models.DateTimeField(blank=True, null=True)
    notes = models.CharField(max_length=1000)

    # Foreign attributes
    user = models.ForeignKey(User, on_delete=models.PROTECT, blank=True, null=True)
    caseUser = models.ForeignKey(CaseLoadUser, on_delete=models.PROTECT, blank=True, null=True)

    # Methods
    # Sends an email to the referral recipient containing the referred resources
    def sendEmail(self, referralTimeStamp, clientName):

        # Do not send an email if the field is empty
        if (not self.email or self.email == '') and (
                not self.caseUser or not self.caseUser.email or self.caseUser.email == ''):
            return

        # Set the message body containing resource details
        strArgs = [r.name + ',  ' for r in self.resource_set.all()]
        strArgs.append('and other resources.')
        resources = [r for r in self.resource_set.all()]

        # Create username string
        userName = self.user.get_full_name()

        # Create email contents
        subject = 'NewERA412 Referral from {}: {}'.format(userName, ''.join(strArgs))
        html_message = render_to_string('NewEra/referral_mailer.html',
                                        {'resources': resources, 'userName': userName, 'notes': self.notes,
                                         'timeStamp': referralTimeStamp, 'clientName': clientName})
        plain_message = strip_tags(html_message)
        from_email = settings.EMAIL_HOST_USER

        # Set recipient
        to = self.email
        if to == None or to == '':
            to = self.caseUser.email

        # Send the email
        mail.send_mail(subject, plain_message, from_email, [to], html_message=html_message, fail_silently=True)

    # Sends a text message to the referral recipient containing the referred resources
    def sendSMS(self, referralTimeStamp, clientName):
        # Do not send a text if the field is empty
        if (not self.phone or self.phone == '') and (
                not self.caseUser or not self.caseUser.phone or self.caseUser.phone == ''):
            return

        # Create username string
        userName = self.user.get_full_name()

        # Set recipient
        to = self.phone
        if to == None or to == '':
            to = self.caseUser.phone

        # Set the message intro string based on whether the referral is to someone on the case load or out of the system
        if (clientName):
            messageIntro = '\nHi {}, \n{}\n--{}\n\n---------'.format(clientName, self.notes, userName)
        else:
            messageIntro = '\n{}\n--{}\n\n---------'.format(self.notes, userName)

        # Create the query string and the message body
        queryString = '?key=' + referralTimeStamp
        queryString = queryString.replace(' ', '%20')  # Make SMS links accessible
        links = ['\n' + r.name + ': http://newera412.com/resources/' + str(r.id) + queryString + '\n' for r in
                 self.resource_set.all()]
        messageBody = ''.join(links) + '---------\nSee us online for more: www.newera412.com'

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(from_=settings.TWILIO_PHONE_NUMBER, to=to, body=messageIntro + messageBody)

    # Basic string printing
    def __str__(self):
        # name = (first_name == None || last_name == None) ? self.get_full_name() : "(unknown)"
        return "Referral sent to " + self.phone + " by " + self.user.get_full_name() + " on " + self.referral_date.strftime(
            "%m-%d-%Y")

    # Sets ordering parameters and their ordering priority
    class Meta:
        ordering = ['referral_date', 'user', 'caseUser']


# class Student(models.Model):
#     id = models.AutoField(primary_key=True)
#     user = models.ForeignKey(User, on_delete=models.PROTECT)
#     first_name = EncryptedCharField(max_length=255, blank=False, null=False)
#     last_name = EncryptedCharField(max_length=255, blank=False, null=False)
#     email = EncryptedCharField(max_length=255)
#     phone = EncryptedCharField(max_length=255)
#     parent_first_name = EncryptedCharField(max_length=255)
#     parent_last_name = EncryptedCharField(max_length=255)
#     parent_email = EncryptedCharField(max_length=255)
#     parent_phone = EncryptedCharField(max_length=255)
#     is_active = models.BooleanField(default=True)
#     date_created = models.DateTimeField(default=timezone.now)
#     graduation_year = EncryptedIntegerField()

#     # Prints the student's full name, prettified
#     def get_full_name(self):
#         return f"{self.first_name} {self.last_name}"

#     # Prints the student's full name, prettified
#     def get_parent_full_name(self):
#         return f"{self.parent_first_name} {self.parent_last_name}"


# class StudentReferral(models.Model):
#     email = EncryptedCharField(max_length=254)
#     phone = EncryptedCharField(max_length=11, blank=False, null=False)
#     referral_date = models.DateTimeField(default=timezone.now)
#     date_accessed = models.DateTimeField(blank=True, null=True)
#     notes = EncryptedCharField(max_length=1000)
#     quarter = EncryptedCharField(max_length=10)
#     user = models.ForeignKey(User, on_delete=models.PROTECT, blank=True, null=True)
#     student = models.ForeignKey(Student, on_delete=models.PROTECT, blank=True, null=True)

#     def sendEmail(self, referralTimeStamp, clientName):
#         if (not self.email or self.email == '') and (
#                 not self.student or not self.student.email or self.student.email == ''):
#             return

#         strArgs = [r.name + ',  ' for r in self.resource_set.all()]
#         strArgs.append('and other resources.')
#         resources = [r for r in self.resource_set.all()]

#         userName = self.user.get_full_name()

#         subject = 'NewERA412 Referral from {}: {}'.format(userName, ''.join(strArgs))
#         html_message = render_to_string('NewEra/referral_mailer.html',
#                                         {'resources': resources, 'userName': userName, 'notes': self.notes,
#                                          'timeStamp': referralTimeStamp, 'clientName': clientName})
#         plain_message = strip_tags(html_message)
#         from_email = settings.EMAIL_HOST_USER

#         to = self.email
#         if to == None or to == '':
#             to = self.caseUser.email

#         mail.send_mail(subject, plain_message, from_email, [to], html_message=html_message, fail_silently=True)

#     def sendSMS(self, referralTimeStamp, clientName):
#         # Do not send a text if the field is empty
#         if (not self.phone or self.phone == '') and (
#                 not self.student or not self.student.phone or self.student.phone == ''):
#             return

#         # Create username string
#         userName = self.user.get_full_name()

#         # Set recipient
#         to = self.phone
#         if to == None or to == '':
#             to = self.caseUser.phone

#         # Set the message intro string based on whether the referral is to someone on the case load or out of the system
#         if (clientName):
#             messageIntro = '\nHi {}, \n{}\n--{}\n\n---------'.format(clientName, self.notes, userName)
#         else:
#             messageIntro = '\n{}\n--{}\n\n---------'.format(self.notes, userName)

#         # Create the query string and the message body
#         queryString = '?key=' + referralTimeStamp
#         queryString = queryString.replace(' ', '%20')  # Make SMS links accessible
#         links = ['\n' + r.name + ': http://newera412.com/resources/' + str(r.id) + queryString + '\n' for r in
#                  self.resource_set.all()]
#         messageBody = ''.join(links) + '---------\nSee us online for more: www.newera412.com'

#         client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
#         client.messages.create(from_=settings.TWILIO_PHONE_NUMBER, to=to, body=messageIntro + messageBody)

#     # Basic string printing
#     def __str__(self):
#         # name = (first_name == None || last_name == None) ? self.get_full_name() : "(unknown)"
#         return "Referral sent to " + self.phone + " by " + self.user.get_full_name() + " on " + self.referral_date.strftime(
#             "%m-%d-%Y")

#     # Sets ordering parameters and their ordering priority
#     class Meta:
#         ordering = ['referral_date', 'user', 'student']


# Model representing a tag
class Tag(models.Model):
    # Attributes
    name = models.CharField(max_length=30)

    # Methods
    # Basic string printing
    def __str__(self):
        return self.name

    # Sets ordering parameters and their ordering priority
    class Meta:
        ordering = ['name']


# Model representing one resource as it exists in isolation
class Resource(models.Model):
    RESOURCE_TYPES_LIST = [
        ("organization", "Organization"),
        ("video", "Video Link (YouTube only)"),
        ("attachment", "File Attachment (PDF, Image, Video)"),
        ("embed", "Embedded Content (iframe)"),
        ("link", "Link to External Website")
    ]

    # Attributes
    name = models.CharField(max_length=100, blank=False, null=False)
    description = models.CharField(max_length=1000, blank=True, null=True)
    hours = models.CharField(max_length=1000, default='')
    # https://stackoverflow.com/questions/386294/what-is-the-maximum-length-of-a-valid-email-address
    email = models.EmailField(max_length=254)
    # We can change this later if needed
    phone = models.CharField(max_length=11)
    extension = models.CharField(max_length=11, blank=True, null=True)
    street = models.CharField(max_length=100)
    street_secondary = models.CharField(max_length=100, default='')
    city = models.CharField(max_length=100, default="Pittsburgh")
    # This should account for 5-digit and 10-digit zip codes
    zip_code = models.CharField(max_length=10)
    # Refers to two digits
    state = models.CharField(max_length=2, default="PA")

    # thumbnail/header image
    image = models.FileField(blank=True)
    content_type = models.CharField(max_length=50, blank=True)

    url = models.URLField()
    clicks = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    contact_name = models.CharField(max_length=181)
    contact_position = models.CharField(max_length=100)
    # Assuming fax number is like a phone number (limited to 10 digits)
    fax_number = models.CharField(max_length=10)
    # This can be the same as or different from the organizational email
    contact_email = models.EmailField(max_length=254)

    # Indicate the type of this resource
    resource_type = models.CharField(max_length=150, blank=False, null=False, default=RESOURCE_TYPES_LIST[0][0])
    event_datetime = models.DateTimeField(blank=True, null=True)
    attachment = models.FileField(blank=True, null=True)
    attachment_content_type = models.CharField(max_length=50, blank=True)
    embedded_content = models.CharField(max_length=1000, blank=True, null=True)

    # Many-to-many foreign keys
    # Blank section added for the admin dashboard management (otherwise resources can't be added)
    tags = models.ManyToManyField(Tag, blank=True)
    referrals = models.ManyToManyField(Referral, blank=True)
    # student_referrals = models.ManyToManyField(StudentReferral, blank=True)

    # Methods
    # Basic string printing
    def __str__(self):
        return self.name

    # Sets ordering parameters and their ordering priority
    class Meta:
        ordering = ['name']


class Note(models.Model):
    ACTIVITY_CHOICES = [
        ('Group Meeting', 'Group Meeting'),
        ('Individual Meeting', 'Individual Meeting'),
        ('Job Search', 'Job Search'),
        ('Case Notes', 'Case Notes')
    ]
    notes = models.CharField(max_length=1000)
    date = models.DateField(default=timezone.now)
    case = models.ForeignKey(CaseLoadUser, default=None, on_delete=models.PROTECT)
    activity_type = models.CharField(choices=ACTIVITY_CHOICES, max_length=150)
    hours = models.FloatField()

    def __str__(self):
        return 'text=' + str(self.text)


class MeetingTracker(models.Model):
    MEETING_CHOICES = [
        ('G.V.I. Citywide Outreach Team Meeting', 'G.V.I. Citywide Outreach Team Meeting'),
        ('Community Outreach/ Community Meeting', 'Community Outreach/ Community Meeting'),
        ('Violence Prevention Community Event', 'Violence Prevention Community Event'),
        ('Social Media Monitoring', 'Social Media Monitoring'),
        ('School Safety work/ Safe passage', 'School Safety work/ Safe passage'),
        ('Case management', 'Case management'),
        ('Reentry Services', 'Reentry Services'),
        ('Intervention Activities', 'Intervention Activities'),
        ('Prevention Activities', 'Prevention Activities'),
        ('Engaging the target population', 'Engaging the target population'),
        ('Supervision/ Staff meeting', 'Supervision/ Staff meeting'),
        ('Violence Prevention Activities in Zone 1', 'Violence Prevention Activities in Zone 1'),
        ('Violence Prevention Activities in Zone 2', 'Violence Prevention Activities in Zone 2'),
        ('Violence Prevention Activities in Zone 3', 'Violence Prevention Activities in Zone 3'),
        ('Violence Prevention Activities in Zone 4', 'Violence Prevention Activities in Zone 4'),
        ('Violence Prevention Activities in Zone 5', 'Violence Prevention Activities in Zone 5'),
        ('Violence Prevention Activities in Zone 6', 'Violence Prevention Activities in Zone 6'),
        ('Violence Prevention Activities in Allegheny County (outside of city limits)',
         'Violence Prevention Activities in Allegheny County (outside of city limits)'),
        ('ACAR/PARC', 'Allegheny County Anchored Reentry/Pennsylvania Reentry Council Reentry Resources'),
        ('Violence Prevention in Homewood', 'Violence Prevention in Homewood'),
        ('Violence Prevention in Northside', 'Violence Prevention in Northside'),
        ('Incident Report', 'Incident Report'),
        ('REACH Meeting', 'REACH Meeting'),
        ('Case Management Providing Reentry Services', 'Case Management Providing Reentry Services'),
        ('Mentoring', 'Mentoring'),
        ('Community Event', 'Community Event'),
        ('Community Meeting', 'Community Meeting'),
        ('Other', 'Other'),
    ]

    NEIGHBORHOOD_CHOICES = neighborhoods.NEIGHBORHOOD_LIST

    user = models.ForeignKey(User, default=None, on_delete=models.PROTECT)
    with_who = models.CharField(choices=MEETING_CHOICES, max_length=150)
    purpose = models.CharField(max_length=150)
    neighborhood = models.CharField(choices=NEIGHBORHOOD_CHOICES, max_length=150)
    duration = models.FloatField(default=0)
    date = models.DateField(default=timezone.now)
    time = models.TimeField(default=timezone.now)
    notes = models.CharField(max_length=1000)

    def __str__(self):
        return 'user=' + self.user.first_name + ' ' + self.user.last_name


# class RiskAssessment(models.Model):
#     RISK_CHOICES = [
#         ('4', 'Red, Violence has occurred and imminent threat remains'),
#         ('3', 'Orange, Violence has occurred that is likely to lead to red'),
#         ('2', 'Yellow, Tensions exist that may lead to violence, but no imminent threat is known'),
#         ('1', 'Green, No violence or imminent threats has occurred'),
#         ('0', 'Other'),
#     ]

#     ACTION_CHOICES = [
#         ('Conflict Mediation', 'Conflict Mediation'),
#         ('Increased Outreach', 'Increased Outreach'),
#         ('Law Enforcement Presence', 'Law Enforcement Presence'),
#         ('G.V.I. Custom Notification', 'G.V.I. Custom Notification'),
#         ('Referral for Services', 'Referral for Services'),
#         ('Community Meeting / Town Hall Form', 'Community Meeting / Town Hall Form'),
#         ('Other', 'Other'),
#     ]

#     NEIGHBORHOOD_CHOICES = neighborhoods.NEIGHBORHOOD_LIST

#     user = models.ForeignKey(User, default=None, on_delete=models.PROTECT)
#     risk_level = models.CharField(choices=RISK_CHOICES, max_length=150)
#     actions = models.CharField(choices=ACTION_CHOICES, max_length=150)
#     neighborhood = models.CharField(choices=NEIGHBORHOOD_CHOICES, max_length=150)
#     notes = models.CharField(max_length=1000)
#     date = models.DateField(default=timezone.now)
#     time = models.TimeField(default=timezone.now)

#     def send_email(self):
#         for choice in self.RISK_CHOICES:
#             if choice[0] == self.risk_level:
#                 risk_level_desc = choice[1]

#         risk = self.risk_level + ' - ' + risk_level_desc

#         # Create email contents
#         subject = 'Action Required - New high-level threat created in NewEra 412'
#         html_message = render_to_string('NewEra/risk_assessment_mailer.html',
#                                         {'threat_level': risk,
#                                          'reported_by': self.user,
#                                          'description': self.notes, 'recommended_action': self.actions,
#                                          'neighborhood': self.neighborhood})
#         from_email = settings.EMAIL_HOST_USER
#         to = settings.RISK_ASSESSMENT_EMAIL_TO.split(',')
#         cc = settings.RISK_ASSESSMENT_EMAIL_CC.split(',')

#         msg = EmailMessage(subject, html_message, from_email, to, cc=cc)
#         msg.content_subtype = "html"
#         msg.send(fail_silently=True)

#     def __str__(self):
#         return 'user=' + self.user.first_name + ' ' + self.user.last_name


# class Biweekly(models.Model):
#     INTERVENTION_CHOICES = [
#         ('Group Related', 'Group Related'),
#         ('Drug Related', 'Drug Related'),
#         ('Domestic/Family Related', 'Domestic/Family Related'),
#         ('Shootings/Stabbings/Homocides', 'Shootings/Stabbings/Homocides'),
#         ('Civil Disturbance Incidents', 'Civil Disturbance Incidents'),
#     ]

#     user = models.ForeignKey(User, default=None, on_delete=models.PROTECT)
#     pay_start = models.DateField(default=timezone.now() - timedelta(days=14))
#     pay_end = models.DateField(default=timezone.now)
#     work_hours = models.IntegerField(default=0)
#     special_hours = models.IntegerField(default=0)
#     num_special_events = models.IntegerField(default=0)
#     meeting_hours = models.IntegerField(default=0)
#     num_meetings = models.IntegerField(default=0)
#     other = models.IntegerField(default=0)
#     num_served = models.IntegerField(default=0)
#     location = models.CharField(max_length=100)
#     intervention = models.CharField(choices=INTERVENTION_CHOICES, max_length=150)
#     num_responses = models.IntegerField(default=0)
#     num_events = models.IntegerField(default=0)
#     num_visits = models.IntegerField(default=0)
#     num_mediations = models.IntegerField(default=0)
#     first_summary = models.CharField(max_length=1000)
#     second_summary = models.CharField(max_length=1000)
#     date = models.DateField(default=timezone.now)

#     def __str__(self):
#         return 'user=' + self.user.first_name + ' ' + self.user.last_name


# class StudentWeeklyUpdate(models.Model):
#     id = models.AutoField(primary_key=True)
#     student = models.ForeignKey(Student, on_delete=models.PROTECT)
#     weekly_absences = EncryptedIntegerField()
#     extra_curricular = EncryptedTextField(max_length=1000)
#     special_needs = EncryptedTextField(max_length=1000)
#     goals = EncryptedTextField(max_length=1000, null=True)
#     notes = EncryptedTextField(max_length=1000)
#     is_active = models.BooleanField(default=True)
#     date_created = models.DateTimeField(default=timezone.now)


# class StudentWeeklyUpdateUpload(models.Model):
#     student_weekly_update = models.ForeignKey(StudentWeeklyUpdate, on_delete=models.PROTECT,
#                                               related_name='weekly_update_uploads')
#     file = models.FileField(upload_to='student_weekly_updates/')


# class StudentQuarterlyUpdate(models.Model):
#     id = models.AutoField(primary_key=True)
#     student = models.OneToOneField(Student, on_delete=models.PROTECT)
#     q1_gpa = EncryptedCharField(max_length=5, null=True)
#     q1_behavioral_infractions = EncryptedCharField(max_length=1000, null=True)
#     q2_gpa = EncryptedCharField(max_length=5, null=True)
#     q2_behavioral_infractions = EncryptedCharField(max_length=1000, null=True)
#     q3_gpa = EncryptedCharField(max_length=5, null=True)
#     q3_behavioral_infractions = EncryptedCharField(max_length=1000, null=True)
#     q4_gpa = EncryptedCharField(max_length=5, null=True)
#     q4_behavioral_infractions = EncryptedCharField(max_length=1000, null=True)
#     is_active = models.BooleanField(default=True)
#     date_created = models.DateTimeField(default=timezone.now)
