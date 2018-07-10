#!/usr/bin/env python
from flask import Flask
from app import create_app

application = Flask('application')

create_app(application)
