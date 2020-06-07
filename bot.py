from twitchio.ext import commands
from datetime import datetime, timedelta
from multiprocessing import Process
import random
import re
import requests
import time

nickBot = "" # Ник бота (ник аккаунта на котором стоит бот)
nickAdmin = "" # Ник администратора бота (оставьте пустым, если бот стоит на том же аккаунте, что используете и Вы)
id_token = "" # ID клиента приложения
secret = "" # Секрет вашего приложения без oauth:
channelName = "" # Канал, где будет работать бот

nicks = set()
gallows_start = False
towns_start = False

# Виселица
answer = ""
word = ""
errors = 0
verbs = set()

# Города
city = ""
cities = list()
last_verb = ""


if nickAdmin == "":
	nickAdmin = nickBot


# Инициализация бота
bot = commands.Bot(
	irc_token="oauth:" + secret,
    client_id=id_token,
    nick=nickBot,
    prefix="!", # Префикс комманд (!test)
    initial_channels=[channelName] )


def timer_chatting():
	time.sleep(60)

	with open("users.txt", "r", encoding="UTF-8") as nick_in_file:
		nicks = set(nick_in_file.read().split("\n"))


	with open("time.txt", "r", encoding="UTF-8") as file_read:
		file_content = file_read.readlines()
		nicks_file = []
		times = []

		for i in range(0, len(file_content)):
			nicks_file.append(file_content[i].split(":")[0].strip())
			times.append(file_content[i].split(":")[1].strip())


	with open("time.txt", "w", encoding="UTF-8") as chat_time:
		for nick in nicks:
			if not nick in nicks_file:
				nicks_file.append(nick)
				times.append("0")

		for i in range(0, len(nicks_file)):
			if nicks_file[i] in nicks:
				times[i] = str(int(times[i]) + 1)

			print(nicks_file[i] + ":" + times[i], file=chat_time)

	timer_chatting()


@bot.event
async def event_ready():
	print("Бот успешно запущен!")
	
	x = Process(target=timer_chatting)
	x.start()


@bot.event
async def event_message(ctx):

	global nicks
	nick_auth = ctx.author.display_name
	try:
		color = ctx.author.tags["color"] if not ctx.author.tags["color"] == "" else "#2d8acc"
	except:
		color = "#2d8acc"
	time_mess = datetime.strftime(ctx.timestamp+timedelta(hours=5), "%d/%m %H:%M:%S")
	channel_name = ctx.channel.name
	print("#" + channel_name + "#" + nick_auth + ": " + ctx.content + ";")
	print("")
	mess = "<div style=\"background-color: #211d1d\">[" + time_mess + "]#" + channel_name + "# <span style=\"font-weight: bold\">" + "<span style=\"color: " + color + "\">" + nick_auth + "</span>: <span style=\"color: white\">" + ctx.content + ";</span></span></div>"

	with open("log.html", "a") as log:
		log.write(mess + "\n")
	
	nicks = set()
	list_users = ctx.channel.chatters
	for nick in list_users:
		nicks.add(nick.name.strip())

	with open("users.txt", "w", encoding="UTF-8") as nick_in_file:
		for nick in nicks:
			print(nick, file=nick_in_file)
			
	nick = "@" + ctx.author.name
	# Игра города
	global city
	global last_verb
	global towns_start

	if "==" in ctx.content.lower() and towns_start and len(ctx.content.split(" ")) == 1:
		time.sleep(2)

		message = ctx.content.lower().split("==")[1]
		if message in cities:
			await ctx.channel.send(nick + ", город уже был назван")
		elif message[0].strip() == last_verb:
			list_city = open("words/towns.txt", "r", encoding="UTF-8").readlines()
			if not message.capitalize().strip() in "".join(list_city).split("\n"):
				await ctx.channel.send(nick + ", этого города нету в словаре")
				print("Нету в словаре: " + message)
				return

			city = message
			city = city.capitalize()

			cities.append(city.lower().strip())
			
			last_verb = city[-2] if city[-1] == "ь" else city[-1]
			
			await ctx.channel.send("Город " + city + " был назван " + nick + " следующий город на букву '" + last_verb + "'")
		else:
			await ctx.channel.send(nick + ", город на букву '" + last_verb + "'")

		time.sleep(5)
	
	
	# Игра виселица
	global errors
	global gallows_start
	verb = ctx.content.lower()[1]
	nick = ctx.author.name.lower()

	if "=" in ctx.content.lower() and gallows_start and len(ctx.content) == 2 and re.fullmatch("[а-я]", verb):
		# Проверяем написанную букву
		if verb in verbs:
			# Буква уже была
			await ctx.channel.send("@" + nick + ", буква уже проверена")
		elif ctx.content.lower()[1] in answer:
			# Буква угадана
			for i in range(0, len(answer)):
				if answer[i] == verb:
					word[i] = verb

			verbs.add(verb)

			await ctx.channel.send("@" + nick + ", буква '" + verb + "' - угадана: " + "".join(word))
		else:
			# Буква не угадана
			verbs.add(verb)

			errors += 1
			await ctx.channel.send("@" + nick + ", буква '" + verb + "' - не угадана, осталось попыток "+ str(6 - errors) +": " + "".join(word))

		time.sleep(2)

		# Условия поражения и победы
		if answer.strip() == ("".join(word)).strip():
			gameisstart = False
			await ctx.channel.send("Победа! Слово - " + answer)
		elif errors == 6:
			gameisstart = False
			await ctx.channel.send("Проигрыш! Слово - " + answer)


		time.sleep(5)
		
	await bot.handle_commands(ctx)


@bot.command(name="help")
async def command_help(ctx):
	await ctx.channel.send("@" + ctx.author.name + " Доступные команды: !time ник, !follow, !start игра (виселица, города), !stop игра (виселица, города)")


@bot.command(name="follow")
async def follow_date(ctx):
	
	try:
		channel = channelName
		headers = {'Client-ID': id_token, 'Authorization': 'Bearer ' + secret,}

		channel_id_GET = requests.get("https://api.twitch.tv/helix/users?login=" + channel, headers=headers)
		channel_id = str(channel_id_GET.json()["data"][0]["id"])
		
		response = requests.get('https://api.twitch.tv/helix/users/follows?from_id=' + str(ctx.author.tags["user-id"]) + "&to_id=" + channel_id, headers=headers)
		
		time.sleep(2)
		
		time_follow = response.json()["data"][0]["followed_at"]
		time_follow = datetime.strptime(time_follow, "%Y-%m-%dT%H:%M:%SZ")
		
		await ctx.channel.send("@" + ctx.author.name + ", подписался на канал - " + datetime.strftime(time_follow, "%H:%M:%S %d/%m/%Y"))
	except:
		await ctx.channel.send("@" + ctx.author.name + ", это Ваш канал")
	

@bot.command(name="time")
async def give_time_chatting(ctx):
	time.sleep(2)

	nick = ctx.author.name
	target = ctx.content.split(" ")[1] if len(ctx.content.split(" ")) > 1 else nick

	with open("time.txt", "r+", encoding="UTF-8") as file_read:
		file_content = file_read.readlines()
		nicks_file = []
		times = []

		for i in range(0, len(file_content)):
			nicks_file.append(file_content[i].split(":")[0].strip())
			times.append(file_content[i].split(":")[1].strip())
		
		if nick == target:
			if not nick in nicks_file:
				print(target + ":0", file=file_read)
				times.append("0")
			
			await ctx.channel.send("@" + nick + ", находится в чате - " + str(int(times[nicks_file.index(nick)])//60) + " часов " + str(int(times[nicks_file.index(nick)])%60) + " минут")
		else:
			if not target in nicks_file:
				await ctx.channel.send("@" + nick + ", такой пользователь не найден")
				return

			await ctx.channel.send("@" + nick + ", " + target + " находится в чате - " + str(int(times[nicks_file.index(target)])//60) + " часов " + str(int(times[nicks_file.index(target)])%60) + " минут")


@bot.command(name="start")
async def start_game(ctx, game):

	global gallows_start
	global towns_start
	
	time.sleep(2)

	# Проверка ника
	if not ctx.author.name == nickAdmin:
		return

	if game == "виселица":
	
		if gallows_start:
			return
		
		global answer
		global word
		global errors
		global verbs
		words = open("words/gallow.txt", "r", encoding="UTF-8").readlines()

		errors = 0
		verbs = set()
		answer = words[random.randint(0, len(words)-1)]
		word = list("_" * (len(answer)-1))

		print("Ответ: " + answer)
		
		await ctx.channel.send("Игра 'Виселица' началась, написать букву '=а' - Загадано слово " + "".join(word))
		
		gallows_start = True
	elif game == "города":
		
		if towns_start:
			return
		
		global city
		global cities
		global last_verb

		cities = list()
		list_city = open("words/towns.txt", "r", encoding="UTF-8").readlines()
		city = list_city[random.randint(0, len(list_city)-1)]
		cities.append(city.lower())

		last_verb = city[-3] if city[-2] == "ь" else city[-2]
		
		await ctx.channel.send("Игра 'Города' началась(=Кузнецк), первый город - " + city)

		time.sleep(5)
		
		towns_start = True
	else:
		await ctx.channel.send("@" + ctx.author.name + ", игры не существует")


@bot.command(name="stop")
async def stop_game(ctx, game):

	global gallows_start
	global towns_start

	if game == "виселица":
		
		if not gallows_start:
			return
			
		gallows_start = False
		await ctx.channel.send("Игра 'Виселица' закончилась")
	elif game == "города":
		
		if not towns_start:
			return
			
		towns_start = False
		await ctx.channel.send("Игра 'Города' закончилась")
	else:
		await ctx.channel.send("@" + ctx.author.name + ", игры не существует")
		

# Старт бота
if __name__ == "__main__":
	bot.run()
