#!/usr/bin/env python
import os

from flask import Flask

from app import create_app

os.environ['AWS_REGION'] = 'eu-west-1'
application = Flask('application')

create_app(application)
