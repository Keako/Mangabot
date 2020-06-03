from bs4 import BeautifulSoup
import requests as req
import telebot
import sqlite3
from telegraph import Telegraph
import lxml.html
import urllib.request
import os


bot_token='1182191112:AAEgX1OJpBk9Osl7frDKf-QiemJym0Vk7SY'
bot=telebot.TeleBot(bot_token)
telegraph_token='ab3a996c9eba6b2ec0c264e6a351f55fcdc07fb0ebe71910e02569ee7de4'


@bot.message_handler(content_types=['text'])
def start(message):
	if '/get' in message.text:
		sendNewChapter(message)
	elif '/add' in message.text:
##		bot.send_message(message.from_user.id, "Пришилите ссылку на мангу")
		addNewManga(message)
	elif '/info' in message.text:
		instruct='Если хотите прочитать главу, напишите боту "/get #ссылка".\nЕсли хотите добавить мангу, напишите "/add #ссылка"'
		bot.send_message(message.from_user.id, instruct)
	elif '/start' in message.text:
		instruct='Если хотите прочитать главу, напишите боту "/get #ссылка".\nЕсли хотите добавить мангу, напишите "/add #ссылка"'
		bot.send_message(message.from_user.id, instruct)
	elif '/check' in message.text:
		checkManga(message)
	elif '/chnew' in message.text:
		checkNewChapter()

def sendNewChapter(message):
	global bot
	html=''
	link=str(message.text)
	link=link.replace('/get ', '')
	my_request=urllib.request.Request(link)
	my_request.add_header('User-Agent', "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:24.0)\Gecko/20100101 Firefox/24.0")
	page=urllib.request.urlopen(my_request)
	text=page.read().decode(encoding="UTF-8")
	doc=lxml.html.document_fromstring(str(text))
	for element in doc.xpath("/html/body/div[6]/script[1]"):
		if element.text.find("rm_h.init") != -1:
			script_text=element.text
	script_line=script_text.split("rm_h.init")[1]
	script_line=script_line[3:-17]
	script_line=script_line[:-1].replace('[', '').split('],')
	links=[]
	for line in script_line:
		el=line.replace('"', r"'").replace("'", '')
		el=el.split(',')
		lnk=el[1] + el[0] + el[2]
		lnk=lnk.replace('https://h23.mangas.rocks/manga/','')
		links.append(lnk)
	telegraph=Telegraph(telegraph_token)
	for i in links:
		html=html + '<img src="' + i + '"/>'
	response=telegraph.create_page('Manga', html_content=html)
	bot.send_message(message.from_user.id, 'https://telegra.ph/{}'.format(response['path']))


def addNewManga(message):
	link=str(message.text)
	link=link.replace('/add ', '')
	response=req.get(link)
	soup=BeautifulSoup(response.text, 'lxml')
	name=str(soup.h1.span.text)
	db=sqlite3.connect("/root/NewManga/Manga.db")
	cur=db.cursor()
	sql="INSERT INTO manga VALUES('" + name + "','" + link + "','" + str(message.from_user.id) + "')"
	sql2="INSERT INTO chapter VALUES('" + link + "','" + str(message.from_user.id) + "','" + getChapter(link) + "')"
	cur.execute(sql)
	cur.execute(sql2)
	db.commit()
	db.close()

def checkManga(message):
	db=sqlite3.connect("/root/NewManga/Manga.db")
	cur=db.cursor()
	sql="SELECT * FROM manga WHERE user='" + str(message.from_user.id) + "'"
	cur.execute(sql)
	result=cur.fetchall()
	for manga in result:
		sql2="SELECT chapter FROM chapter WHERE link='" + manga[1] + "' AND user='" + str(message.from_user.id) + "'"
		cur.execute(sql2)
		chapter=cur.fetchone()
		chapt=str(chapter)
		chapt=chapt.replace("('","")
		chapt=chapt.replace("',)","")
		send=manga[0] + ' ' + chapt
		bot.send_message(message.from_user.id, send)
	db.close()


def checkNewChapter():
	db=sqlite3.connect("/root/NewManga/Manga.db")
	check=0
	cur=db.cursor()
	sql_urs='SELECT DISTINCT user FROM manga'
	cur.execute(sql_urs)
	users=cur.fetchall()
	for ui in users:
		for u in ui:
			check=0
			sql="SELECT link FROM manga"
			cur.execute(sql)
			result=cur.fetchall()
			sql2="SELECT name FROM manga"
			cur.execute(sql2)
			result2=cur.fetchall()
			for i in result:
				for j in i:
					chapter=getChapter(j)
					sql_chpt="SELECT chapter FROM chapter WHERE link='" + j + "' AND user='" + u + "'"
					#bot.send_message(u, sql_chpt)
					cur.execute(sql_chpt)
					res_ch=cur.fetchall()
					for ch in res_ch:
						for ch_ch in ch:
							if int(chapter) > int(ch_ch):
								snd='У манги "' + result2[check][0] + '" вышла ' + chapter + ' глава'
								bot.send_message(u, snd)
					send=result2[check][0] + ' ' + chapter
					check+=1	
					#print(send)
					#bot.send_message(u, send)
	db.close()


def getChapter(link):
	response=req.get(link)
	soup=BeautifulSoup(response.text, 'lxml')
	lnk=soup.h4.a['href']
	chapter=lnk.split('/')[3]
	return chapter


#270174742	


bot.polling()
