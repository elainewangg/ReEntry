# <a href="http://newera412.com/" target="_blank">NewERA412 Platform</a>

* Organization: RealisticReEntry
* Client Contact: <a href="mailto:bvbaseball42@gmail.com">`Taili Thompson`</a>
* Student Consultants: <a href="https://github.com/elainewangg">`Elaine Wang`</a>, <a href="https://github.com/adrienneli104">`Adrienne Li`</a>, and <a href="https://github.com/claricedu">`Clarice Du`</a>
* `See the GitHub Wiki for more important information`

### Application Versions

* `Python 3.6.6`
* `Django 3.0.2 final`
* `Twilio 6.38.0`
* See `requirements.txt` for a complete enumaration of package dependencies

***

# Production
To restart the app and server.
Do this when there are changes.
```
sudo systemctl restart gunicorn
sudo nginx -t && sudo systemctl restart nginx
```

### Dependency Setup (DEVELOPMENT)

##### LINUX Commands for people unfamiliar with django and linux 
*For Windows users*
If you are running on a fresh linux environment, you need to also install these following programs to setup the necessary dependency. 
* install necessary virtual environment program with command `sudo apt install python3-virtualenv`
* install python dev stuff with `sudo apt-get install python3-dev`
* Create the env: `virtualenv django_env` (set `django_env` to your preferred env name) 
* Start the env: `source django_env/bin/activate`
* Install all dependencies: `pip install -r requirements.txt`
* install postgres on your machine with `sudo apt install postgresql postgresql-contrib`
* with postgres installed, use this command `sudo service postgresql start` to start postgresql database
* in terminal, enter `sudo -u postgres psql`  to open postgresql console. you know ur in the console when u see `postgres=#`  at the front
* in the console, enter `CREATE USER taili WITH PASSWORD 'VeChain3d3$$';`  to create a new user taili
* in the console, enter `create database newera;`  to create a new database.
* in the console, enter `grant all privileges on database newera to taili;`  to give the privileges to user taili.
* in the console, enter `ALTER USER taili CREATEDB;` to provide additional necessary db creation privilege to user taili. After that, quit out console with `\q`
* in your terminal, enter `./manage.py makemigrations NewEra`  to make migration
* in your terminal, enter `./manage.py migrate`  to migrate
* in your terminal, enter `./manage.py collectstatic`  to generate static files
* in your terminal, enter `./manage.py test`  to run the test suite. Everything should pass.
* in your terminal, enter  `./manage.py runserver` , and then click on the link provided in terminal (something like http://127.0.0.1:8000/)

*For Mac users*
* install necessary virtual environment program with command `pip install virtualenv`
* install python dev stuff with `brew install python`
* Create the env: `virtualenv venv` (set `venv` to your preferred env name) 
* Start the env: `source venv/bin/activate`
* Install all dependencies: `pip install -r requirements.txt`
* install postgres on your machine with `brew install postgres`
* with postgres installed, use this command `brew services start postgresql` to start postgresql database
* in terminal, enter `psql postgres`  to open postgresql console. you know ur in the console when u see `postgres=#` at the front
* in the console, enter `CREATE USER taili WITH PASSWORD 'VeChain3d3$$';`  to create a new user taili
* in the console, enter `create database newera;`  to create a new database.
* in the console, enter `grant all privileges on database newera to taili;`  to give the privileges to user taili.
* in the console, enter `ALTER USER taili CREATEDB;` to provide additional necessary db creation privilege to user taili. After that, quit out console with `\q`
* in your terminal, enter `./manage.py makemigrations NewEra`  to make migration
* in your terminal, enter `./manage.py migrate`  to migrate
* in your terminal, enter `./manage.py collectstatic`  to generate static files
* in your terminal, enter `./manage.py test`  to run the test suite. Everything should pass.
* in your terminal, enter  `./manage.py runserver` , and then click on the link provided in terminal (something like http://127.0.0.1:8000/)
* To create an admin user, `./manage.py createsuperuser` 



###### First Time: 

The following will set up a python environment for the cloned project. This allows you to keep all your project dependencies (or `pip modules`) in isolation, and running their correct versions. 

* Create the env: `virtualenv django_env` (set `django_env` to your preferred env name) 
* Start the env: `source django_env/bin/activate`
* Install all dependencies: `pip install -r requirements.txt`
* Exit the env: `deactivate` or exit terminal 
* In settings.py, set: 
`ALLOWED_HOST = [“*”]`,`DEBUG = True `


###### De Futuro (important):  

* **After installing new python libraries to your pipenv, you must update the `requirements.txt` file**
* Do this by running `pip freeze > requirements.txt`

### Test Suite 

* Run the suite with `./manage.py test` (Only model tests are incuded)

### Included Scripts 

###### Populate (DEPRECATED)

* `python manage.py populate`
* And an admin (**is_superuser**): User(username='admin', password='admin')

###### Drop (DEPRECATED)

* `python manage.py drop`
* Destroys all user objects

###### Load Tags and Resources

* `python manage.py load_tags_and_resources`
* Loads the values and initial sets of tags and resources from a CSV ("Northside PD Service Providers.csv" in the root directory)
	* Loads a resource with a name, tag, website, contact name, contact position, phone number, fax number, contact email, address, city, state, zip code, second address line, and/or description, should they be provided
	* Tags are loaded with the resources
