#!/bin/bash
#
# Bootstrap virtualenv environment and postgres databases locally.
#
# NOTE: This script expects to be run from the project root with
# ./scripts/bootstrap.sh

set -eo pipefail

if [ ! $VIRTUAL_ENV ]; then
  virtualenv ./venv
  . ./venv/bin/activate
fi

# check pycurl version
echo "Checking pycurl version. Check ./README.md for installation steps."
python -c "import pycurl; print(pycurl.version)" | grep -i openssl

# Install Python development dependencies
pip3 install -r requirements_for_test.txt
