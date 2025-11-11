from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
AZURE_ACCOUNT_NAME = os.environ.get('AZURE_ACCOUNT_NAME')
AZURE_ACCOUNT_KEY = os.environ.get('AZURE_ACCOUNT_KEY')


if AZURE_ACCOUNT_NAME:
    # 1. Configuración de PRODUCCIÓN (Azure)

    AZURE_CUSTOM_DOMAIN = f'{AZURE_ACCOUNT_NAME}.blob.core.windows.net'

    # Configuración de Archivos Estáticos (CSS, JS)
    AZURE_CONTAINER = 'static'
    STATICFILES_STORAGE = 'storages.backends.azure_storage.AzureStorage'
    STATICFILES_LOCATION = AZURE_CONTAINER
    STATIC_URL = f'https://{AZURE_CUSTOM_DOMAIN}/{AZURE_CONTAINER}/'

    # Configuración de Archivos Media (Fotos de perfil)
    AZURE_MEDIA_CONTAINER = 'media'
    DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'
    MEDIAFILES_LOCATION = AZURE_MEDIA_CONTAINER
    MEDIA_URL = f'https://{AZURE_CUSTOM_DOMAIN}/{AZURE_MEDIA_CONTAINER}/'

else:
    # 2. Configuración LOCAL (tu PC)

    STATIC_URL = '/static/'
    STATIC_ROOT = BASE_DIR / 'staticfiles_production' # Carpeta para 'collectstatic' local
    STATICFILES_DIRS = [
    BASE_DIR / "static",
    ]

    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media/'
# SECURITY WARNING: don't run with debug turned on in production!
#DEBUG = False
#ALLOWED_HOSTS = [
#    'inspecmax-d7caewfbe0ahg5h7.brazilsouth-01.azurewebsites.net',
#
#     'localhost', # Opcional, para pruebas locales
#]

#ALLOWED_HOSTS = []
WEBSITE_HOSTNAME = os.environ.get('WEBSITE_HOSTNAME')

if WEBSITE_HOSTNAME:
    # Si la variable existe, estamos en producción (Azure)
    DEBUG = False
    ALLOWED_HOSTS = [WEBSITE_HOSTNAME]
else:
    # Si la variable NO existe, estamos en local (tu PC)
    DEBUG = True  # O False, como prefieras para local
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
    'storages',
]

# Configuración para Django Crispy Forms (usando Bootstrap 5)
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5" # Esto funciona porque ahora tenemos 'crispy_bootstrap5' en INSTALLED_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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
        'DIRS': [BASE_DIR / "Templates"],  # Aquí apunta a tu carpeta Templates global
        'APP_DIRS': True, # <--- ¡CLAVE! Esto permite a Django buscar templates dentro de la carpeta 'templates' de cada INSTALLED_APP (incluyendo crispy_forms y crispy_bootstrap5).
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
# https://docs.docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# settings.py

# Esto ya deberías tener:
STATIC_URL = '/static/'

# Agrega esto:
import os
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# OptifireAPT/settings.py (Fragmento)

# URL a donde redirigir si se necesita iniciar sesión
LOGIN_URL = 'login' # Usa el nombre de la ruta de login de Django (que viene en include('django.contrib.auth.urls'))

# URL por defecto a donde redirigir después de iniciar sesión.
# Django buscará esta URL después de un login exitoso.
LOGIN_REDIRECT_URL = '/usuarios/' # Redirige a la nueva vista del inspector/usuario normal

# URL a donde redirigir después de cerrar sesión
LOGOUT_REDIRECT_URL = '/'