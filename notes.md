## UPDATES

- added choice to use Google Secrets Manager
- adding djfernet fields for encrypting token, other cryptography packages don't work with django 6.0
- added saving authenticated tokens to a django model with encryption
- added subfolders for services and utils which both have helper functions used by management commands
- added clear emails for one specified user management command
- added batch calling for message.get to save requests
- added auto pagination support for my populate data management command
- added custom queries and label filters for populate data management command

## TODO

- find way to populate database once, sending 500 for a batch, allowing an option for how many emails to populate, an option for all emails
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
