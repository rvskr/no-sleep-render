#!/bin/bash
gunicorn -w $(($(nproc) - 1)) -b 0.0.0.0:8000 wsgi:app

