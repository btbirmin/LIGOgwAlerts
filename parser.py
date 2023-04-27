#pip install bs4
#pip install requests
#pip install mysql-connector
#pip install --upgrade setuptools
#pip install twilio
from bs4 import BeautifulSoup 	
import requests 	
import mysql.connector
import datetime
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from smtplib import SMTP
from twilio.rest import Client
import re
import os

def ligo():

	DEBUG = "true"

	mydb = mysql.connector.connect(host="localhost",user="root",passwd="ligo",database="ligo")
	mycursor = mydb.cursor()

	account_sid  = 'B555910248f7e33608e54433e2d78fb'
	auth_token  = 'd01372b17552a21fd1097444b5393547'
	client  = Client(account_sid, auth_token)
	myTwilioNumber = '+15556667777 '
	CellPhone1 = '+10000000000'
	CellPhone2 = '+10000000000'

	#track how long parser.py takes to run
	startTime = datetime.datetime.now()

	#headers = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
	url = "https://gracedb.ligo.org/latest/"
	r = requests.get(url)
	data = r.text
	soup = BeautifulSoup(data, "html.parser")
	
	table = soup.find_all('table')[1] 
	rows = table.find_all('tr')[1:]

	data = {
    'uid' : [],
    'labels' : [],
    't_start' : [],
    't_0' : [],
    't_end' : [],
    'far_hz' : [],
    'createddate' : []
	}

	for row in rows:
	    cols = row.find_all('td')
	    data['uid'].append( cols[0].get_text() )
	    data['labels'].append( cols[1].get_text() )
	    data['t_start'].append( cols[2].get_text() )
	    data['t_0'].append( cols[3].get_text() )
	    data['t_end'].append( cols[4].get_text() )
	    data['far_hz'].append( cols[5].get_text() )
	    data['createddate'].append( cols[6].get_text() )

	#print(len(data['uid']))    
	for i in range(0, len(data['uid'])):
		#debug print:
		#print(data['uid'][i])    
		#print(data['labels'][i])    
		#print(data['t_start'][i])    
		#print(data['t_0'][i])    
		#print(data['t_end'][i])    
		#print(data['far_hz'][i])    
		#print(data['createddate'][i])

		#fix labels column to all be on one line
		label_fixed = re.sub("\s+", ",", data['labels'][i].strip())

		#insert into mysql - use ignore to continue on if error arise due to primary key
		sql = "insert ignore into latestGWCandidates (uid, labels,t_start, t_0, t_end, far_hz, createddate, insertdate, acknowledged) VALUES (%s, %s, %s,%s, %s, %s,%s, %s, %s)"
		val = (data['uid'][i], label_fixed, data['t_start'][i], data['t_0'][i], data['t_end'][i], data['far_hz'][i], data['createddate'][i], datetime.datetime.now(), 'NO')
		mycursor.execute(sql, val)
		mydb.commit()

	#QUERY database for newly inserted gw candidates
	mycursor.execute("select * from latestGWCandidates where acknowledged = 'NO' order by insertdate asc")
	alert_results = mycursor.fetchall()

	uid_var = 0

	for i in alert_results:
		uid_var = i[0]
		label_var = i[1]
		t_start_var = i[2]
		t_0_var = i[3]
		t_end_var = i[4]
		far_hz_var = i[5]
		createddate_var = i[6]
		insertdate_var = i[7]
		acknowledged_var = i[8]
	
	#check if there is a new GW alert and if so continue below
	if uid_var != 0:
		
		email = 'example1@gmail.com'
		password = 'PASSWORD'
		send_to_emails = 'example1@gmail.com, example2@gmail.com, example3@gmail.com'
		#send_to_emails = 'btbirmin@gmail'
		subject = 'LIGO Alert! - New GW Candidate: '+ uid_var +'' # The subject line
		message = 'https://gracedb.ligo.org/superevents/'+uid_var+'/view/'

		msg = MIMEMultipart()
		msg['From'] = email
		msg['To'] = send_to_emails
		msg['Subject'] = subject
			
		 # Attach the message to the MIMEMultipart object
		msg.attach(MIMEText(message, 'plain'))

		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.starttls()
		server.login(email, password)
		text = msg.as_string() # You now need to convert the MIMEMultipart object to a string to send
		server.sendmail(email, msg["To"].split(","), text)
		server.quit()

		#after sending email - update latest candidate to acknowledged = 'YES' (aka email sent)
		mycursor.execute("update latestGWCandidates set acknowledged = 'YES'")
		mydb.commit()

		textMessageBody = 'LIGO ALERT - https://gracedb.ligo.org/superevents/'+uid_var+'/view/'
		textMessage = client.messages.create(body=textMessageBody, from_=myTwilioNumber, to=CellPhone1)
		textMessage = client.messages.create(body=textMessageBody, from_=myTwilioNumber, to=CellPhone2)


	#insert into mysql - use ignore to continue on if error arise due to primary key
	sql = "insert ignore into jobManager (jobName , lastRunstartTime ,lastRunEndTime) VALUES (%s, %s, %s)"
	val = ('parser.py', startTime, datetime.datetime.now())
	mycursor.execute(sql, val)
	mydb.commit()

ligo()
