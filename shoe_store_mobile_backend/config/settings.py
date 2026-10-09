# os lets us read environment variables such as database credentials
# and Django configuration values.
import os

# Path helps us build reliable file paths based on the project's
# location instead of hard-coding Windows paths.
from pathlib import Path

# load_dotenv reads values from our .env file and loads them
# into the environment so Django can access them with os.getenv().
from dotenv import load_dotenv


# ---------------------------------------------------------
# PROJECT PATHS / ENVIRONMENT VARIABLES
# ---------------------------------------------------------

# BASE_DIR points to the root folder of the Django project.
#
# Example:
# C:\Users\julie\OneDrive\ShoeMobileApp\shoe_store_mobile_backend
BASE_DIR = Path(__file__).resolve().parent.parent


# Load environment variables from:
#
# shoe_store_mobile_backend/.env
#
# This keeps passwords and secret values out of settings.py.
load_dotenv(BASE_DIR / '.env')


# ---------------------------------------------------------
# DJANGO SECURITY / DEVELOPMENT SETTINGS
# ---------------------------------------------------------

# SECRET_KEY is used internally by Django for cryptographic signing.
#
# The real value is stored in .env rather than directly in the code.
SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    'dev-secret-key'
)


# DEBUG=True displays detailed Django error pages.
#
# This is useful during development but MUST be False in production
# because debug pages can expose sensitive application information.
DEBUG = (
        os.getenv('DJANGO_DEBUG', 'True').lower() == 'true'
)


# During local development we currently allow requests using any host.
#
# IMPORTANT:
# In production this should be restricted to the real domain/server,
# such as:
#
# ALLOWED_HOSTS = ['api.example.com']
ALLOWED_HOSTS = ['*']


# ---------------------------------------------------------
# INSTALLED DJANGO APPLICATIONS
# ---------------------------------------------------------

INSTALLED_APPS = [

    # Django's built-in administration interface.
    'django.contrib.admin',

    # Django's built-in authentication system:
    # users, passwords, permissions, and groups.
    'django.contrib.auth',

    # Tracks Django model/content types.
    'django.contrib.contenttypes',

    # Enables Django session support.
    'django.contrib.sessions',

    # Provides Django's messaging framework.
    'django.contrib.messages',

    # Handles static files such as CSS and JavaScript.
    'django.contrib.staticfiles',


    # Django REST Framework provides tools for building our API.
    'rest_framework',

    # Adds token authentication support for the mobile app.
    #
    # Customers log in and receive a token that they send with
    # protected API requests.
    'rest_framework.authtoken',

    # Allows requests from a frontend running on a different
    # origin/domain during development.
    'corsheaders',

    # Our shoe store application containing models, serializers,
    # views, services, and API routes.
    'store',
]


# ---------------------------------------------------------
# MIDDLEWARE
# ---------------------------------------------------------

# Middleware processes requests before they reach a view and
# responses before they return to the client.
MIDDLEWARE = [

    # Handles Cross-Origin Resource Sharing (CORS).
    # It is placed near the top so it can modify responses early.
    'corsheaders.middleware.CorsMiddleware',

    # Adds various security protections.
    'django.middleware.security.SecurityMiddleware',

    # Enables Django session handling.
    'django.contrib.sessions.middleware.SessionMiddleware',

    # Handles common HTTP behaviors such as trailing slash redirects.
    'django.middleware.common.CommonMiddleware',

    # Protects traditional Django forms against CSRF attacks.
    'django.middleware.csrf.CsrfViewMiddleware',

    # Associates authenticated Django Users with incoming requests.
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # Enables Django's message framework.
    'django.contrib.messages.middleware.MessageMiddleware',

    # Helps prevent the site from being embedded inside malicious frames.
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ---------------------------------------------------------
# URL CONFIGURATION
# ---------------------------------------------------------

# Tells Django that the main URL configuration is located in:
#
# config/urls.py
ROOT_URLCONF = 'config.urls'


# ---------------------------------------------------------
# TEMPLATE CONFIGURATION
# ---------------------------------------------------------

# Django templates are mainly needed for Django Admin right now.
#
# The customer-facing application will eventually be React Native,
# so most customer screens will not use Django templates.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        # No custom project-wide template folders are currently used.
        'DIRS': [],

        # Allows Django to find templates inside installed apps.
        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [

                # Makes the request available inside templates.
                'django.template.context_processors.request',

                # Makes authentication/user information available.
                'django.contrib.auth.context_processors.auth',

                # Makes Django messages available to templates.
                'django.contrib.messages.context_processors.messages',
            ]
        },
    }
]


# ---------------------------------------------------------
# WSGI
# ---------------------------------------------------------

# WSGI is the interface Django can use when served by a production
# web server.
#
# Django's runserver command uses a development server instead.
WSGI_APPLICATION = 'config.wsgi.application'


# ---------------------------------------------------------
# MYSQL DATABASE
# ---------------------------------------------------------

DATABASES = {
    'default': {

        # Tell Django to use MySQL.
        'ENGINE': 'django.db.backends.mysql',

        # Database connection information comes from the .env file.
        #
        # If an environment variable is missing, the second value
        # acts as a development fallback.
        'NAME': os.getenv(
            'DB_NAME',
            'shoe_store'
        ),

        'USER': os.getenv(
            'DB_USER',
            'shoe_user'
        ),

        'PASSWORD': os.getenv(
            'DB_PASSWORD',
            ''
        ),

        # 127.0.0.1 means MySQL is running on this computer.
        'HOST': os.getenv(
            'DB_HOST',
            '127.0.0.1'
        ),

        # 3306 is MySQL's standard/default port.
        'PORT': os.getenv(
            'DB_PORT',
            '3306'
        ),

        'OPTIONS': {

            # utf8mb4 supports full Unicode, including emoji and
            # a wide range of international characters.
            'charset': 'utf8mb4',
        },
    }
}


# ---------------------------------------------------------
# PASSWORD VALIDATION
# ---------------------------------------------------------

# Django's built-in password validators are currently disabled.
#
# This is acceptable while we are developing/testing, but before
# production we should enable strong password validation rules.
AUTH_PASSWORD_VALIDATORS = []


# ---------------------------------------------------------
# LANGUAGE / TIME ZONE
# ---------------------------------------------------------

# Default application language.
LANGUAGE_CODE = 'en-us'


# Store/display application times using the Pacific time zone.
TIME_ZONE = 'America/Los_Angeles'


# Enable Django's internationalization features.
USE_I18N = True


# Store datetime values using timezone-aware timestamps.
USE_TZ = True


# ---------------------------------------------------------
# STATIC FILES
# ---------------------------------------------------------

# URL prefix used for Django static files.
#
# This currently matters mainly for Django Admin.
STATIC_URL = 'static/'


# ---------------------------------------------------------
# DEFAULT DATABASE PRIMARY KEY TYPE
# ---------------------------------------------------------

# New Django models automatically use BigAutoField for their
# integer primary keys unless another field is explicitly defined.
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

# During development, allow API requests from any frontend origin.
#
# This makes it easier to test the future React Native/mobile
# frontend against the Django backend.
#
# IMPORTANT:
# In production this should be restricted to approved origins
# instead of remaining True.
CORS_ALLOW_ALL_ORIGINS = True


# ---------------------------------------------------------
# DJANGO REST FRAMEWORK
# ---------------------------------------------------------

REST_FRAMEWORK = {

    # API endpoints are publicly accessible by default.
    #
    # Individual protected views, such as checkout, addresses,
    # and order history, explicitly use:
    #
    # permission_classes = [IsAuthenticated]
    #
    # Our product/category endpoints are intentionally public.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],


    # TokenAuthentication allows the mobile app to authenticate
    # using a token in the HTTP Authorization header.
    #
    # Example:
    #
    # Authorization: Token abc123...
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}