#!/bin/bash

cd backend
rm -f ../backend_dist.zip
zip -r ../backend_dist.zip . -x "venv/*" ".venv/*" "*/__pycache__/*" ".git/*" ".DS_Store" ".ruff_cache/*" ".env.example"
cd ..
eb deploy django-env
eb status django-env