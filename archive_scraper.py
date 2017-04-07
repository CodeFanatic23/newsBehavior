from bs4 import BeautifulSoup
import requests
import datetime
import lxml
import os
import time
from lxml import html
import pandas as pd
'''
	 the starting and ending dates are inclusive
'''
class Archive_Scraper:
	def __init__(self):
		print("#"*8+" Enter the details to scrape separated by SPACE.")
		sd,sm,sy=input("Enter starting day month year ").split(" ")
		ed,em,ey=input("Enter ending day month year ").split(" ")
		self.keyword=input("Enter company data to scrape -")
		self.sm=int(sm)
		self.sy=int(sy)
		self.em=int(em)
		self.ey=int(ey)
		self.sd=int(sd)
		self.ed=int(ed)
		w = int(input("Enter website to scrape\n1)Econ Time\n2)Reuters\n3)The Hindu\n4)NDTV\n5)BusinessLine\n"))
		if w == 1:
			print("Scraping from Economictimes")
			self.econ_times()
		if w == 2:
			print("Scraping from reuters")
			self.reuters()
		if w == 3:
			print("Scraping from thehindu")
			self.thehindu()
		if w == 4:
			print("Scraping from NDTV")
			self.ndtv()
		if w == 5:
			print("Scraping from BusinessLine")
			self.businessLine()
		else:
			print("Invalid choice")
	def generate_ym_pair(self,y,sm,em,need_zero):
		year_mon=[]
		for m in range(sm,em+1):
			if(m<10):
				if(need_zero):
					year_mon.append((y,"0"+str(m)))
				else:
					year_mon.append(y,str(m))
			else:
				year_mon.append((y,m))
		return year_mon

	def year_m(self,non_zero):
		year_month=[]
		for y in range(self.sy,self.ey+1):
			if(self.sy==self.ey):
					year_month.extend(self.generate_ym_pair(y,self.sm,self.em,non_zero))
			if(self.sy!=self.ey):
					if(y==self.sy):
						year_month.extend(self.generate_ym_pair(y,self.sm,12,non_zero))
					elif (y==self.ey):
						year_month.extend(self.generate_ym_pair(y,1,self.em))
					else:
						year_month.extend(self.generate_ym_pair(y,1,12))
		return year_month

	def scrape(self,url):
		#time.sleep(1)
		r = requests.get(url)
		print(url)
		a,b = url.split('//')
		soup = BeautifulSoup(r.content,"html.parser")
		s = ''
		#ndtv.com
		if b.startswith('ndtv'):
			date_data = soup.findAll('span',{"itemprop":'dateModified'})
			for i in date_data:
				s = i.get('content').split('T')[0]
				print("date",s)
		elif b.startswith('gadgets'):#gadgets.ndtv
			date_data = soup.find_all(class_='dtreviewed')
			for i in date_data:
				s = i.get_text().split('"')[0]
				s = s.split(" ")
				s  = s[0]+"-"+(s[1])[0:3]+"-"+s[2]
				print("date",s)
				#s = datetime.datetime.strptime(s, "%d %B %Y")
		elif b.startswith('auto'):
			date_data = soup.find_all(class_='article__pubdate')
			for i in date_data:
				s = i.get_text().split(" ")
				s[1] = s[1][:-1]
				s = s[1]+'-'+s[0]+'-'+s[2]
				print(s)
		else:
			date_data = soup.find_all(class_='ins_dateline') #profit.ndtv
			for i in date_data:
				s = i.get_text().split(':')[1]
				a = s.split(' ')
				s = a[2].split(',')
				s = s[0]+'-'+(a[1])[0:3]+'-'+a[3]
				#s = datetime.datetime.strptime(s, "%d-%B-%Y")
				print("date",s)
		
		return s
	def reuters(self):
		url="http://www.reuters.com/resources/archive/us/{year}{month}{date}.html"
		blacklist=['video','#top']
		collection=[]
		year_month=self.year_m(True)
		for year,month in year_month:
			print("Year " + str(year)," Month " +str(month))
			for d in range(self.sd,self.ed+1):
				print ("date "+str(d))
				if(d<10):
					d="0"+str(d)
				r=requests.get(url.format(year=year,month=month,date=d))
				if(r.status_code==200):
					b=BeautifulSoup(r.content,'html.parser')
					links=b.select('div > div > div > div > div > div > a')
					for link in links:
						if(not ([i for i in blacklist if link.get('href').find(i)!=-1])):
							if( link.get('href').find(self.keyword)!=-1):
								index=link.get('href').rfind('/')
								link="http://www.reuters.com/article"+link.get('href')[index:]
								collection.append((str(d)+"-"+str(month)+"-"+str(year),link))
						#else:
						#	print('blacklisted '+link.get('href'))
				else:
					print("Skipped "+r.content)
		
		
		print("Collected "+str(len(collection))+" urls for "+self.keyword)
		self.writeToFile(collection,"reutersArchive",self.keyword,self.sd,self.sm,self.sy)

	def econ_times(self):
		base_url="http://economictimes.indiatimes.com/archivelist/year-{year},month-{month},starttime-{start_t}.cms"
		start_time=36892
		start_date=datetime.date(self.sy,self.sm,self.sd)
		days=(start_date-datetime.date(2001,1,1)).days + start_time
		count_days=(datetime.date(self.ey,self.em,self.ed)-start_date).days+1
		collection=[]
		visit_url=''
		for day in range(count_days):
			date_diff=datetime.timedelta(day)
			final_date=date_diff+start_date
			print (final_date),
			visit_url=base_url.format(year=final_date.year,month=final_date.month,start_t=days+day)
			page=requests.get(visit_url)
			print(visit_url)
			xtree=html.fromstring(page.content)
			links=xtree.xpath("*//section[@id='pageContent']//li/a/@href")
			for link in links:
				if(link.find(self.keyword)!=-1):
					link='http://economictimes.indiatimes.com'+link
					collection.append((str(final_date.day)+'-'+str(final_date.month)+'-'+str(final_date.year),link))
		print("Collected "+str(len(collection))+" urls for "+self.keyword)
		self.writeToFile(collection,"econtimesArchive",self.keyword,self.sd,self.sm,self.sy)

	def thehindu(self):
		base_url="http://www.thehindu.com/archive/web/{year}/{month}/{day}/"
		year_month=self.year_m(True)
		start_date=datetime.date(self.sy,self.sm,self.sd)
		count_days=(datetime.date(self.ey,self.em,self.ed)-start_date).days+1
		for d in range(count_days):
			date_diff=datetime.timedelta(d)
			final_date=date_diff+start_date
			print (final_date),
			visit_url=base_url.format(year=final_date.year,month=final_date.month,day=final_date.day)
			# this webpage loads very slow and becomes unresponsive sometimes hence a timeout of None
			page=requests.get(visit_url,timeout=None)
			print(visit_url)
			xtree=html.fromstring(page.content)
			collection=[]
			links=xtree.xpath("*//ul[@class='archive-list']//a/@href")
			for link in links:
				if(link.find(self.keyword)!=-1):
					collection.append((str(final_date.day)+'-'+str(final_date.month)+'-'+str(final_date.year),link))
		print("Collected "+str(len(collection))+" urls for "+self.keyword)
		self.writeToFile(collection,"thehinduArchive",self.keyword,self.sd,self.sm,self.sy)

	def ndtv(self):
		base_url="http://archives.ndtv.com/articles/{year}-{month}.html"
		year_month=self.year_m(True)
		start_date=datetime.date(self.sy,self.sm,self.sd)
		end_date = datetime.date(self.ey,self.em,self.ed)
		collectionitc=[]
		collectionsun = []
		collectiontcs = []

		for d in range(start_date.year-int(self.ey) +1):
			print("Scraping for the year",start_date.year-d)
			try:
				for x in range(start_date.month,end_date.month+1):
					visit_url=base_url.format(year=start_date.year-d,month=str(x).zfill(2))
					page=requests.get(visit_url,timeout=None)
					print(visit_url)
					xtree=html.fromstring(page.content)
					
					links=xtree.xpath("//*[@id='main-content']/ul/li/a/@href")
					print(len(links))
					for link in links:
						if 'khabar.ndtv' in link or 'hi.ndtv' in link or 'hi.gadgets' in link or 'gadgets.ndtv' in link or 'food.ndtv' in link:
							continue
						if(link.find('-itc')!=-1 or link.find('itc-')!= -1):
							collectionitc.append(self.scrape(link)+'::'+link)
						if(link.find('-tcs')!=-1 or link.find('tcs-')!= -1):
							collectiontcs.append(self.scrape(link)+'::'+link)
						if(link.find('sun-pharma')!=-1):
							collectionsun.append(self.scrape(link)+'::'+link)
			except Exception as e:
				print(e)
				print("---------------------------------ERROR---------------------------------")
				print("---------------------------------ERROR---------------------------------")


			# print("Collected "+str(len(collection))+" urls for "+str(start_date.year-d)+self.keyword)
			self.writeToFile(collectionitc,"ndtvArchive",'itc',self.sd,self.sm,self.sy)
			self.writeToFile(collectionsun,"ndtvArchive",'sun-pharma',self.sd,self.sm,self.sy)
			self.writeToFile(collectiontcs,"ndtvArchive",'tcs',self.sd,self.sm,self.sy)

		

	def businessLine(self):
		base_url="http://www.thehindubusinessline.com/today/?date={date}"
		year_month=self.year_m(True)
		start_date=datetime.date(self.sy,self.sm,self.sd)
		end_date = datetime.date(self.sy,self.em,self.ed)
		print(start_date)
		print(end_date.year)
		
		collectionitc=[]
		collectionsun = []
		collectiontcs = []
		collectionon=[]
		collectionsbi = []
		collectionhd = []
		collectionmar = []
		for i in range(start_date.year-int(self.ey)+1):
			
			start_date=datetime.date(self.sy-i,self.sm,self.sd)
			end_date = datetime.date(self.sy-i,self.em,self.ed)
			daterange = pd.date_range(start_date, end_date)
			for d in daterange:
				try:
					d  = str(d).split(' ')[0]
					visit_url=base_url.format(date=d)
					page=requests.get(visit_url,timeout=None)
					print(visit_url)
					xtree=html.fromstring(page.content)
					
					links=xtree.xpath("//*[@id='printhide']//a/@href")
					print(len(links))
					for link in links:
						if(link.find('maruti')!=-1):
							print(link)
							collectionmar.append(str(datetime.datetime.strptime(d,'%Y-%m-%d').strftime('%d-%b-%Y'))+'::'+link)
						if(link.find('-itc')!=-1 or link.find('itc-')!= -1):
							print(link)
							collectionitc.append(str(datetime.datetime.strptime(d,'%Y-%m-%d').strftime('%d-%b-%Y'))+'::'+link)
						if(link.find('-tcs')!=-1 or link.find('tcs-')!= -1):
							print(link)
							collectiontcs.append(str(datetime.datetime.strptime(d,'%Y-%m-%d').strftime('%d-%b-%Y'))+'::'+link)
						if(link.find('sun-pharma')!=-1):
							print(link)
							collectionsun.append(str(datetime.datetime.strptime(d,'%Y-%m-%d').strftime('%d-%b-%Y'))+'::'+link)
						if(link.find('sbi')!=-1):
							print(link)
							collectionsbi.append(str(datetime.datetime.strptime(d,'%Y-%m-%d').strftime('%d-%b-%Y'))+'::'+link)
						if(link.find('hdfc')!=-1):
							print(link)
							collectionhd.append(str(datetime.datetime.strptime(d,'%Y-%m-%d').strftime('%d-%b-%Y'))+'::'+link)
						if(link.find('ongc')!=-1):
							print(link)
							collectionon.append(str(datetime.datetime.strptime(d,'%Y-%m-%d').strftime('%d-%b-%Y'))+'::'+link)
				except Exception as e:
					print(e)
					print("---------------------------------ERROR---------------------------------")
					print("---------------------------------ERROR---------------------------------")


				# print("Collected "+str(len(collection))+" urls for "+self.keyword)
			self.writeToFile(collectionmar,"businessLineArchive",'maruti suzuki',self.sd,self.sm,self.sy)
			self.writeToFile(collectionitc,"businessLineArchive",'itc',self.sd,self.sm,self.sy)
			self.writeToFile(collectionsun,"businessLineArchive",'sun-pharma',self.sd,self.sm,self.sy)
			self.writeToFile(collectiontcs,"businessLineArchive",'tcs',self.sd,self.sm,self.sy)
			self.writeToFile(collectionsbi,"businessLineArchive",'sbi',self.sd,self.sm,self.sy)
			self.writeToFile(collectionon,"businessLineArchive",'ongc',self.sd,self.sm,self.sy)
			self.writeToFile(collectionhd,"businessLineArchive",'hdfc',self.sd,self.sm,self.sy)
				
			

	def writeToFile(self,links,webp,company,date,month,year):
		BASE_PATH = os.path.dirname(os.path.abspath(__file__))
		try:
			os.makedirs(os.path.join(BASE_PATH,"links",company,'archive'))
		except Exception as e:
			pass
		
		f = open(os.path.join(BASE_PATH,"links",company,"archive","results_"+webp+"_"+company+"_"+str(date)+"_"+str(month)+"_"+str(year)+'.data'),'a+')
		for i in links:
			f.write(str(i)+"\n")
		f.close()

start=Archive_Scraper()