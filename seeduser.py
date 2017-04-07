'''
Module to add users to database (for admin functions) outside of site interface
'''

from base64 import b64encode, b64decode
from app import db, models


import os, getpass
from fastpbkdf2 import pbkdf2_hmac

firstusername = ''
firstpw = 'a'
firstpw_II = 'b'

while (firstusername == '') or (firstpw != firstpw_II):
	firstusername = raw_input('Enter the user name: \n')

	#check to see if username already exists
	usernametest = models.user.query.filter_by(username=firstusername).first()
	if usernametest != None:
		print 'Username taken.  Please select a different name.'
		continue

	firstpw = getpass.getpass('Enter password: \n')
	firstpw_II = getpass.getpass('Enter password again: \n')

	if firstusername == '':
		print('Please enter a username.')
	if firstpw != firstpw_II:
		print('Password must match itself. Please try again.')

firstsalt = os.urandom(24)


firsthash = pbkdf2_hmac('sha512', firstpw, firstsalt, 100000)
firsthash = b64encode(firsthash)



firstuser = models.user(
	username = firstusername,
	hashed_pw = firsthash,
	salt = b64encode(firstsalt))

db.session.add(firstuser)
print '****Committing****'
db.session.commit()
