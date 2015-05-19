__author__ = 'divanshu'

import messaging
import time
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import enchant
import random
import numpy, bisect
import MySQLdb
import Queue

ortc_messenger = None
db = None
BASE_FOR_CHANNEL = "user_channel_"

combined_words = []
start_words = []
bots = []

BASE_DIR = "/home/ubuntu/Concatenate_backend"

def start():
    global ortc_messenger
    global db

    # print getRandomWord("ABSTRACT")

    ortc_messenger = messaging.Messaging()

    while not ortc_messenger.ortc_client:
        time.sleep(1)
    while not ortc_messenger.ortc_client.is_connected:
        time.sleep(1)

    with open(BASE_DIR+'/start_words.txt','r') as file:
        for line in file:
            for word in line.split():
                start_words.append(word.upper())
    print len(start_words)

    with open(BASE_DIR+'/combined.txt','r') as file:
        for line in file:
            for word in line.split():
                if len(word) > 1:
                    combined_words.append(word.upper())
    print len(combined_words)
    combined_words.sort()

    # with open(BASE_DIR+'/bots.txt','r') as file:
    #     for line in file:
    #         for bot in line.split():
    #             bots.append(bot)
    #             subscribe_user_to_channel(bot)
    # print len(bots)

    db = MySQLdb.connect(host='localhost',
                         user='root',
                         passwd='root',
                         db='concaty')

    cur = db.cursor()
    cur.execute("SELECT * FROM bots")
    for row in cur.fetchall():
        bots.append(row[0])
        subscribe_user_to_channel(row[0])


waiting_for = {}

def on_message(sender, channel, message):
    global ortc_messenger
    print 'Message received on ('+channel+'): ' + message
    data = json.loads(message)
    print data
    print data["typeFlag"]

    # invite other friend
    if data["typeFlag"] == 1:
        print data["fromUser"] # hosted the game
        print data["toUser"] # joined the game

    # accept invite
    if data["typeFlag"] == 2:
        print data["fromUser"] # joining the game
        print data["toUser"] # hosted the game
        if data["toUser"] in waiting_for and waiting_for[data["toUser"]] == data["fromUser"]:
            # waiting_for[data["toUser"]] = ""
            startGame(data["fromUser"],data["toUser"],False)
        else:
            # the waiting user will wait for 15 seconds, else opponent left.
            # nowhere invaldiated for now. Might want to improve that.
            waiting_for[data["fromUser"]] = data["toUser"]

    # invite request cancel
    if data["typeFlag"] == 3:
        print data["fromUser"]
        print data["toUser"]

    # game started request - invite accepted to the person who is hosting
    if data["typeFlag"] == 4:
        print data["fromUser"]
        print data["toUser"]
        print data["gameId"]
        print data["gameWord"]
        print data["userTurn"]
        print data["isBot"]

    # game word sent
    if data["typeFlag"] == 5:
        print data["fromUser"]
        print data["toUser"]
        print data["gameId"]
        print data["gameWord"]
        print data["myScore"]
        processGameWord(data)

    # game over request
    if data["typeFlag"] == 6:
        print data["fromUser"]
        print data["toUser"]
        print data["gameId"]
        # send a message to notify score and the winner to both the users!
        # unmap the gaming key-value pairs
        # update score in db

    # word time over request
    if data["typeFlag"] == 7:
        print data["fromUser"]
        print data["toUser"]
        print data["gameId"]
        print data["userTurn"]
        sendGameOverRequest(data)

    # quick game matched two players
    if data["typeFlag"] == 8:
        print data["fromUser"]
        print data["toUser"]
        print data["fromUserScore"]
        print data["fromUserName"]
        print data["toUserScore"]
        print data["toUserName"]
        print data["isBot"]


def subscribe_user_to_channel(user_id):
    global ortc_messenger
    ortc_messenger.ortc_client.subscribe(get_channel_for_user(user_id), True, on_message)

def get_channel_for_user(user_id):
    return BASE_FOR_CHANNEL + user_id

# APIs exposed

dictionary = enchant.Dict("en_US")

@csrf_exempt
def subscribeUser(request):
    subscribe_user_to_channel(request.body)
    print "subscribing to : " + str(request.body)
    return HttpResponse("Done", content_type='text/html')

# not using in the present version
@csrf_exempt
def gameWordEntered(request):
    global games, ortc_messenger
    data = json.loads(request.body) # gameId, fromUser, toUser, gameWord
    game = games[data["gameId"]]
    word = data["gameWord"]
    is_present_in_dict = dictionary.check(word)
    common_part_with_last_word = getMaxPrefixMatchingSuffix(word, game.last_word)
    if not is_present_in_dict or word == game.last_word or common_part_with_last_word == 0:
        # Game over
        data["typeFlag"] = 6
        ortc_messenger.ortc_client.send(get_channel_for_user(data["toUser"]),json.dumps(data))
        ortc_messenger.ortc_client.send(get_channel_for_user(data["fromUser"]),json.dumps(data))
    else:
        data["typeFlag"] = 5
        # update score here
        ortc_messenger.ortc_client.send(get_channel_for_user(data["toUser"]),json.dumps(data))
        ortc_messenger.ortc_client.send(get_channel_for_user(data["fromUser"]),json.dumps(data))
    game.last_word = word
    return HttpResponse("Done", content_type='text/html')

# Game Play

def processGameWord(data):
    global games, ortc_messenger
    word = data["gameWord"]

    if data["fromUser"] == games[data["gameId"]].user_1:
        games[data["gameId"]].user_1_score = max(games[data["gameId"]].user_1_score, data["myScore"])
    if data["fromUser"] == games[data["gameId"]].user_2:
        games[data["gameId"]].user_2_score = max(games[data["gameId"]].user_2_score, data["myScore"])
    print str(games[data["gameId"]].user_1_score) + " " + str(games[data["gameId"]].user_2_score)

    games[data["gameId"]].last_word = word
    games[data["gameId"]].user_playing = data["toUser"]

def sendGameOverRequest(data):
    global games, ortc_messenger
    # if games[data["gameId"]].user_playing == data["userTurn"]:
    new_data = {}
    new_data["typeFlag"] = 6
    new_data["fromUser"] = data["fromUser"]
    new_data["toUser"] = data["toUser"]
    sendOnBothChannels(new_data)


class Game:
    def __init__(self,str):
        self.last_word = str
    user_1 = None
    user_2 = None
    last_word = "HELLO"
    user_1_score = 0
    user_2_score = 0
    user_playing = None

game_id = 0
games = {}
user_opponent = {}
user_game_id = {}

def startGame(user_id_1,user_id_2,isBot):
    global game, game_id, ortc_messenger
    game = Game(random.choice(start_words))
    game.user_1 = user_id_1
    game.user_2 = user_id_2
    game.user_playing = user_id_2 if random.getrandbits(1)==1  else user_id_1
    game_id += 1 # might want to make this thread safe
    games[game_id] = game
    user_opponent[user_id_1] = user_id_2
    user_opponent[user_id_2] = user_id_1
    user_game_id[user_id_1] = game_id
    user_game_id[user_id_2] = game_id

    data = {}
    data["typeFlag"] = 4
    data["fromUser"] = user_id_1
    data["toUser"] = user_id_2
    data["gameWord"] = game.last_word.upper()
    data["gameId"] = game_id
    data["userTurn"] = game.user_playing
    data["isBot"] = isBot

    sendOnBothChannels(data)

    return game

def getMaxPrefixMatchingSuffix(next_word,last_word):
    for idx in range(0,len(last_word)):
        if next_word.find(last_word[idx:]) == 0:
            return len(last_word) - idx
    return 0

def sendOnBothChannels(data):
    ortc_messenger.ortc_client.send(get_channel_for_user(data["toUser"]),json.dumps(data))
    data["fromUser"], data["toUser"] = data["toUser"], data["fromUser"]
    if "fromUserName" in data:
        data["fromUserName"], data["toUserName"] = data["toUserName"], data["fromUserName"]
        data["fromUserScore"], data["toUserScore"] = data["toUserScore"], data["fromUserScore"]
    ortc_messenger.ortc_client.send(get_channel_for_user(data["toUser"]),json.dumps(data))


# BOT Game Play

@csrf_exempt
def getRandomWord(request):
    str = request.body
    strlen = len(request.body)
    # Increasing the variable increases the difficulty of the bot
    len_suffix = min(int(numpy.random.exponential(1.8)+1.0), strlen)

    search_start = bisect.bisect_left(combined_words,str[-len_suffix:])
    search_end = bisect.bisect_right(combined_words,str[-len_suffix:-1] + chr(ord(str[strlen-1])+1))

    while search_end == search_start or (len_suffix == strlen and strlen > 1):
        len_suffix -= 1
        search_start = bisect.bisect_left(combined_words,str[-len_suffix:])
        search_end = bisect.bisect_right(combined_words,str[-len_suffix:-1] + chr(ord(str[strlen-1])+1))

    found = combined_words[random.randint(search_start,search_end-1)]
    return HttpResponse(found, content_type='text/html')

waiting_person = {"id": "", "time": 0, "name": "", "score": ""}

@csrf_exempt
def addMeToWaitPool(request):
    # request.body is a json with id, name, score
    request_data = json.loads(request.body)
    global waiting_person
    if waiting_person["id"] != "" and time.time() - waiting_person["time"] < 45:
        data = {}
        data["typeFlag"] = 8
        data["fromUser"] = waiting_person["id"]
        data["toUser"] = request_data["id"]
        data["fromUserName"] = waiting_person["name"]
        data["fromUserScore"] = waiting_person["score"]
        data["toUserName"] = request_data["name"]
        data["toUserScore"] = request_data["score"]
        data["isBot"] = False
        sendOnBothChannels(data)
        waiting_person["id"] = ""
    else:
        waiting_person["id"] = request_data["id"]
        waiting_person["name"] = request_data["name"]
        waiting_person["score"] = request_data["score"]
        waiting_person["time"] = time.time()

    return HttpResponse("Done", content_type='text/html')

def removeMeFromPool(request):
    global waiting_person
    if waiting_person["id"] == request.body:
        waiting_person["id"] = ""

@csrf_exempt
def giveMeBot(request):
    global db
    global waiting_person
    if waiting_person["id"] == request.body:
        bot_id = random.choice(bots)
        cur = db.cursor()
        cur.execute("SELECT * FROM bots WHERE id = '" + bot_id + "'")
        bot_details = cur.fetchone()
        data = {}
        data["typeFlag"] = 8
        data["fromUser"] = bot_id
        data["fromUserName"] = bot_details[1]
        data["fromUserScore"] = bot_details[2]
        data["toUser"] = waiting_person["id"]
        data["toUserName"] = waiting_person["name"]
        data["toUserScore"] = waiting_person["score"]
        data["isBot"] = True
        ortc_messenger.ortc_client.send(get_channel_for_user(waiting_person["id"]),json.dumps(data))
        # startGame(waiting_person,bot_id,True)
        waiting_person["id"] = ""
    return HttpResponse("Done", content_type='text/html')

@csrf_exempt
def startGameWithBot(request):
    data = json.loads(request.body)
    startGame(data["fromUser"], data["toUser"], True)
    return HttpResponse("Done", content_type='text/html')

@csrf_exempt
def updateScoreForBot(request):
    global db
    data = json.loads(request.body)
    bot_id = data["id"]
    score_increase = data["score"]
    cur = db.cursor()
    cur.execute("UPDATE bots SET score=score+" + score_increase + " WHERE id='" + bot_id + "'")
    print "Score updated for bot with id " + bot_id
    return HttpResponse("Done", content_type='text/html')
