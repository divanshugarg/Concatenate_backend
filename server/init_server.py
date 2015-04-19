__author__ = 'divanshu'

import messaging
import time
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import enchant
import random
import numpy, bisect

ortc_messenger = None
BASE_FOR_CHANNEL = "user_channel_"

combined_words = []
start_words = []
bots = []

def start():
    global ortc_messenger
    with open('start_words.txt','r') as file:
        for line in file:
            for word in line.split():
                start_words.append(word.upper())
    print len(start_words)

    with open('combined.txt','r') as file:
        for line in file:
            for word in line.split():
                combined_words.append(word.upper())
    print len(combined_words)
    combined_words.sort()

    # print getRandomWord("ABSTRACT")

    ortc_messenger = messaging.Messaging()

    while not ortc_messenger.ortc_client:
        time.sleep(1)
    while not ortc_messenger.ortc_client.is_connected:
        time.sleep(1)


    with open('bots.txt','r') as file:
        for line in file:
            for bot in line.split():
                bots.append(bot)
                subscribe_user_to_channel(bot)
    print len(bots)

    # ortc_messenger.ortc_client.subscribe("host_game980030692009825",True,on_message)
    # time.sleep(2)
    # data = "{ \"typeFlag\": 1, \"fromUser\": \"divanshu\", \"toUser\": \"shubham\" }"
    # ortc_messenger.ortc_client.send("demo_game",data)
    #
    # # startGame("divanshu", "aman")

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
    if games[data["gameId"]].user_playing == data["userTurn"]:
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
    ortc_messenger.ortc_client.send(get_channel_for_user(data["toUser"]),json.dumps(data))


# BOT Game Play

@csrf_exempt
def getRandomWord(request):
    str = request.body
    strlen = len(request.body)
    len_suffix = min(int(numpy.random.exponential(2.0)+1.0), strlen)

    search_start = bisect.bisect_left(combined_words,str[-len_suffix:])
    search_end = bisect.bisect_right(combined_words,str[-len_suffix:-1] + chr(ord(str[strlen-1])+1))

    while search_end == search_start:
        len_suffix -= 1
        search_start = bisect.bisect_left(combined_words,str[-len_suffix:])
        search_end = bisect.bisect_right(combined_words,str[-len_suffix:-1] + chr(ord(str[strlen-1])+1))

    found = combined_words[random.randint(search_start,search_end-1)]
    return HttpResponse(found, content_type='text/html')

waiting_person = ""

@csrf_exempt
def addMeToWaitPool(request):
    global waiting_person
    # add the person to a pool or match to a waiting player
    if waiting_person != "":
        # add the waiting_for concept
        # startGame(waiting_person,request.body,False)
        data = {}
        data["typeFlag"] = 8
        data["fromUser"] = waiting_person
        data["toUser"] = request.body
        data["isBot"] = False
        sendOnBothChannels(data)
        waiting_person = ""
    else:
        waiting_person = request.body
    return HttpResponse("Done", content_type='text/html')

@csrf_exempt
def giveMeBot(request):
    global waiting_person
    if waiting_person == request.body:
        bot_id = random.choice(bots)
        data = {}
        data["typeFlag"] = 8
        data["fromUser"] = bot_id
        data["toUser"] = waiting_person
        data["isBot"] = True
        ortc_messenger.ortc_client.send(get_channel_for_user(waiting_person),json.dumps(data))
        # startGame(waiting_person,bot_id,True)
        waiting_person = ""
    return HttpResponse("Done", content_type='text/html')

@csrf_exempt
def startGameWithBot(request):
    data = json.loads(request.body)
    startGame(data["fromUser"], data["toUser"], True)
