from config.env import env
import logging.config

# 日志 测试
if env.bool("DJANGO_DEBUG", default=True):
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django.db.backends': {
                'handlers': ['console'],
                'propagate': False,
                'level': 'DEBUG',
            },
        }
    }
else:
    LOGGING_CONFIG = None
    if env.bool("DJANGO_INNER_LOG", default=False):
        CONF = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'verbose': {
                    'format': '[%(asctime)s] %(levelname)s %(filename)s[line:%(lineno)d] %(message)s',
                    # '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
                    # 'datefmt': '%y-%m-%d %H:%M:%S',
                },
                'simple': {
                    'format': '[%(asctime)s] %(levelname)s %(message)s',
                },
            },
            "filters": {
                "require_debug_false": {
                    "()": "django.utils.log.RequireDebugFalse",
                },
                "require_debug_true": {
                    "()": "django.utils.log.RequireDebugTrue",
                },
            },
            'handlers': {
                'console': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'simple',
                },
                'mp': {
                    'level': 'INFO',
                    'class': 'logging.StreamHandler',
                    'formatter': 'verbose',
                },
                'mail_admins': {
                    'level': 'ERROR',
                    'filters': ['require_debug_false'],
                    'class': 'django.utils.log.AdminEmailHandler',
                    'include_html': True,
                },
            },
            'loggers': {
                'root': {
                    'level': 'INFO',
                    'handlers': ['mp'],
                    "propagate": True,
                },
                "django.request": {
                    "handlers": ["mail_admins"],
                    "level": "ERROR",
                    "propagate": False,
                },
                "django.server": {
                    "handlers": ["console"],
                    "level": "INFO",
                    "propagate": False,
                },

            }
        }

        logging.config.dictConfig(CONF)

