## TODO

- link email to my website and direct all emails there instead of school email
- figure out how to call populate_data management command using client's credentials.json
- use regex or small language model to filter internship/job applications
- design a way to get the importance of a job, maybe an api that gets size of company
- create a frontend with dashboard
- google oauth
- add docker files for frontend and backend for docker compose

## NOTES

- right now i have relational models in my local sqlite db
- to populate a new user my local db, i made create_user management command (frontend will come later)
- to populate new emails, i made populate_data management command but it needs either an existing json file or credentials.json (is this possible?)
- currently, my populate_data management command currently takes an optional JSON file that is list of emails OR if a json file is not specified it will try to fetch emails from GMAIL API but it doesnt have access to the credentials.json or tokens.json 
- **idea**: try to make another management command that lets user enter the credentials.json that will encrypt the secret into the database model -> no need for development, GMAIL_CREDENTIALS_PATH to .env