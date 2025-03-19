"""
Django settings for anywall project.

Generated by 'django-admin startproject' using Django 4.2.13.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import subprocess

from anywall_app.logger import setup_logger
logger = setup_logger(__name__)

import os
import sys
from dotenv import load_dotenv



# print(f"os.getcwd()]: {os.getcwd()}")
# print(f"Path(__file__):{Path(__file__)}")
# # Load environment variables from .env file
load_dotenv('C:\\Anywall\\conf\\config.env', override=True)

a = os.getenv('DB_PASSWORD')

logger.debug(a)


try:
    python_exe_path = sys.executable
    logger.debug(f"python_exe_path: {python_exe_path}")
except Exception:
    python_exe_path = sys.executable


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

logger.debug(f"settings BASE_DIR + 1: {Path(__file__).resolve().parent}")
logger.debug(f"Path(__file__): {Path(__file__)}")

# Assuming '/Users/username/migrations/' is the external directory
external_migrations_dir = 'C:\\Anywall\\resources'


# Add the external directory to sys.path
sys.path.append(external_migrations_dir)


# Print the current sys.path
# print("paths in setting.py")
# for path in sys.path:
#     print(path)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-=mff#jb50a%mh=sg(np!0qo1*g6n-%0_5zgd!v00msq-+z9d5@'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

LOGIN_URL = '/login'
LOGIN_REDIRECT_URL = '/setting'
LOGOUT_REDIRECT_URL = '/login'

ASGI_APPLICATION = 'anywall.asgi.application'



ALLOWED_HOSTS = ['daattnnn', 'localhost', '127.0.0.1', '172.20.112.13', '172.16.0.74', '100.43.37.109']

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [("172.20.112.13", 6379)],
        },
    },
}

WS_PORT = 8000

CSRF_TRUSTED_ORIGINS = ['http://daattnnn:8000', 'http://172.20.112.13:8000', 'http://100.43.37.109:8000']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'rest_framework',
    'colorfield',
    'anywall_app',
    'drf_yasg',
    'channels',
]

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Basic': {
            'type': 'basic'
        }
    }
}

MEDIA_ROOT = 'C:\\Anywall\\resources\\'


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add WhiteNoise middleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'anywall_app.middleware.CustomHeadersMiddleware',
]

ROOT_URLCONF = 'anywall.urls'

# thisdir = os.path.dirname(os.path.abspath(__file__))

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'anywall.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'mysql.connector.django',
        'OPTIONS': {
            'read_default_file': os.path.join(BASE_DIR, 'my.cnf'),
        },
        'PORT': '3306',  # Default port for MySQL
        'OPTIONS': {
            'unix_socket': os.getenv('MYSQL_UNIX_PORT', '/home/runner/workspace/mysql_data/mysql.sock'),
        }
    }
}
DATABASES['default']['PASSWORD'] = os.getenv('DB_PASSWORD', '')

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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

MIGRATION_MODULES = {
    'anywall_app': 'migrations',
}

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Rome'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
#STATICFILES_DIRS = [
#    os.path.join(BASE_DIR, 'static')
#]
STATIC_ROOT = os.path.join(BASE_DIR, 'static')  # Add this line

# WhiteNoise settings
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
