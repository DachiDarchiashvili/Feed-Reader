# -*- coding: utf-8 -*-

"""
Created on Dec 28, 2019

@author: Dachi Darchiashvili
"""

from .base import *  # @UnusedWildImport


DEBUG = False

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'feed_reader_db',
        'USER': 'gocha',
        'PASSWORD': 'qwert5432',
        'HOST': 'pgdb',
        'PORT': '5432',
        'TEST': {
            'DEPENDENCIES': [],
        },
    },
}
