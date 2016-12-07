'''
Module to add users to database (for admin functions) outside of site interface
'''

from base64 import b64encode, b64decode
from app import db, models


import os
from fastpbkdf2 import pbkdf2_hmac

firstusername = raw_input('Enter the user name: ')
firstpw = raw_input('Enter password: ')


firstsalt = os.urandom(24)


firsthash = pbkdf2_hmac('sha512', firstpw, firstsalt, 100000)
firsthash = b64encode(firsthash)

print '****Initial values****'
print firstusername, type(firstusername)
print firstsalt, type(firstsalt)
print b64encode(firstsalt)
print firsthash, type(firsthash)


firstuser = models.user(
	username = firstusername,
	hashed_pw = firsthash,
	salt = b64encode(firstsalt))

db.session.add(firstuser)
print '****Committing****'
db.session.commit()
