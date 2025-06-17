import environ

from .base import *

env = environ.Env()
environ.Env.read_env()
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", default=False)

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
DATABASES = {
    'default': {
        "ENGINE": env("DB_ENGINE", default="django.db.backends.sqlite3"),
        "NAME": env("POSTGRES_DB", default=os.path.join(BASE_DIR, "db.sqlite3")),
        "USER": env("POSTGRES_USER", default="user"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="password"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
    }
}

# change
ALLOWED_HOSTS = env.list("SERVERNAMES", default="localhost")

EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")

ANYMAIL = {
    "SENDGRID_API_KEY": env("SENDGRID_API_KEY", default=""),
}

EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="xxxx@gmail.com")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="xxxx@gmail.com")
EMAIL_PORT = 587
EMAIL_USE_TLS = bool(env("EMAIL_USE_TLS", default=True))
SERVER_EMAIL = env("SERVER_EMAIL", default="xxxx@gmail.com")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="mypassword")


# Use this var to identify commit info at the top of the app - Don't use this in Production Environment
REPO_DIR = env("REPO_DIR", default='')

CUSTOMER_SERVICE = env("CUSTOMER_SERVICE", default="")

# Logging

GPT_LOGFILE_NAME = os.path.join(
    BASE_DIR, "logs", "gpt.log"
)

LOGFILE_SIZE = 1024 * 1024 * 50  # 50 MB
LOGFILE_COUNT = 5

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",  # noqa
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
        "simple": {"format": "[%(name)s:%(lineno)s] %(levelname)s %(message)s"},  # noqa
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", },
        "gpt_log": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": GPT_LOGFILE_NAME,
            "maxBytes": LOGFILE_SIZE,
            "backupCount": LOGFILE_COUNT,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "gpt": {
            "handlers": ["gpt_log"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}


#######################
#      OPENAI         #
#######################

OPENAI_USE_AZURE = bool(env("OPENAI_USE_AZURE", default=False))

if OPENAI_USE_AZURE:
    OPENAI_AZURE_ENDPOINT = env("OPENAI_AZURE_ENDPOINT", default="")
    OPENAI_AZURE_API_KEY = env("OPENAI_AZURE_API_KEY", default="")
    OPENAI_AZURE_DEPLOYMENT_NAME = env(
        "OPENAI_AZURE_DEPLOYMENT_NAME", default="")
    OPENAI_AZURE_MODEL = env("OPENAI_AZURE_MODEL", default="")
    OPENAI_AZURE_API_VERSION = env("OPENAI_AZURE_API_VERSION", default="")
    OPENAI_AZURE_WHISPER_DEPLOYMENT_NAME = env(
        "OPENAI_AZURE_WHISPER_DEPLOYMENT_NAME", default="")
else:
    OPENAI_LIVE_MODE = bool(env("OPENAI_LIVE_MODE", default=False))

    if OPENAI_LIVE_MODE:
        OPENAI_API_KEY = env("OPENAI_API_KEY_LIVE", default="")
    else:
        OPENAI_API_KEY = env("OPENAI_API_KEY_TEST", default="")

    OPENAI_DEFAULT_MODEL = env("OPENAI_DEFAULT_MODEL", default="gpt-3.5-turbo")
    OPENAI_WHISPER_MODEL = env("OPENAI_WHISPER_MODEL", default="whisper-1")

GPT_MODEL_MAX_TOKENS = env("GPT_MODEL_MAX_TOKENS", default=4096)
GPT_MAX_TOKENS_PER_RESPONSE = env(
    "GPT_MAX_TOKENS_PER_RESPONSE", default=800)
GPT_TEMPERATURE = env("GPT_TEMPERATURE", default=0.2)


# CORS & CSRF SETTINGS
CORS_ORIGIN_WHITELIST = env.list("CORS_ORIGIN_WHITELIST", default=[
    "http://localhost:8000",
    "http://localhost:8080",
    "http://localhost:3000"
])
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[
    "http://localhost:8000",
    "http://localhost:80",
    "http://127.0.0.1:80",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
])
CORS_ALLOW_HEADERS = env.list("CORS_ALLOW_HEADERS", default=[
    "accept",
    "authorization",
    "content-type",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "session-user-id",
])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[
    "http://localhost:8080",
    "http://localhost:3000"
])
