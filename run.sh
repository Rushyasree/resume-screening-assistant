#!/usr/bin/env bash
set -euo pipefail

export FLASK_ENV="${FLASK_ENV:-development}"
export USE_WATSONX="${USE_WATSONX:-false}"
python backend/main.py
