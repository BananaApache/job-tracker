    

# job-tracker

# About

A django based backend for keeping track of your job/internship applications by connecting to the GMAIL API.

# Development Setup

1. Clone the repository
2. Install `uv` if you haven't already, see here for more details: [Installing uv](https://docs.astral.sh/uv/getting-started/installation/):
3. Install dependencies and set up pre-commit hooks:

```bash
make setup
```

4. Setup your `backend/.env` based on the `backend/.env.example`

### Django Secret Key

1. Generate a random django secret key to put in your `.env`. This can be done with django or secrets package. 
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
# OR 
python -c 'import secrets; print(secrets.token_hex(50))'
```
2. Then place it in your `.env` like so:
```
SECRET_KEY=your-generated-key
```

### Gmail API

1. [Create a Google Cloud project here](https://developers.google.com/workspace/guides/create-project)
2. You have two options for your secrets file.

   1. (**Recommended method**) Activate your billing account for Google and setup a Secrets Manager, and create your secret. More info can be found [here](https://codelabs.developers.google.com/codelabs/secret-manager-python#0) 
   2. Or create your client secret in a `credentials.json` and place them inside your project. Then place the path to the `credentials.json` file to your `.env`. You can then delete that after you populate the database with a custom defined django admin management command. For more info on tokens and secrets, see [here](https://developers.google.com/workspace/guides/auth-overview)

```
GMAIL_CREDENTIALS_PATH=/path/to/your/gmail_credentials.json
```

This is needed to be able to connect to the Gmail API.

### Make migrations

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

### Populate database

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

OR newly scraped 1000 emails from Gmail API

```bash
cd backend
uv run manage.py populate_data --user user@example.com --maxResults 1000 --inbox-only
```

OR with custom specific queries

```bash
python manage.py populate_data --email user@example.com --maxResults 1000 --query "-category:promotions -category:social -category:updates -category:forums"
```

**Also make sure the micro local server port is not conflicting with your django settings port**

# Start local server

1. To start local django backend:

```bash
cd backend
uv run manage.py runserver
```

2. Navigate to `http://127.0.0.1:8000/admin`
