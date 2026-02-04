
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

2. Create your client secret in a credentials.json and place them inside your project. Then place the path to the credentials.json file to your `.env`.

```
GMAIL_CREDENTIALS_PATH=/path/to/your/gmail_credentials.json
GMAIL_TOKEN_PATH=/path/to/your/gmail_token.json
```

This is needed to be able to connect to the Gmail API.

## Make migrations

1. Make migrations for Label, User, and JobEmail models which can be found in `backend/api/models.py`
```bash
cd backend
uv run manage.py makemigrations
uv run manage.py migrate
```

2. The `db.sqlite3` should be made under `backend/`

3. Make a super user to check models in django admin page:
```bash
cd backend
uv run manage.py createsuperuser
```

## Populate database

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
uv run manage.py populate_data --file scripts/sample.json --user user@example.com
```
OR newly scraped 100 emails from Gmail API
```bash
cd backend
uv run manage.py populate_data --user user@example.com
```
**Also make sure the micro local server port is not conflicting with your django settings port**

## Start local server

1. To start local django backend:
```bash
cd backend
uv run manage.py runserver
```

2. Navigate to `http://127.0.0.1:8000/admin`

