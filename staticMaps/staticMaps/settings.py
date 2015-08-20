# coding=UTF-8

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def env_var(key, default=None):
    """Retrieves env vars and makes Python boolean replacements"""
    val = os.environ.get(key, default)
    if val == 'True':
        val = True
    elif val == 'False':
        val = False
    elif val == 'None':
        val = None
    return val


BASE_LAYER_DIR = os.path.join(BASE_DIR, "baselayers")
BASE_LAYERS = {}

for filename in os.listdir(BASE_LAYER_DIR):
    base, ext = os.path.splitext(filename)
    if ext == ".xml":
        BASE_LAYERS[base] = filename

BASE_LAYERS_ATTRIBUTION = {}
try:
    with open(os.path.join(BASE_LAYER_DIR, "attribution.json"), "r") as f:
        BASE_LAYERS_ATTRIBUTION = json.load(f)
except Exception, e:
    print "Error loading baselayers %s" % e

ATTRIBUTION_FONT = os.path.join(BASE_DIR, "fonts/Raleway-Regular.ttf")
ATTRIBUTION_FONT_SIZE = 10
MAX_IMAGE_DIMENSION = env_var('MAX_IMAGE_DIMENSION', 1024)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'lr&)s39c&v@^0&%57zlwe_h3e_un*e*^xurh95rjzz=q6zkn^b'

DEBUG = env_var("DEBUG", False)
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = (
    'django.contrib.gis',
    'mapRender',
)

MIDDLEWARE_CLASSES = ()

ROOT_URLCONF = 'staticMaps.urls'

WSGI_APPLICATION = 'staticMaps.wsgi.application'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = False
USE_L10N = False
USE_TZ = False


# logging
LOG_LEVEL = 'INFO'
if DEBUG:
    LOG_LEVEL = 'DEBUG'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'syslog': {
            'format': ('staticmaps %(asctime)s [%(process)d] [%(levelname)s] ' +
                       '%(filename)s:%(lineno)s:%(funcName)s %(message)s'),
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
         },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

if env_var("LOGGING_SYSLOG", False) and os.path.exists("/dev/log"):
    # If rsyslogd is running, use it
    LOGGING["handlers"]["syslog"] = {
        'level': 'DEBUG',
        'class': 'logging.handlers.SysLogHandler',
        'formatter': 'syslog',
        'filters': ['user'],
        'facility': 'local5',
        'address': '/dev/log',
    }
    for (key, val) in LOGGING["loggers"].items():
        val["handlers"][0] = "syslog"
