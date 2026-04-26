#!/usr/bin/env bash
set -e

pip install setuptools==68.0.0
pip install -r requirements.txt --no-build-isolation
