#!/usr/bin/env python
from app import create_app

application = create_app()
application.app_context().push()
