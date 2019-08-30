#!/usr/bin/env python
import os

from flask import Flask
from credstash import getAllSecrets

from app import create_app

os.environ['AWS_REGION'] = 'eu-west-1'
os.environ.update(getAllSecrets(region="eu-west-1"))

application = Flask('application')

create_app(application)
