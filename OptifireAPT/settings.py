from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-sbd#^wxmisc$n+(j#s!xy7g_#r2(9d*73dx2n8vg30vz=59#lb'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


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
    
    # 🚨 SOLUCIÓN: LIBRERÍAS CRISPY FORMS 🚨
    # 1. App base de Crispy Forms
    'crispy_forms', 
    # 2. El paquete de templates específico para Bootstrap 5 (¡NECESARIO!)
    'crispy_bootstrap5', 
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
        'DIRS': [BASE_DIR / 'templates'],
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
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

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

# Configuración de Archivos Multimedia (Fotos de perfil, documentos, etc.)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ==============================================================================
# CONFIGURACIÓN DE CORREO ELECTRÓNICO (SMTP) - ¡PARA RECUPERACIÓN DE CONTRASEÑA!
# ==============================================================================

# 1. Backend: Usa el backend SMTP para enviar correos reales.
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# 2. Host (Servidor de Correo): Por ejemplo, Gmail.
EMAIL_HOST = 'smtp.gmail.com'

# 3. Puerto: 587 es el estándar para STARTTLS.
EMAIL_PORT = 587             

# 4. Seguridad: Habilitar TLS (Transport Layer Security).
EMAIL_USE_TLS = True         

# 5. Credenciales: ¡REEMPLAZA ESTOS VALORES!
# IMPORTANTE: Si usas Gmail, necesitas generar una "Contraseña de Aplicación"
# y usarla aquí en lugar de tu contraseña principal.
EMAIL_HOST_USER = 'tu_email@gmail.com'  # <-- TU CORREO DE ENVÍO
EMAIL_HOST_PASSWORD = 'TU_CONTRASEÑA_O_CLAVE_DE_APLICACION' # <-- TU CLAVE/CONTRASEÑA

# Opcionales, pero buenas prácticas:
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = EMAIL_HOST_USER # Para correos de error del servidor