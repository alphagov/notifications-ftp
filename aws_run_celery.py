#!/usr/bin/env python
from app import create_app
from credstash import getAllSecrets
import os

os.environ.update(getAllSecrets(region="eu-west-1"))

application = create_app()
application.app_context().push()
