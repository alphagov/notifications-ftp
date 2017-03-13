import os

from app import create_app
from credstash import getAllSecrets

os.environ.update(getAllSecrets(region="eu-west-1"))

application = create_app()

if __name__ == "__main__":
    application.run()
