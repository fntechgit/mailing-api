# Virtual Env

````bash
$ python3.6 -m venv env

$ source env/bin/activate
````
# Generate Secret Key

````bash
$ base64 /dev/urandom | head -c50
````

# Install reqs

````
pip install -r requirements.txt 

pip freeze > requirements.txt

pip install gunicorn psycopg2-binary

python manage.py makemigrations

python manage.py migrate
````

https://docs.djangoproject.com/en/3.0/topics/migrations/

# OpenAPI DOC

http://BASE_URL/openapi?format=openapi-json

# create super user

python manage.py createsuperuser


# static files

see https://docs.djangoproject.com/en/3.0/howto/static-files/deployment

````
$ python manage.py  collectstatic
````

# locale

django-admin makemessages -l es
django-admin compilemessages

# dev server

python manage.py runserver

# kill debug process

sudo lsof -t -i tcp:8000 | xargs kill -9

# dump data 
 
python manage.py dumpdata api.MailTemplate --indent 4 --format json > api/fixtures/mailtemplates.json
 
python manage.py loaddata mailtemplates.json
 
# run job

python manage.py runjob send_emails_job

# DB permissions

```
GRANT SUPER ON *.* TO 'fnopen_mailing_api_dev_user'@'172.16.1.%';
FLUSH PRIVILEGES;
```

# VCS Integration ( GITHUB )

we need to create a new github app here

https://github.com/organizations/fntechgit/settings/apps/new

see https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/about-creating-github-apps

and 

1. Generate a new private key
2. set the proper repositories permissions ( Content [read/write])
3. install org wide the new app
4. APP ID  and private key ( encoded on B64) should be provide on .env file using vars
   GITHUB_APP_ID
   GITHUB_APP_PRIVATE_KEY


