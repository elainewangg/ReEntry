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

from NewEra import neighborhoods, case_labels
from django.contrib.postgres.fields import ArrayField
from multiselectfield import MultiSelectField
from django_select2.forms import Select2MultipleWidget

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

    Within this model, is_superuser represents an admin
    '''

    # Phone number is not provided in AbstractUser
    phone = models.CharField(max_length=11, blank=False, null=False)

    # Team is not provided in AbstractUser
    team = models.CharField(max_length=100, blank=True, null=False)

    # Now is organization so we need to delete the line before this, but make sure it is correct first
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, blank=True, null=True)

    # is_supervisor is a boolean that tells whether the user is a supervisor
    is_supervisor = models.BooleanField(blank=False, null=False, default=False)

    # is_reentry_coordinator field
    is_reentry_coordinator = models.BooleanField(default=False)

    # is_community_outreach_worker field
    is_community_outreach_worker = models.BooleanField(default=False)
    
    # is_service_provider field
    is_service_provider = models.BooleanField(default=False)
    
    # is_resource_coordinator field
    is_resource_coordinator = models.BooleanField(default=False)

    # Methods
    # Basic string printing
    def __str__(self):
        return self.get_username() + " (" + self.get_full_name() + ")"

    # Returns the case load of the user
    def get_case_load(self):
        return CaseLoadUser.objects.filter(user=self)

    # Returns the referrals made by a user
    def get_referrals(self):
        return Referral.objects.filter(user=self)

    # Returns user role
    def get_role(self):
        user_type_fields = {
            'is_superuser': 'admin',
            'is_supervisor': 'supervisor',
            'is_reentry_coordinator': 'reentry_coordinator',
            'is_community_outreach_worker': 'community_outreach_worker',
            'is_service_provider': 'service_provider',
            'is_resource_coordinator': 'resource_coordinator',
        }

        keys = list(user_type_fields.keys())
        # Get only the user type fields that are flagged true
        filtered_properties = [x for x in vars(self).items() if x[1] is True and x[0] in keys]

        role = []

        for property_name, property_value in filtered_properties:
            role.append(property_name)
        if len(role) > 0:
            return role[0]
        else:
            return None

    # Returns an array of the user types the user is assigned to
    def get_user_types(self):
        user_type_fields = {
            'is_supervisor': 'supervisor',
            'is_superuser': 'admin',
            'is_reentry_coordinator': 'reentry_coordinator',
            'is_community_outreach_worker': 'community_outreach_worker',
            'is_service_provider': 'service_provider',
            'is_resource_coordinator': 'resource_coordinator',
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
            'is_supervisor': 'Supervisor',
            'is_superuser': 'Admin',
            'is_reentry_coordinator': 'Reentry Coordinator',
            'is_community_outreach_worker': 'Community Outreach Worker',
            'is_service_provider': 'Service Provider',
            'is_resource_coordinator': 'Resource Coordinator',
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
        ordering = ['-is_active', 'is_superuser', 'username', 'first_name', 'last_name', 'team']


# Model for individuals on the case load
class CaseLoadUser(models.Model):
    # Attributes
    first_name = models.CharField(max_length=30, blank=False, null=False)
    last_name = models.CharField(max_length=150, blank=False, null=False)
    nickname = models.CharField(max_length=100, default='')
    email = models.EmailField(max_length=254, unique=True, error_messages={'unique': 'This email has already been registered'}, default=None)
    phone = models.CharField(max_length=11, unique=True, error_messages={'unique': 'This phone number has already been registered'}, default=None)
    neighborhood = models.CharField(max_length=150, blank=True, null=False, default='')
    case_label = MultiSelectField(choices=case_labels.CASE_LABEL_LIST)
    is_active = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, blank=True, null=True)
    age = models.CharField(max_length=3, blank=True, default='')
    zip_code = models.CharField(max_length=5, blank=True, default='', 
                                validators=[RegexValidator(regex=r'^\d{5}$', message=(u'Must be a 5-digit zipcode'))])
    education = models.CharField(max_length=150, blank=True, null=False, default='')
    is_vote_registered = models.CharField(max_length=20, blank=True, null=False, default='')
    is_employed = models.CharField(max_length=20, blank=True, null=False, default='')

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

# Model for individuals who signed up but have not confirmed yet
class TempCaseLoadUser(models.Model):
    # Attributes
    first_name = models.CharField(max_length=30, blank=False, null=False)
    last_name = models.CharField(max_length=150, blank=False, null=False)
    nickname = models.CharField(max_length=100, default='')
    email = models.EmailField(max_length=254, unique=True, error_messages={'unique': 'This email has already been registered'}, default=None)
    phone = models.CharField(max_length=11, unique=True, error_messages={'unique': 'This phone number has already been registered'}, default=None)
    neighborhood = models.CharField(max_length=150, blank=True, null=False, default='')
    case_label = MultiSelectField(choices=case_labels.CASE_LABEL_LIST)
    is_active = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, blank=True, null=True)
    age = models.CharField(max_length=3, blank=True, default='')
    zip_code = models.CharField(max_length=5, blank=True, default='', 
                                validators=[RegexValidator(regex=r'^\d{5}$', message=(u'Must be a 5-digit zipcode'))])
    education = models.CharField(max_length=150, blank=True, null=False, default='')
    is_vote_registered = models.CharField(max_length=20, blank=True, null=False, default='')
    is_employed = models.CharField(max_length=20, blank=True, null=False, default='')

    # Methods
    # Basic string printing
    def __str__(self):
        return self.get_full_name() + ", phone number " + self.phone

    # Prints the case load user's full name, prettified
    def get_full_name(self):
        return self.first_name + " " + self.last_name

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


# Model representing a tag
class Tag(models.Model):

    # Attributes
    name = models.CharField(max_length=30)
    tag_type = models.CharField(max_length=150, blank=False, null=False, default='')
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
        ("attachment", "File Attachment (PDF, Image, Video)")
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
        ('Case Management', 'Case Management'),
        ('Community Engagement', 'Community Engagement'),
        ('Program Recruitment', 'Program Recruitment'),
        ('Service Provider', 'Service Provider'),
        ('Program Enrollment', 'Program Enrollment'),
        ('Community Event', 'Community Event'),
        ('Tabling Event', 'Tabling Event'),
        ('Community Outreach', 'Community Outreach'),
        ('Training', 'Training'),
        ('Program Participant', 'Program Participant'),
        ('Other', 'Other')
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