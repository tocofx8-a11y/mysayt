"""
Raqamli Avlod — O'quv markaz platformasi uchun Django sozlamalari.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# XAVFSIZLIK: production'ga chiqarishdan oldin bu qiymatlarni albatta o'zgartiring!
SECRET_KEY = 'django-insecure-CHANGE-THIS-BEFORE-DEPLOY'
DEBUG = True
ALLOWED_HOSTS = ['*']  # rivojlantirish uchun; productionda aniq domen yoziladi

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Bizning ilovalarimiz
    'accounts',   # foydalanuvchilar va rollar (Super Admin, Admin, O'qituvchi, Talaba)
    'core',       # kurslar, guruhlar, darslar, faoliyat logi
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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
                'core.context_processors.showcase_cards',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Ma'lumotlar bazasi — boshida SQLite, keyinchalik PostgreSQL'ga o'tkazish mumkin
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Bizning maxsus User modelimiz (4 xil rol bilan)
AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Talabalar yuklaydigan fayllar (.pdf, .docx, .txt, video va h.k.) shu yerga saqlanadi
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login qilingandan keyin qayerga yo'naltirilishi rolga qarab views.py da belgilanadi
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'   # login'dan keyin 'home' ga o'tadi, u yerdan rolga qarab tegishli panelga yo'naltiriladi
