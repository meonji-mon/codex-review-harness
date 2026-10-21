#!/bin/bash
# Supplementary command check; does not execute inspected input.
/usr/bin/python3 -B "$(dirname "$0")/guard.py" git || {
  echo "Harness guard unavailable; command denied." >&2
  exit 2
}
