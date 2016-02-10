DESCRIPTION:
This is a flask powered website built for the Udacity Full Stack Web Development Menu App course
and web server final project.

The three functions of this webapp are:

1. Provide an interface and database for users to manage restaurants and their menus

2. Implement Oauth logins in order to protect user's restaurant creations

3. Compile JSON files to simplify data exports

###########################################
########## MY SETUP #######################
###########################################

i. This application is hosted on http://ec2-52-27-37-204.us-west-2.compute.amazonaws.com/

ii. The server's ip address for ssh login is 52.27.37.204 
ssh port is 2200

iii. I installed:
		Apache2
		mod_wsgi
		libpq-dev
		postgresql-9.4
		postgresql-contrib
		postgresql-server-dev-X.Y
		git
		python-setuptools
		python-pip
		psycopg2
		Flask
		virtualenv
		oauth2client
		Flask-SQLAlchemy

iv.  I referenced: 
		Stack Overflow - so many times
		https://discussions.udacity.com/t/markedly-underwhelming-and-potentially-wrong-resource-list-for-p5/8587
		http://killtheyak.com/use-postgresql-with-django-flask/
		https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps
		http://flask.pocoo.org/docs/0.10/quickstart/
		http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/
		http://modwsgi.readthedocs.org/en/develop/configuration-directives/WSGIDaemonProcess.html
		http://postgresql.org/docs/current/static
		http://ubuntuforums.org
		http://help.ubuntu.com/community
		https://discussions.udacity.com
		
###########################################
######## Running it yourself ##############
###########################################

--------------------------------------------------------------------------------------------------------
PREQUESITES:
To use this app Python, SqlAlchemy, Flask, and Oauth2client need to be installed on your computer.  
The digital ocean link in my references above is probably the most helpful start to running your server.

You could also install vagrant and run Udacity's virtual machine with all necessary modules already setup 
and ready to use:

https://www.udacity.com/wiki/ud197/install-vagrant

------------------------------------------------------------------------------------------------------
SETUP:
Once the necessary python modules are installed on your system the database needs to be set up.

First login to psql and create a database called restaurant.  You should also create a new postgresql Role 
for the Database restaurant in order to isolate permissions.  This user's name and password need to be
 entered in both database_setup.py and catalog.py where sqlalchemy is connecting to psql
 (look for create_engine('postgresql://...')

Once the database has been created and the correct connection information entered navigate to document
 root and type "python database_setup.py" for the one time database setup.

To run the server type "python final_project.py" and navigate to "http://localhost:5000" to start
 using the system
(The server also runs on "http://127.0.0.1:5000", but the linked OAuth authenticators only recognize 
login requests from localhost:5000)

IF you want to deploy the app on a server so that it is publicly visible this link will be your 
bestfriend: http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/
The OAUTH logins won't work for you so you will have to create your own google and facebook apps 
then whitelist your server in their settings and download their client secrets JSON files to replace 
the current ones.

-------------------------------------------------------------------------------------------------------
USE: 
You can begin creating restaurants and menus as soon as you've logged in with either google or facebook. 
 (There is also an option for Amazon that is not yet functional)
Once you've logged in a restaurant can be created from the restaurants home page, and then menu items 
can be added to the new restaurant. As long as you are the owner of a restaurant there will also be 
options to edit and delete menu items and restaurants.

If you want a JSON object that describes your restaurant there are three functions available:

1. /restaurant/JSON/                                  returns all restaurants and their id's

2. /restaurant/<restaurant_id>/menu/JSON              returns a specific restaurants menu

3. /restaurant/<restaurant_id>/menu/<menu id>/JSON    returns a specific menu item
--------------------------------------------------------------------------------------------------------



