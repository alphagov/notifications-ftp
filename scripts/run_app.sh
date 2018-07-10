#!/bin/bash

set -e

source environment.sh

FLASK_APP=wsgi.py flask run -p 6015
