#!/usr/bin/env python3
import pyrebase
import sys
import time
import select
import signal
import requests
import os
from requests import Session
from requests.exceptions import HTTPError



def exit_app():
	global my_stream
	global db
	global uid
	global uuid
	global user
	if (my_stream!=None):
		#update last connection
		try:
			db.child("users").child(uid).child("devices").child(uuid).child("DT").update({"connected": "False","last_connection":time.asctime()},user['idToken'])
		except HTTPError as e:
			#data lost
			nop=1
		except:
			print("Unknown error",file=sys.stderr)

		my_stream.close()
		my_stream=None

def signal_handler(signal, frame):
	exit_app()
	sys.exit(0)


def stream_handler(message):
	global my_stream
	global last_cmd
	#callback for REST streaming
	#print(message["event"],file=sys.stderr) # put   patch (update)    null event (keepalive do nothing)  auth_revoked (close it)
	#print(message["path"],file=sys.stderr) # /-K7yGTTEp7O549EzTYtI
	#print(message["data"],file=sys.stderr) # {'title': 'Pyrebase', "body": "etc..."}   dict of data
	#print(str(message),file=sys.stderr)
	if (("put" in message["event"])or("patch" in message["event"])):
		# ignore the cnt for now, nothing to do if lost
		#    could perhaps flag error to cloud??
		# write to stdout
		if ("commandToRecv" in message["path"]):
			if (message["data"]!=last_cmd):
				print(message["data"],flush=True)
				last_cmd = message["data"];
		elif ("RecvCnt" in message["path"]):
			#ignore this
			nop=1
		else:
			if (message["data"]["commandToRecv"]!=last_cmd):
				print(message["data"]["commandToRecv"],flush=True)
				last_cmd = message["data"]["commandToRecv"];
	elif ("auth_revoked" in message["event"]):
		print("Stream not authorized",file=sys.stderr)
		my_stream.close()
		my_stream=None

#----------------------------------------------------------------------------------------------------

sys.stderr = open('/var/log/fb.log', 'a+')

email = sys.argv[1]
password = sys.argv[2]
uuid = sys.argv[3]

config = {
    "apiKey": "AIzaSyC15sCkx5ROi8NSg9NTsD-rNB8o0BTe92A",
    "authDomain": "netplay-429de.firebaseapp.com",
    "databaseURL": "https://netplay-429de.firebaseio.com",
    "projectId": "netplay-429de",
    "storageBucket": "netplay-429de.appspot.com",
}

signal.signal(signal.SIGINT, signal_handler)    # exit gracefully

firebase = pyrebase.initialize_app(config)

# Get a reference to the auth service
auth = firebase.auth()
db = firebase.database()

last_auth=-1
db_init=-1
loop_var=1
my_stream=None
uid = ""
last_cmd = ""

#remove buffering from in/out
#sys.stdin = sys.stdin.detach()
#sys.stdout = sys.stdout.detach()

#---------------------------------------
# main loop
while loop_var>0:

	print("loop time ",time.monotonic()-last_auth,file=sys.stderr)
	if ((last_auth>0)and(time.monotonic()-last_auth>2800)):
	# if need to reauth, do so
	#  if fail, set not auth 
		try:
			if (my_stream!=None):
				my_stream.close()
				my_stream=None
		except AttributeError as e:
			print("close failed ",e,file=sys.stderr)
		except:
			print("close failed ",file=sys.stderr)
		try:
			user = auth.refresh(user['refreshToken'])
			last_auth = time.monotonic()
			print("reauth success",file=sys.stderr)
		except:
			print("reauth failed",file=sys.stderr)
			last_auth=-1
			user=None


	# login
	#  if fail with bad user/password, exit
	#    else retry 
	# Log the user in
	if (last_auth<0):
		try:
			user = auth.sign_in_with_email_and_password(email, password)
			uid = user["localId"]
			last_auth = time.monotonic()
			print("auth success ",user["expiresIn"],file=sys.stderr)
		except HTTPError as e:
			if (("EMAIL_NOT_FOUND" in str(e))or("INVALID_PASSWORD" in str(e))):
				user = None
				loop_var=0
				print("Bad credentials",file=sys.stderr)
			else:
				user = None
				print("Login fail ",e,file=sys.stderr)
		except:
			print("Login fail ",file=sys.stderr)
			user = None

	# init database
	if ((user != None) and (my_stream==None) and (db_init<0)):
		#init DB connection
		addnew=False
		try:
			#devs = db.child("users").child(uid).child("devices").get(user['idToken'])
			devs = db.child("users").child(uid).child("devices").shallow().get(user['idToken'])
			#print(devs.val(),file=sys.stderr)
			if (uuid in str(devs.val())):
				addnew=False
			else:
				addnew=True

			db_init=1;
		except:
			addnew=True
		if (addnew):
			print("Device NOT FOUND!! Will exit!",file=sys.stderr)
			loop_var=0

	#open stream and set stream handler
	if ((my_stream==None)and(loop_var>0)):
		try:
			db.child("users").child(uid).child("devices").child(uuid).child("DT").update({"connected": "True","last_connection":time.asctime()},user['idToken'])
			my_stream = db.child("users").child(uid).child("devices").child(uuid).child("RX").stream(stream_handler,user['idToken'])
		except:
			my_stream = None
			print("Could not open stream",file=sys.stderr)


	# select on STDIN
	#   if running from CLI, STDIN will always show readable then BLOCK
 	#    needs to be run piped from another program
	#    when ready, wait .2 sec for full message then read and send it
	if (loop_var>0):
		#read_list = [sys.stdin]		#stdin is fd 0
		read_list = [0]		#stdin is fd 0
		readable, writeable, err = select.select(read_list,[],[],180)    #select wait upto 3 min

		if (len(readable)>0):
			time.sleep(0.2)    #get complete message
			#print("reading now",file=sys.stderr)
			#data = sys.stdin.buffer.read()
			try:
				bdata = os.read(0,8196)
			except:
				print("Exception on data read",file=sys.stderr)
				bdata = None

			if (bdata):
				data = bdata.decode()
			else:
				# EOF or exception on read, exit
				print("STDIN closed, exiting",file=sys.stderr)
				exit_app()


			#print("read",data,file=sys.stderr)
			rc=0
			try:
				dt = db.child("users").child(uid).child("devices").child(uuid).child("TX").get(user['idToken'])
				#print(str(dt.val()),file=sys.stderr)
				#dt.val = {"commandToRecv" : "val", "RecvCnt" : "int"}
				rc = int(dt.val()["SendCnt"]) + 1
				#print("Current data",str(dt.val()),file=sys.stderr)
				data2 = {"commandToSend": data, "SendCnt": str(rc)}
				print(str(data2),file=sys.stderr)
				db.child("users").child(uid).child("devices").child(uuid).child("TX").update(data2,user['idToken'])
			except:
				#data lost	
				print("Could not update cloud ",data,file=sys.stderr)
				nop=1

	#loop

#---------------------------------------

exit_app()


