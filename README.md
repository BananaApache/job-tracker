
# job-tracker

## About

A django based backend for keeping track of your job/internship applications through connecting to the GMAIL API.

## Development Setup

1. Clone the repository
2. Install `uv` if you haven't already, see here for more details: [Installing uv](https://docs.astral.sh/uv/getting-started/installation/): 
3. Install dependencies and set up pre-commit hooks:
```bash
make setup
```
4. Setup your `backend/.env` based on the `backend/.env.example`

## Gmail API

1. [Create a Google Cloud project here](https://developers.google.com/workspace/guides/create-project)

This is needed to be able to connect to the Gmail API.

## (OPTIONAL) Populate database

1. Create your user:
```bash
cd backend
uv run manage.py create_user --email your_email@example.com
```

2. Create a sample json file with 100 emails
```bash
cd backend/scripts
uv run fetch_mail.py
```

3. Populate database from sample json file
```bash
cd backend
uv run manage.py populate_data --file scripts/sample.json
```

## Start local server

1. To start local django backend:
```bash
cd backend
uv run manage.py runserver
```

2. Navigate to `http://127.0.0.1:8000/admin`
