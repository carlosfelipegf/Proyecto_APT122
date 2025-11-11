from pathlib import Path
import os  # <-- Asegúrate de que esto esté al principio

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# --- CLAVES SECRETAS ---
# Lee las claves desde las Variables de Entorno de Azure
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
AZURE_ACCOUNT_NAME = os.environ.get('AZURE_ACCOUNT_NAME')
AZURE_ACCOUNT_KEY = os.environ.get('AZURE_ACCOUNT_KEY')


# --- Configuración Dinámica de DEBUG y HOST ---
# Este bloque soluciona el Error 500
WEBSITE_HOSTNAME = os.environ.get('WEBSITE_HOSTNAME')

if WEBSITE_HOSTNAME:
    # Si la variable existe, estamos en producción (Azure)
    DEBUG = False
    ALLOWED_HOSTS = [WEBSITE_HOSTNAME]
else:
    # Si la variable NO existe, estamos en local (tu PC)
    DEBUG = True
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost']


# Application definition

INSTALLED_APPS = [
    # ... aplicaciones de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'usuarios.apps.UsuariosConfig',
    
    # Tus apps
    # 'otra_app',
    
    #  SOLUCIÓN: LIBRERÍAS CRISPY FORMS 
    # 1. App base de Crispy Forms
    'crispy_forms', 
    # 2. El paquete de templates específico para Bootstrap 5 (¡NECESARIO!)
    'crispy_bootstrap5',
    #'storages', # <-- Comentado por ahora, ¡correcto!
]

# Configuración para Django Crispy Forms (usando Bootstrap 5)
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'OptifireAPT.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "Templates"],
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


WSGI_APPLICATION = 'OptifireAPT.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':  os.environ.get('DB_NAME'),        
        'USER':  os.environ.get('DB_USER'),        
        'PASSWORD': os.environ.get('DB_PASSWORD'), 
        'HOST': os.environ.get('DB_HOST'),        
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',
        },          
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# --- Configuración de Archivos Estáticos (Temporal) ---
# Este es el bloque unificado y corregido
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles_production' # Necesario para que 'collectstatic' funcione
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
# (Dejamos MEDIA_URL y MEDIA_ROOT fuera por ahora)


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# OptifireAPT/settings.py (Fragmento)

# URL a donde redirigir si se necesita iniciar sesión
LOGIN_URL = 'login' 

# URL por defecto a donde redirigir después de iniciar sesión.
LOGIN_REDIRECT_URL = '/usuarios/' 

# URL a donde redirigir después de cerrar sesión
LOGOUT_REDIRECT_URL = '/'