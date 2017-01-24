# armarium_public - Robbins Collection Manuscript Application
##Fresh Installation Instructions
##v.3.1, 14 December 2016

##Introduction
These instructions are for a clean installation and activation of the Robbins Collection manuscript application (Jordan Shedlock’s MIMS final project from 2016).  This is a Python Flask application using a SQLite3 database, running through an Apache2 server via WSGI.  This repository contains a clean version that can be easily cloned and installed.


##Stack and Requirements
The application has been tested on the following stack.  It is [currently deployed] (http://104.131.3.203/) on DigitalOcean.  
* Ubuntu 14.04.4 (also 14.04.5) (64-bit)
* Apache2
* Sqlite3
* Python 2.7

The following packages must be installed on Ubuntu (as detailed below):
* python-pip  
* python-dev  
* libapache2-mod-wsgi  
* build-essential  
* libffi-dev  
* libssl-dev  
* git  

The following Python libraries are required.  They can be installed using pip and the included requirements file (which will automatically install their dependencies).  
* Flask  
* Werkzeug  
* Jinja2  
* Flask-SQLAlchemy  
* WTForms  
* BeautifulSoup  
* fastpbkdf2  


The application’s visualizations require the d3.js library, placed in the static folder and named d3.min.js .  This is already included in the GitHub repository.  

##Server creation and setup
The following instructions are tested on an Ubuntu 14.04.5 virtual machine hosted by Digital Ocean.  

After setting up a server or virtual machine of your preference, do the following:  

`apt-get update`  
`apt-get install apache2`  

At this point, you can add a static index.html file and check that server is working if desired.

Install Ubuntu dependencies:  
apt-get install python-pip python-dev libapache2-mod-wsgi build-essential libffi-dev libssl-dev git

Change directory to web folder and clone repository:  
`cd /var/www/`  
`git clone https://github.com/jtshed2016/armarium_public.git`


Edit __init__.py to add your own secret key.  This is required for the security of cookies (used for logging in to edit information).  Recommended method: in Python interpreter, enter the following lines and copy and paste the result into __init__.py.

`import os`  
`os.urandom(24)`  

Install Python dependencies:  
`pip –r install requirements.txt`  


Move armarium.conf  file to sites-available directory:  
`mv armarium.conf /etc/apache2/sites-available`


Enable mod_wsgi, if not already enabled:  
`a2enmod wsgi`

Enable the application (armarium) and disable the default site.  Reload server.  
`a2dissite 000-default`  
`a2ensite armarium`  
`service apache2 reload`  



At this point, the application should be functioning and available from the root of the domain.  

##Application Configuration and Maintenance

###New Users
In order to allow easy editing of manuscript information (e.g. to correct errant information from the automated ingestion, misspellings, etc.), the application includes “admin” pages where registered users can update information in the database.  These users must be logged in to access these.  New users can be added via the admin pages by existing users.  However, since no users are included in the database from the repository, the first user must be added using the `armarium_public/seeduser.py` script, which takes a username and password and creates a new record in the database.  

###Database

The installation in the repository includes a database (`armarium_public/app.db`) that is already populated with data for the 211 manuscripts in LawCat as of December 2016, as well as a number of “external works” (scholarly works using the Robbins manuscripts).  However, it is also possible to recreate the database using the `armarium_public/clear_and_update_database.py` script.  It is necessary to do this if any changes are made to the database model (`armarium_public/app/models.py`).  However, this will erase all information in the database.  This script will automatically repopulate the database, except for users and external works.  In order to avoid losing these data, one can use the `armarium_public/exdocs_backup.py` script to import and export external works/external docs data (after running the script from a command line, you will be given the choice of exporting current data to a new file, or importing data to a working database from an existing file.  
Prior to running this script, one can use the armarium_public/exdocs_backup.py script to export the external works to a separate file.  After the database has been recreated and repopulated, the same script can be used to retrieve the external works from this file and reinsert them into the database.  



