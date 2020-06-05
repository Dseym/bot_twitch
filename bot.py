from twitchio.ext import commands
from datetime import datetime, timedelta
import requests
from multiprocessing import Process
import time

nickBot = "" # Ник бота
id_token = "" # ID клиента приложения
secret = "" # Секрет вашего приложения
channelName = "" # Канал, где будет работать бот

# Инициализация бота
bot = commands.Bot(
	irc_token="oauth:" + secret,
    client_id=id_token,
    nick=nickBot,
    prefix="!", # Префикс комманд (!test)
    initial_channels=[channelName]
)


nicks = set()

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


bot_mess = False

@bot.event
async def event_message(ctx):

	global bot_mess
	global nicks
	nick_auth = ctx.author.display_name
	color = ctx.author.tags["color"] if not ctx.author.tags["color"] == "" else "#2d8acc"
	time_mess = datetime.strftime(ctx.timestamp+timedelta(hours=5), "%d/%m %H:%M:%S")
	channel_name = ctx.channel.name
	bot_true = "(bot)" if bot_mess and nick_auth == "dsey" else ""
	print("#" + channel_name + "#" + nick_auth + ": " + ctx.content + ";")
	print("")
	mess = "<div style=\"background-color: #211d1d\">[" + time_mess + "]#" + channel_name + "# <span style=\"font-weight: bold\">" + bot_true + "<span style=\"color: " + color + "\">" + nick_auth + "</span>: <span style=\"color: white\">" + ctx.content + ";</span></span></div>"

	with open("log.html", "a") as log:
		log.write(mess + "\n")
	
	bot_mess = False
	
	await bot.handle_commands(ctx)
	word_list = ("когда стрим", "когда будет стрим", "кагда стрим", "кагда будет стрим", "когда будет стрым", "кагда будет стрым", "когда стрым", "кагда стрым", "када стрым", "кода стрым", "када стрим", "кода стрим", "када будет стрым", "кода будет стрым", "када будет стрим", "кода будет стрим", "когда будит стрим", "кагда будит стрим", "кагда будит стрым", "когда будит стрым")
	for word in word_list:
		if ctx.content.find(word) > -1:
			time.sleep(6)
			await ctx.channel.send("никто не знает, а еще есть группа Зака, если там ничего нового, то стрим, скорее всего, не будет ( https://vk.com/zakvielgroup )")
			bot_mess = True
	
	nicks = set()
	list_users = ctx.channel.chatters
	for nick in list_users:
		nicks.add(nick.name.strip())

	with open("users.txt", "w", encoding="UTF-8") as nick_in_file:
		for nick in nicks:
			print(nick, file=nick_in_file)
	
# Сколько времени человек подписан на канал
@bot.command(name="follow")
async def follow_date(ctx):
	
	global bot_mess
	channel = channelName
	headers = {'Client-ID': id_token, 'Authorization': 'Bearer ' + secret,}

	channel_id_GET = requests.get("https://api.twitch.tv/helix/users?login=" + channel, headers=headers)
	channel_id = str(channel_id_GET.json()["data"][0]["id"])
	
	response = requests.get('https://api.twitch.tv/helix/users/follows?from_id=' + str(ctx.author.tags["user-id"]) + "&to_id=" + channel_id, headers=headers)
	
	time.sleep(2)
	
	time_follow = response.json()["data"][0]["followed_at"]
	time_follow = datetime.strptime(time_follow, "%Y-%m-%dT%H:%M:%SZ")
	
	await ctx.channel.send("@" + ctx.author.name + ", подписался на канал - " + datetime.strftime(time_follow, "%H:%M:%S %d/%m/%Y"))
	
	bot_mess = True
	
# Сколько времени человек находится в чате
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
	
	bot_mess = True

# Старт бота
if __name__ == "__main__":
	bot.run()
