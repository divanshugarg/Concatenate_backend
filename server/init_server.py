__author__ = 'divanshu'

import messaging
import time
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import enchant
import random

ortc_messenger = None
BASE_FOR_CHANNEL = "user_channel_"

start_words = []

def start():
    global ortc_messenger
    with open('combined.txt','r') as file:
        for line in file:
            for word in line.split():
                start_words.append(word.upper())
    print len(start_words)
    ortc_messenger = messaging.Messaging()

    while not ortc_messenger.ortc_client:
        time.sleep(1)
    while not ortc_messenger.ortc_client.is_connected:
        time.sleep(1)

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
            startGame(data["fromUser"],data["toUser"])
        else:
            # the waiting user will wait for 5-10 seconds, else opponent left.
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
        print data["gameWord"]
        # send a message to notify score and the winner to both the users!
        # unmap the gaming key-value pairs

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
    game = games[data["gameId"]]
    word = data["gameWord"]

    if data["fromUser"] == games[data["gameId"]].user_1:
        games[data["gameId"]].user_1_score = max(games[data["gameId"]].user_1_score, data["myScore"])
    if data["fromUser"] == games[data["gameId"]].user_2:
        games[data["gameId"]].user_2_score = max(games[data["gameId"]].user_2_score, data["myScore"])
    print str(games[data["gameId"]].user_1_score) + " " + str(games[data["gameId"]].user_2_score)

    games[data["gameId"]].last_word = word


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

def startGame(user_id_1,user_id_2):
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

    ortc_messenger.ortc_client.send(get_channel_for_user(data["toUser"]),json.dumps(data))
    data["fromUser"], data["toUser"] = data["toUser"], data["fromUser"]
    ortc_messenger.ortc_client.send(get_channel_for_user(data["toUser"]),json.dumps(data))

    return game

def getMaxPrefixMatchingSuffix(next_word,last_word):
    for idx in range(0,len(last_word)):
        if next_word.find(last_word[idx:]) == 0:
            return len(last_word) - idx
    return 0





