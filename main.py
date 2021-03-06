import threading
import csv
import pxssh
import matplotlib.pyplot as plt
import time
import threshold
import mail1
import math
import numpy
import sys
import writecsv
import datainitialize
count=mail1.getcount()
c1,c2,c3=0,0,0
duration=mail1.getduration()
currenttime1,currenttime2=time.time(),time.time()
mail1sentdisc,mail1sentmemory,writtenheader=False,False,False
class Server(threading.Thread):
	def __init__(self,credentials):
		threading.Thread.__init__(self)
		self.hostname=credentials['hostname']
		self.username=credentials['username']
		self.password=credentials['password']
		self.version= credentials['version']  
		self.duration=credentials['duration'] 
		self.s=pxssh.pxssh()
		self.memory=[]
		self.cpu=[]
		self.disk=[]
		self.memoryfile=[]
		self.diskfile=[]
		self.cpufile=[]
		self.y1=0
		self.y2=0
		self.monitorcount=0
		self.downcount=0
		self.down=False
		try:
			self.s.login(self.hostname,self.username,self.password)
		except:
			self.down=True
		self.serverdown={}
	def memorymonitor(self):
		if self.version=='rhel7':
			self.s.sendline(''' awk '/^Mem/ {printf("%u%%", ($3/$2)*100);}' <(free -m) ''')
		else:
			self.s.sendline(''' awk '/^Mem/ {printf("%u%%", ($3/$2)*100);}' <(free -m) ''')
		self.s.prompt()
		self.memory.append((int(self.s.before[-3:-1])))
		self.memoryfile.extend([{'time':time.ctime(time.time())},{'memory':self.memory[-1]}])
		global writtenheader
		'''if not writtenheader:
			writecsv.writeheader(self)
			writtenheader=True'''
		writecsv.memorywrite(self)
		del self.memory[:-1]
		self.memoryfile=[]
	def cpumonitor(self):
		self.s.sendline(' mpstat | grep all')
		self.s.prompt()
		self.cpu.append(100-float(self.s.before[-7:-2].decode('utf-8')))
		self.cpufile.extend([{'time':time.ctime(time.time())},{'cpu':self.cpu[-1]}])
		writecsv.cpuwrite(self)
		del self.cpu[:-1]
		self.cpufile=[] 
	def diskmonitor(self):
		self.s.sendline(''' awk '/^total/ {printf("%u%%", $5);}' <(df -h --total) ''')
		self.s.prompt()
		self.disk.append((int(self.s.before[-3:-1])))
		self.diskfile.extend([{'time':time.ctime(time.time())},{'disk':self.disk[-1]}])
		writecsv.diskwrite(self)
		del self.disk[:-1]
		self.diskfile=[]
	def diskdata(self):
		hostname=self.hostname
		thresholdusage=threshold.diskthreshold(hostname)
		currentusage=self.disk[-1]
		string=""" Subject: Alert

		Disk usage alert for {} \n
		Current Disk usage = {}% \n Threshold = {}% \n Increase in limit = {}% 
		  """.format(hostname,currentusage,thresholdusage,(currentusage- thresholdusage))
		return string
	def memorydata(self):
		hostname=self.hostname
		thresholdusage=threshold.memorythreshold(hostname)
		currentusage=self.memory[-1]
		string=""" Subject: Alert

		Memory usage alert for {} \n
		Current Memory usage = {}% \n Threshold = {}% \n Increase in limit = {}% 
		  """.format(hostname,currentusage,thresholdusage,(currentusage- thresholdusage))
		return string

	def cpudata(self):
		hostname=self.hostname
		thresholdusage=threshold.cputhreshold(hostname)
		currentusage=self.cpu[-1]
		string=""" Subject: Alert

		CPU usage alert for {} \n
		Current CPU usage = {}% \n Threshold = {}% \n Increase in limit = {}% 
		  """.format(hostname,currentusage,thresholdusage,(currentusage- thresholdusage))
		return string

	def monitor(self):
		#self.cpumonitor()
		if not self.down:
			self.memorymonitor()
			global mail1sentmemory,mail1sentdisc,c1,c2,count,currenttime1,currenttime2,duration,c3
			if threshold.memorythreshold(self.hostname)<self.memory[-1]:
				if  c2<count:
					if abs(time.time()-(currenttime1+duration*c2*60))<30:
						print('Sending memory alert to ',mail1.maillist)
						mail1.sendmessage(self.memorydata())
						c2+=1

			else:
				mail1sentmemory=True
				#print('Memory usage above thresholds')
			self.diskmonitor()
			if threshold.diskthreshold(self.hostname)<self.disk[-1]:
				if  c1<count:
					if abs(time.time()-(currenttime2+duration*c1*60))<30:
						print('Sending disk alert to ',mail1.maillist)
						mail1.sendmessage(self.diskdata())
						c1+=1
			else:
				mail1sentdisc=True
			self.cpumonitor()
			if threshold.cputhreshold(self.hostname)<self.cpu[-1]:
				if  c3<count:
					if abs(time.time()-(currenttime2+duration*c3*60))<30:
						print('Sending cpu alert to ',mail1.maillist)
						mail1.sendmessage(self.cpudata())
						c3+=1
			time.sleep(1)
			
		else:
			print(self.hostname,'Server Down')
			self.serverdown[time.ctime(time.time())]=0
			self.monitorcount+=1
			self.downcount+=1
			try:
				self.s.login(self.hostname,self.username,self.password)
				self.down=False
			except:
				self.down=True
				time.sleep(1)
		#writecsv.downdata(self)
	def run(self):
			while True:
				print('Monitoring ',self.hostname)
				self.monitor()
				#self.showval()
			
	def showval(self):
		self.y1+=1
		self.y2+=1
		figure(1)
		scatter(self.y1,self.memory)
		figure(2)
		scatter(self.y2,self.disk)
		pause(0.05)
		while True:
			pause(0.05)
if __name__ == '__main__':
	f=open('serverdata.csv','r+')
	reader=csv.DictReader(f,delimiter=',')
	objects=[Server(line) for line in reader]
	for thread in objects:
		thread.start()



