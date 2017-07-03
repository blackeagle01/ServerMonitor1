import yagmail
import csv
import getpass
import sys
f=open('mail.csv','r+')
reader=csv.DictReader(f,delimiter=',')
password=getpass.getpass()
maillist=[]
for line in reader:
	maillist.append(line['mails'])
def getcount():
	return int(line['number'])
def getduration():
	return int(line['duration'])
def sendmessage(message):
	try:
		yag=yagmail.SMTP('tiku.harsh',password)
	except :
		print('Cannot login: \n Possible Reasons: \n 1. No network connection. \n 2. Incorrect username or password')
		sys.exit(1)
	yag.send(maillist,'alert',message)

if __name__=="__main__":
	sendmessage('message')