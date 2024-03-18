from datetime import datetime

import django_filters
from bootstrap_datepicker_plus import (DatePickerInput, DateTimePickerInput,
                                       TimePickerInput)
from django import forms
from django.contrib.auth import authenticate
from django.core.files.uploadedfile import UploadedFile
from django.forms.widgets import CheckboxSelectMultiple

from NewEra import case_labels, neighborhoods, educations, registrations
# from NewEra.models import (Biweekly, CaseLoadUser, MeetingTracker, Note,
#                            Organization, Referral, Resource, RiskAssessment,
#                            StudentQuarterlyUpdate, StudentReferral,
#                            StudentWeeklyUpdate, StudentWeeklyUpdateUpload, Tag,
#                            User)
from NewEra.models import (CaseLoadUser, MeetingTracker, Note,
                           Organization, Referral, Resource, Tag,
                           User)

INPUT_ATTRIBUTES = {
	'class' : 'form-control organization', 'style': 'width: 300px; height: 40px; margin-bottom: 20px;'	}
COMMON_ATTRIBUTES = {'class' : 'form-control common'}
EVENT_ATTRIBUTES = {'class' : 'form-control common', 'placeholder': 'Event or Deadline'}
ATTACHMENT_ATTRIBUTES = {'class' : 'form-control attachment'}
EMBEDDED_ATTRIBUTES = {'class' : 'form-control embed', 'placeholder': 'Paste <iframe>...</iframe> code here'}
HIDDEN_ATTRIBUTES = {'class' : 'form-control hidden'}

TEXTAREA_ATTRIBUTES = { 'class': 'form-control', 'style': 'height: 200px; overflow-y: scroll;', 'cols': 40, 'rows': 40}

MAX_IMAGE_UPLOAD_SIZE = 2500000 #2.5mb
MAX_ATTACHMENT_UPLOAD_SIZE = 20000000 #20mb

USER_TYPE_CHOICES = [
	('sow', 'SOW'),
	('safe_passage_coordinator', 'Safe Passage Coordinator'),
	('supervisor', 'Supervisor'),
	('safe_passage_coordinator_supervisor', 'Safe Passage Coordinator Supervisor'),
	('admin', 'Admin')
]

# Model Forms

'''
COMMON NOTES:
- First names have a 30-digit maximum to match Django's maximum for first names
- Last names have a 150-digit maximum to match Django's maximum for last names
- Emails have a 254-digit maximum to reflect the IETF standard (https://stackoverflow.com/questions/386294/what-is-the-maximum-length-of-a-valid-email-address)
- Phone numbers have an 11-digit maximum to match a 1 and 10 subsequent digits at maximum (methods check for a minimum of 10 digits)
'''
# Form used to create and edit a CaseLoadUser
class CaseLoadUserForm(forms.ModelForm):
	# Set up attributes
	first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	phone = forms.CharField(max_length=11, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES), required=False)
	email = forms.EmailField(max_length=254, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES), required=False)
	nickname = forms.CharField(max_length=100, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES), required=False)
	neighborhood = forms.CharField(widget=forms.Select(attrs=INPUT_ATTRIBUTES, choices=neighborhoods.NEIGHBORHOOD_LIST))
	case_label = forms.CharField(widget=forms.Select(attrs=INPUT_ATTRIBUTES, choices=case_labels.CASE_LABEL_LIST))
	age = forms.CharField(max_length=3, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES), required=False)
	zip_code = forms.CharField(max_length=5, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES), required=False)
	education = forms.CharField(widget=forms.Select(attrs=INPUT_ATTRIBUTES, choices=educations.EDUCATION_LIST), required=False)
	is_vote_registered = forms.CharField(widget=forms.Select(attrs=INPUT_ATTRIBUTES, choices=registrations.REGISTRATION_LIST), required=False)

	# Define the model and fields to include/exclude
	class Meta:
		model = CaseLoadUser
		fields = ['first_name', 'last_name', 'nickname', 'email', 'phone', 'neighborhood', 'case_label', 'is_active', 'user', 'age', 'zip_code', 'education', 'is_vote_registered']
		exclude = (
			'user',
		)

	def __init__(self, *args, **kwargs):
		super(CaseLoadUserForm, self).__init__(*args, **kwargs)
		self.fields['is_vote_registered'].label = "Voter Registration"
		# is_active field not defined above so it can be hidden on creation; if the case load user exists, is_active
		self.fields['is_active'].widget.attrs=INPUT_ATTRIBUTES

		# Hide the is_active field if the model is being created
		# https://stackoverflow.com/questions/55994307/exclude-fields-for-django-model-only-on-creation
		if not self.instance or self.instance.pk is None:
			for name, field in self.fields.items():
				if name in ['is_active', ]:
					field.widget = forms.HiddenInput()

	# Validate the phone number entered
	def clean_phone(self):
		# Obtain only the digits entered from the phone
		phone = self.cleaned_data['phone']
		cleaned_phone = ''.join(digit for digit in phone if digit.isdigit())

		# Validate that the phone number is either the standard 10 digits or it is 11 starting with a 1
		if phone and (len(cleaned_phone) != 10 and not (len(cleaned_phone) == 11 and cleaned_phone[0] == '1')):
			raise forms.ValidationError('The phone number must be either exactly 10 digits or a 1 followed by 10 digits.')

		return cleaned_phone

	# Ensure that for a case load entry, the SOW has inputted values for either the phone or the email, or both
	def clean(self):
		# cleaned_data is necessary to get the fields after they've already been cleaned
		cleaned_data = super().clean()
		phone = cleaned_data.get('phone')
		email = cleaned_data.get('email')

		# Raise an error if neither field is valid
		if not (phone or email):
			raise forms.ValidationError('You must input either a phone number or an email address for this user.')

		return cleaned_data

# Form to create new notes
class CreateNoteForm(forms.ModelForm):
    notes = forms.CharField(max_length=1000, required=True, widget=forms.Textarea(attrs=INPUT_ATTRIBUTES))
    date = forms.DateField(widget=DatePickerInput())
    class Meta:
        model = Note
        fields = ['notes', 'date', 'activity_type', 'hours']

# Form to edit organizations
class EditOrganizationForm(forms.ModelForm):
	name = forms.CharField(max_length=30, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	is_active = forms.BooleanField(required=False)

	class Meta:
		model = Organization
		fields = ('name','is_active')

# Form to edit users 
class EditUserForm(forms.ModelForm):
	# Set up attributes
	email = forms.EmailField(max_length=254, widget=forms.EmailInput(attrs=INPUT_ATTRIBUTES))
	first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	phone = forms.CharField(max_length=11, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	organization = forms.ModelChoiceField(queryset=Organization.objects.all())
	is_active = forms.BooleanField(required=False)
	user_type = forms.MultipleChoiceField(choices=USER_TYPE_CHOICES,
										  label='User Type',
										  widget=forms.CheckboxSelectMultiple(attrs={'class': 'list-unstyled'}),
										  )

	# Define the model and fields to include/exclude
	class Meta:
		model = User
		fields = ('email', 'first_name', 'last_name', 'phone', 'organization', 'is_active', 'user_type')
		exclude = (
			# A user's username cannot be changed
			'username',
			# A user's password and confirmation cannot be changed except through the change password link
			'password',
			'confirm_password'
		)

	# Validate the phone number entered
	def clean_phone(self):
		# Obtain only the digits entered from the phone
		phone = self.cleaned_data['phone']
		cleaned_phone = ''.join(digit for digit in phone if digit.isdigit())

		# Validate that the phone number is either the standard 10 digits or it is 11 starting with a 1
		if phone and (len(cleaned_phone) != 10 and not (len(cleaned_phone) == 11 and cleaned_phone[0] == '1')):
			raise forms.ValidationError('The phone number must be either exactly 10 digits or a 1 followed by 10 digits.')

		return cleaned_phone

	# Validate selected roles
	def clean_roles(self):
		roles = self.cleaned_data.get('user_type')

		if len(roles) == 0:
			raise forms.ValidationError('At least one role must be selected.')

# Form to edit the current, logged in user
class EditSelfUserForm(forms.ModelForm):
	# Set up attributes
	email = forms.EmailField(max_length=254, widget=forms.EmailInput(attrs=INPUT_ATTRIBUTES))
	first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	last_name  = forms.CharField(max_length=150, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	phone = forms.CharField(max_length=11, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	organization = forms.ModelChoiceField(queryset=Organization.objects.all())

	# Define the model and fields to include/exclude
	class Meta:
		model = User
		fields = ('email', 'first_name', 'last_name', 'phone', 'organization')
		exclude = (
			# A user's username cannot be changed
			'username',
			# A user's password and confirmation cannot be changed except through the change password link
			'password',
			'confirm_password',
			# A user cannot make themselves inactive
			'is_active'
		)

	# Validate the phone number entered
	def clean_phone(self):
		# Obtain only the digits entered from the phone
		phone = self.cleaned_data['phone']
		cleaned_phone = ''.join(digit for digit in phone if digit.isdigit())

		# Validate that the phone number is either the standard 10 digits or it is 11 starting with a 1
		if phone and (len(cleaned_phone) != 10 and not (len(cleaned_phone) == 11 and cleaned_phone[0] == '1')):
			raise forms.ValidationError('The phone number must be either exactly 10 digits or a 1 followed by 10 digits.')

		return cleaned_phone

# Form to create and edit resources
class CreateResourceForm(forms.ModelForm):
	# Set up attributes
	# Indicate the type of this resource to change the display mode
	resource_type = forms.CharField(widget=forms.Select(choices=Resource.RESOURCE_TYPES_LIST, attrs=COMMON_ATTRIBUTES))
	is_active = forms.BooleanField(required=False, label="Active Resource")

	# Common Fields
	name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs=COMMON_ATTRIBUTES))
	description = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs=COMMON_ATTRIBUTES))
	image = forms.FileField(label=('Thumbnail'),required=False, widget=forms.ClearableFileInput(attrs=COMMON_ATTRIBUTES))
	url = forms.URLField(label=('URL Link'), required=False, widget=forms.TextInput(attrs=COMMON_ATTRIBUTES))

	# Any type can have an event date/time attached
	event_datetime = forms.DateTimeField(label=('Date & Time'), required=False, widget=DateTimePickerInput(attrs=EVENT_ATTRIBUTES))

	# used to introduce a blank space between sections
	blank = forms.CharField(required=False, widget=forms.TextInput(attrs=HIDDEN_ATTRIBUTES))

	# Organization
	hours = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs=INPUT_ATTRIBUTES))
	email = forms.EmailField(max_length=254, required=False, widget=forms.EmailInput(attrs=INPUT_ATTRIBUTES))
	phone = forms.CharField(max_length=11, required=False, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	extension = forms.CharField(max_length=11, required=False, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))

	street = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	street_secondary = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	city = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	zip_code = forms.CharField(max_length=10, required=False, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	state = forms.CharField(max_length=2, required=False, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))

	contact_name = forms.CharField(max_length=181, required=False, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	contact_position = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	# Assuming fax number is like a phone number
	fax_number = forms.CharField(max_length=11, required=False, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	# This may or may not be different from the organizational email
	contact_email = forms.EmailField(max_length=254, required=False, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))

	# Video Type - will use URL field

	# File Attachment Type
	attachment = forms.FileField(label=('Attachment'),required=False, widget=forms.ClearableFileInput(attrs=ATTACHMENT_ATTRIBUTES))

	# Embedded Content
	embedded_content = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs=EMBEDDED_ATTRIBUTES))

	# Link to External Website - will use URL field


	# Define the model and fields to include/exclude
	class Meta:
		model = Resource
		fields = ('resource_type', 'is_active',
		'name', 'description',
		'image', 'url',
		'event_datetime',
		'tags',
		'blank',
		'hours', 'email', 'phone', 'extension', 'street', 'street_secondary', 'city', 'state', 'zip_code',
		'contact_name', 'contact_position', 'fax_number', 'contact_email',
		'attachment', 'embedded_content',
		)
		# content_type is used to manage images, so the user should not manipulate it
		exclude = (
			'content_type', 'attachment_content_type'
		)

	def __init__(self, *args, **kwargs):
		super(CreateResourceForm, self).__init__(*args, **kwargs)
        # Tags field represented via the CheckboxSelectMultiple() widget
		self.fields['tags'].widget = CheckboxSelectMultiple()
		self.fields['tags'].queryset = Tag.objects.all()

		# Hide the is_active field if the model is being created
		# https://stackoverflow.com/questions/55994307/exclude-fields-for-django-model-only-on-creation
		if not self.instance or self.instance.pk is None:
			for name, field in self.fields.items():
				if name in ['is_active', ]:
					field.widget = forms.HiddenInput()

	# Validate the resource image
	def clean_image(self):
		image = self.cleaned_data['image']

		if image:
			# Raise an error if the file's extension isn't valid
			if not image.name.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
				raise forms.ValidationError('File type is not image')

			# Raise an error if the file isn't an image or if it is too large
			try:
				if (not image.content_type) or (not image.content_type.startswith('image')):
					raise forms.ValidationError('File type is not image')
				if image.size > MAX_IMAGE_UPLOAD_SIZE:
					raise forms.ValidationError('File too big (max: {0} mb)'.format(MAX_IMAGE_UPLOAD_SIZE/1000000))
			except:
				pass

		return image

	# Validate the phone number entered
	def clean_phone(self):
		# Obtain only the digits entered from the phone
		phone = self.cleaned_data['phone']
		cleaned_phone = ''.join(digit for digit in phone if digit.isdigit())

		# Validate that the phone number is either the standard 10 digits or it is 11 starting with a 1
		if phone and (len(cleaned_phone) != 10 and not (len(cleaned_phone) == 11 and cleaned_phone[0] == '1') and not (len(cleaned_phone) == 3 and cleaned_phone[1] == '1' and cleaned_phone[2] == '1')):
			raise forms.ValidationError('The phone number must be either exactly 10 digits, a 1 followed by 10 digits, or an N-1-1 code of 3 digits.')

		return cleaned_phone

	# Validate the fax number entered
	def clean_fax_number(self):
		# Obtain only the digits entered from the fax
		fax_number = self.cleaned_data['fax_number']
		cleaned_fax_number = ''.join(digit for digit in fax_number if digit.isdigit())

		# Validate that the fax number is either the standard 10 digits or it is 11 starting with a 1
		if fax_number and (len(cleaned_fax_number) != 10 and not (len(cleaned_fax_number) == 11 and cleaned_fax_number[0] == '1')):
			raise forms.ValidationError('The fax number must be either exactly 10 digits or a 1 followed by 10 digits.')

		return cleaned_fax_number

	# Validate a file attachment
	def clean_attachment(self):
		file = self.cleaned_data['attachment']

		if file:
			# Raise an error if the file's extension isn't valid
			if not file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.pdf', '.mp4', '.mpeg', '.mov', '.wmv', '.webm')):
				raise forms.ValidationError('File type is not a PDF, image or video file.')

			# Raise an error if the file isn't an image or if it is too large
			try:
				if ((not file.content_type)
				or (not file.content_type.startswith('image'))
				or (not file.content_type.startswith('video'))
				or (not file.content_type.startswith('application/pdf'))):
					raise forms.ValidationError('File type is not a PDF, image or video file.')
				if file.size > MAX_ATTACHMENT_UPLOAD_SIZE:
					raise forms.ValidationError('File too big (max: {0} mb)'.format(MAX_ATTACHMENT_UPLOAD_SIZE/1000000))
			except:
				pass

		return file

# Form only used to edit notes
class EditReferralNotesForm(forms.ModelForm):
	# Notes is the only attribute SOWs can freely edit
	notes = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs=INPUT_ATTRIBUTES))

	# Define the model and fields to include/exclude
	class Meta:
		model = Referral
		fields = ('notes',)

# # Form only used to edit notes in a Student Referral
# class EditStudentReferralNotesForm(forms.ModelForm):
# 	# Notes is the only attribute SOWs can freely edit
# 	notes = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs=INPUT_ATTRIBUTES))

# 	# Define the model and fields to include/exclude
# 	class Meta:
# 		model = StudentReferral
# 		fields = ('notes',)

# Form to select timeframe of risk assessment data
class SelectDataTimeframe(forms.Form):
	start_date = forms.DateField(widget=forms.widgets.DateInput(attrs={'type': 'date'}))
	end_date = forms.DateField(widget=forms.widgets.DateInput(attrs={'type': 'date'}))

	class Meta:
		fields = ('start_date','end_date')

# Form to create or edit tags
class TagForm(forms.ModelForm):
	# Name is the only attribute
	name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))

	# Define the model and fields to include/exclude
	class Meta:
		model = Tag
		fields = ('name',)

# Filter function for the resources; needs instantiation as a form
class ResourceFilter(django_filters.FilterSet):
	# Tags is the only attribute; uses the CheckboxSelectMultiple widget for easy selection
	tags = django_filters.ModelMultipleChoiceFilter(queryset=Tag.objects.all(), widget=forms.CheckboxSelectMultiple, label='')

	# Define the model and fields to include/exclude
	class Meta:
		model = Resource
		fields = ('tags',)

# Meeting Tracker Form
class MeetingTrackerForm(forms.ModelForm):
    notes = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs=INPUT_ATTRIBUTES))
    date = forms.DateField(widget=DatePickerInput())
    time = forms.TimeField(widget=TimePickerInput())
    duration = forms.FloatField(label="Duration (hours)")

    class Meta:
        model = MeetingTracker
        fields = ['with_who', 'purpose', 'neighborhood', 'duration', 'date', 'time', 'notes']

# Risk Assessment Form
# class RiskAssessmentForm(forms.ModelForm):
#     notes = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs=INPUT_ATTRIBUTES))
#     date = forms.DateField(widget=DatePickerInput())
#     time = forms.TimeField(widget=TimePickerInput())

#     class Meta:
#         model = RiskAssessment
#         fields = ['risk_level', 'actions', 'neighborhood', 'notes', 'date', 'time']

# Bi-weekly Form
# class BiweeklyForm(forms.ModelForm):
#     pay_start = forms.DateField(label='Start of the pay period', widget=DatePickerInput())
#     pay_end = forms.DateField(label='End of the pay period', widget=DatePickerInput())
#     work_hours = forms.IntegerField(label='Total hours work this pay period')
#     special_hours = forms.IntegerField(label='Total hours of special event')
#     num_special_events = forms.IntegerField(label='Number of special events')
#     meeting_hours = forms.IntegerField(label='Total hours of meetings attended')
#     num_meetings = forms.IntegerField(label='Number of meetings attended')
#     other = forms.IntegerField(label='Other hours')
#     num_served = forms.IntegerField(label='Number Served')
#     num_responses = forms.IntegerField(label='Number of incident responses')
#     num_events = forms.IntegerField(label='Number of community meetings/events')
#     num_visits = forms.IntegerField(label='Number of home visits')
#     num_mediations = forms.IntegerField(label='Number of mediations')
#     first_summary = forms.CharField(max_length=1000, required=False, label='Summary for the first week', widget=forms.Textarea(attrs=INPUT_ATTRIBUTES))
#     second_summary = forms.CharField(max_length=1000, required=False, label='Summary for the second week', widget=forms.Textarea(attrs=INPUT_ATTRIBUTES))
#     date = forms.DateField(widget=DatePickerInput())

#     class Meta:
#         model = Biweekly
#         fields = ['pay_start', 'pay_end', 'work_hours', 'special_hours', 'num_special_events', 'meeting_hours', 'num_meetings', 'other', 'num_served', 'location', 'intervention', 'num_responses', 'num_events', 'num_visits', 'num_mediations', 'first_summary', 'second_summary', 'date']

# Standard Validation Forms 

# Form for a user to log in
class LoginForm(forms.Form):
	# Set up attributes; username and password are the only ones relevant for login
	username = forms.CharField(max_length=150, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	password = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs=INPUT_ATTRIBUTES))

	# Ensure that the username and password are valid
	def clean(self):
		# cleaned_data is necessary to get the fields after they've already been cleaned
		cleaned_data = super().clean()
		username = cleaned_data.get('username')
		password = cleaned_data.get('password')

		# Determine if a user exists with the given username and password
		user = authenticate(username=username, password=password)

		# Raise an error if the user does not exist
		if not user:
			raise forms.ValidationError("Invalid Username or Password Entered")

		return cleaned_data # Required by super

# Form for a user to switch roles
class RoleSwitchForm(forms.Form):
	role_choices = {
		'is_safe_passage_coordinator': 'SPC (Safe Passage Coordinator)',
		'is_safe_passage_coordinator_supervisor': 'SPC Supervisor',
		'is_supervisor': 'Supervisor',
		'is_superuser': 'Admin'
	}
	role = forms.ChoiceField(widget=forms.RadioSelect(choices=role_choices))

# Form for an admin to add a user
class RegistrationForm(forms.Form):
	# Set up attributes
	username = forms.CharField(max_length=150, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	password = forms.CharField(max_length=50, label='Password', widget=forms.PasswordInput(attrs=INPUT_ATTRIBUTES))
	confirm_password = forms.CharField(max_length=50, label='Confirm Password', widget=forms.PasswordInput(attrs=INPUT_ATTRIBUTES))
	email = forms.EmailField(max_length=254, widget=forms.EmailInput(attrs=INPUT_ATTRIBUTES))
	first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	phone = forms.CharField(max_length=11, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
	organization = forms.ModelChoiceField(queryset=Organization.objects.all())
	user_type = forms.MultipleChoiceField(choices=USER_TYPE_CHOICES,
									   label='User Type',
									   widget=forms.CheckboxSelectMultiple(attrs={'class': 'list-unstyled'})
									)

	# Define the model and fields to include/exclude
	class Meta:
		model = User
		fields = ['username', 'password', 'confirm_password' 'email', 'first_name', 'last_name', 'phone', 'team']
		# A user cannot make be made inactive when first created
		exclude = (
			'is_active',
		)

	# Ensure that the user's password is valid
	def clean(self):
		# cleaned_data is necessary to get the fields after they've already been cleaned
		cleaned_data = super().clean()
		password = cleaned_data.get('password')
		confirm_password = cleaned_data.get('confirm_password')

		# Raise an error if the password doesn't match the password_confirmation
		if password and confirm_password and password != confirm_password:
			raise forms.ValidationError("Passwords did not match.")

		return cleaned_data

	# Ensure that the username is not already used
	def clean_username(self):
		username = self.cleaned_data.get('username')

		# Raise an error if the username is already in the database
		if User.objects.filter(username__exact=username):
			raise forms.ValidationError("Username is already taken.")

		return username

	# Validate the phone number entered
	def clean_phone(self):
		# Obtain only the digits entered from the phone
		phone = self.cleaned_data['phone']
		cleaned_phone = ''.join(digit for digit in phone if digit.isdigit())

		# Validate that the phone number is either the standard 10 digits or it is 11 starting with a 1
		if phone and (len(cleaned_phone) != 10 and not (len(cleaned_phone) == 11 and cleaned_phone[0] == '1')):
			raise forms.ValidationError('The phone number must be either exactly 10 digits or a 1 followed by 10 digits.')

		return cleaned_phone

	# Validate selected roles
	def clean_roles(self):
		roles = self.cleaned_data.get('user_type')

		if len(roles) == 0:
			raise forms.ValidationError('At least one role must be selected.')

# Form used to create and edit a StudentWeeklyUpdateForm
# class StudentWeeklyUpdateForm(forms.ModelForm):
# 	# Set up attributes
# 	weekly_absences = forms.IntegerField(widget=forms.NumberInput(attrs=INPUT_ATTRIBUTES), min_value=0, max_value=100)
# 	extra_curricular = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs=INPUT_ATTRIBUTES))
# 	special_needs = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs=INPUT_ATTRIBUTES))
# 	goals = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs=INPUT_ATTRIBUTES))
# 	notes = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs=INPUT_ATTRIBUTES))

# 	# Define the model and fields to include/exclude
# 	class Meta:
# 		model = StudentWeeklyUpdate
# 		fields = [
# 			'weekly_absences',
# 			'extra_curricular',
# 			'special_needs',
# 			'goals',
# 			'notes',
# 			'is_active',
# 			'student',
# 			'date'
# 		]
# 		exclude = (
# 			'student', 'date'
# 		)

# 	def __init__(self, *args, **kwargs):
# 		super(StudentWeeklyUpdateForm, self).__init__(*args, **kwargs)
# 		# is_active field not defined above so it can be hidden on creation; if the case load user exists, is_active
# 		self.fields['is_active'].widget.attrs=INPUT_ATTRIBUTES

# 		# Hide the is_active field if the model is being created
# 		# https://stackoverflow.com/questions/55994307/exclude-fields-for-django-model-only-on-creation
# 		if not self.instance or self.instance.pk is None:
# 			for name, field in self.fields.items():
# 				if name in ['is_active', ]:
# 					field.widget = forms.HiddenInput()

# Form used to create and edit a Student
# class StudentForm(forms.ModelForm):
# 	current_year = datetime.now().year
# 	min_year = current_year - 1
# 	max_year = current_year + 10

# 	# Set up attributes
# 	first_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
# 	last_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES))
# 	graduation_year = forms.IntegerField(widget=forms.NumberInput(attrs=INPUT_ATTRIBUTES), min_value=min_year, max_value=max_year, initial=current_year)
# 	email = forms.CharField(max_length=255, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES), required=False)
# 	phone = forms.CharField(max_length=255, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES), required=False)
# 	parent_first_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES), required=False)
# 	parent_last_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES), required=False)
# 	parent_email = forms.CharField(max_length=255, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES), required=False)
# 	parent_phone = forms.CharField(max_length=255, widget=forms.TextInput(attrs=INPUT_ATTRIBUTES), required=False)

# 	# Define the model and fields to include/exclude
# 	class Meta:
# 		model = Student
# 		fields = [
# 			'first_name',
# 			'last_name',
# 			'graduation_year',
# 			'email',
# 			'phone',
# 			'parent_first_name',
# 			'parent_last_name',
# 			'parent_email',
# 			'parent_phone',
# 			'is_active',
# 			'user',
# 			'date_created',
# 		]
# 		exclude = (
# 			'user', 'date_created'
# 		)

# 	def __init__(self, *args, **kwargs):
# 		super(StudentForm, self).__init__(*args, **kwargs)
# 		# is_active field not defined above so it can be hidden on creation; if the case load user exists, is_active
# 		self.fields['is_active'].widget.attrs=INPUT_ATTRIBUTES

# 		# Hide the is_active field if the model is being created
# 		# https://stackoverflow.com/questions/55994307/exclude-fields-for-django-model-only-on-creation
# 		if not self.instance or self.instance.pk is None:
# 			for name, field in self.fields.items():
# 				if name in ['is_active', ]:
# 					field.widget = forms.HiddenInput()

# 	# Ensure that for a student entry, the SPC has inputted values for either the phone or the email, or both
# 	def clean(self):
# 		# cleaned_data is necessary to get the fields after they've already been cleaned
# 		cleaned_data = super().clean()
# 		phone = cleaned_data.get('phone')
# 		email = cleaned_data.get('email')

# 		# Raise an error if neither field is valid
# 		if not (phone or email):
# 			raise forms.ValidationError('You must input either a phone number or an email address for this student.')

# 		return cleaned_data

# Form used to create and edit a StudentQuarterlyUpdateForm
# class StudentQuarterlyUpdateForm(forms.ModelForm):
# 	# Set up attributes
# 	q1_gpa = forms.DecimalField(widget=forms.NumberInput(attrs=INPUT_ATTRIBUTES), decimal_places=2, min_value=0, max_value=5, required=False)
# 	q1_behavioral_infractions = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs=INPUT_ATTRIBUTES))
# 	q2_gpa = forms.DecimalField(widget=forms.NumberInput(attrs=INPUT_ATTRIBUTES), decimal_places=2, min_value=0, max_value=5, required=False)
# 	q2_behavioral_infractions = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs=INPUT_ATTRIBUTES))
# 	q3_gpa = forms.DecimalField(widget=forms.NumberInput(attrs=INPUT_ATTRIBUTES), decimal_places=2, min_value=0, max_value=5, required=False)
# 	q3_behavioral_infractions = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs=INPUT_ATTRIBUTES))
# 	q4_gpa = forms.DecimalField(widget=forms.NumberInput(attrs=INPUT_ATTRIBUTES), decimal_places=2, min_value=0, max_value=5, required=False)
# 	q4_behavioral_infractions = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs=INPUT_ATTRIBUTES))

# 	# Define the model and fields to include/exclude
# 	class Meta:
# 		model = StudentQuarterlyUpdate
# 		fields = [
# 			'student',
# 			'q1_gpa',
# 			'q1_behavioral_infractions',
# 			'q2_gpa',
# 			'q2_behavioral_infractions',
# 			'q3_gpa',
# 			'q3_behavioral_infractions',
# 			'q4_gpa',
# 			'q4_behavioral_infractions',
# 			'is_active',
# 			'date_created',
# 		]
# 		exclude = ('student', 'date_created')

# 	def __init__(self, *args, **kwargs):
# 		super(StudentQuarterlyUpdateForm, self).__init__(*args, **kwargs)
# 		# is_active field not defined above so it can be hidden on creation; if the case load user exists, is_active
# 		self.fields['is_active'].widget.attrs=INPUT_ATTRIBUTES

# 		# Hide the is_active field if the model is being created
# 		# https://stackoverflow.com/questions/55994307/exclude-fields-for-django-model-only-on-creation
# 		if not self.instance or self.instance.pk is None:
# 			for name, field in self.fields.items():
# 				if name in ['is_active', ]:
# 					field.widget = forms.HiddenInput()

# class StudentWeeklyUpdateUploadForm(forms.ModelForm):
# 	class Meta:
# 		model = StudentWeeklyUpdateUpload
# 		fields = ['file']

# 	def clean_file(self):
# 		file = self.cleaned_data.get('file')

# 		if file:
# 			if isinstance(file, UploadedFile) and file.content_type not in ['image/jpeg', 'image/png', 'application/pdf']:
# 				raise forms.ValidationError('Invalid file format. Only JPEG, PNG, and PDF files are allowed.')

# 			if isinstance(file, UploadedFile) and file.size > 2 * 1024 * 1024:
# 				raise forms.ValidationError('File size exceeds the limit of 2MB.')

# 		return file

# StudentWeeklyUpdateUploadFormset = forms.modelformset_factory(
#     StudentWeeklyUpdateUpload,
#     form=StudentWeeklyUpdateUploadForm,
#     extra=1,
#     max_num=5,  # Optional: Set a maximum number of file uploads per formset
#     can_delete=True,  # Optional: Allow deleting uploaded files
# )
