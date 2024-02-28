"""
Django settings for ReEntryApp project.

Generated by 'django-admin startproject' using Django 3.0.3.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
from django.core.exceptions import ImproperlyConfigured

from dotenv import load_dotenv
load_dotenv()

# ENV VAR FETCHER / WRAPPER 
def get_env_value(env_variable):
    try:
        return os.environ[env_variable]
    except KeyError:
        error_msg = 'Couldn\'t fetch the {} from the env'.format(env_variable)
        raise ImproperlyConfigured(error_msg)


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_env_value('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = False
DEBUG = True

# ALLOWED_HOSTS = ['67.205.174.6', 'www.newera412.com', 'newera412.com']
ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_filters',
    'NewEra',
    'django_select2',
    'bootstrap_datepicker_plus',
    'encrypted_model_fields',
]

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ReEntryApp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ReEntryApp.wsgi.application'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'my_cache_table',
    },
    'select2': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'my_cache_table',
    },
}

# DEPLOYMENT DATABASE 
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DB_NAME = get_env_value("DB_NAME")
DB_USER = get_env_value("DB_USER")
DB_PASS = get_env_value("DB_PASS")
DB_HOST = get_env_value("DB_HOST")

DATABASES = {
        'default' : {
            'ENGINE' : 'django.db.backends.postgresql_psycopg2',
            'NAME' : DB_NAME,
            'USER' : DB_USER,
            'PASSWORD' : DB_PASS,
            'HOST' : DB_HOST,
            'PORT' : '',
        }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_L10N = True
USE_TZ = True

#####################################################
# Additional Non-Trivial Vars
#####################################################

# AUTH 
LOGIN_URL = '/login'
LOGIN_REDIRECT_URL = '/'

# Makes our custom user the base used for authentication (overrides django default)
AUTH_USER_MODEL = 'NewEra.User'

# EMAIL (Temporary credentials added below:)
EMAIL_HOST = 'smtp.gmail.com'   
EMAIL_PORT = 587
EMAIL_HOST_USER = get_env_value('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = get_env_value('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
RISK_ASSESSMENT_EMAIL_TO = get_env_value('RISK_ASSESSMENT_EMAIL_TO')
RISK_ASSESSMENT_EMAIL_CC = get_env_value('RISK_ASSESSMENT_EMAIL_CC')

# TWILIO SMS

TWILIO_PHONE_NUMBER = get_env_value('TWILIO_PHONE_NUMBER')
TWILIO_ACCOUNT_SID = get_env_value('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = get_env_value('TWILIO_AUTH_TOKEN')

# For use in links sent in EMAIL/SMS notifications 
# REFERRAL_LINK_ROOT = 'www.newera412.com'

# Misc Deployment Vars 

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'NewEra/static'),
)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'NewEra/user_uploads/')

# DB Configuration 

import dj_database_url 
prod_db  =  dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(prod_db)

FIELD_ENCRYPTION_KEY = 'NcHmRPUyTEKrz9CgL04pHVhl9Gymxo5uaxtMbfuAWl8='
