__author__ = 'divanshu'

import messaging
import time
import json

ortc_messenger = None
BASE_FOR_CHANNEL = "user_channel_"

def start():
    global ortc_messenger
    ortc_messenger = messaging.Messaging()

    while not ortc_messenger.ortc_client:
        time.sleep(1)
    while not ortc_messenger.ortc_client.is_connected:
        time.sleep(1)

    ortc_messenger.ortc_client.subscribe("demo_game",True,on_message)
    time.sleep(2)
    data = "{ \"typeFlag\": 1, \"fromUser\": \"divanshu\", \"toUser\": \"shubham\" }"
    ortc_messenger.ortc_client.send("demo_game",data)


def on_message(sender, channel, message):
    global ortc_messenger
    print 'Message received on ('+channel+'): ' + message
    data = json.loads(message)
    print data
    print data["typeFlag"]

    # invite other friend
    if data["typeFlag"] == 1:
        print data["fromUser"]
        print data["toUser"]

    # accept invite
    if data["typeFlag"] == 2:
        print data["fromUser"] # joining the game
        print data["toUser"] # hosted the game
        send_data = data
        send_data["typeFlag"] = 6
        ortc_messenger.ortc_client.send(get_channel_for_user(data["toUser"]),json.dumps(send_data))

    # invite request cancel
    if data["typeFlag"] == 3:
        print data["fromUser"]
        print data["toUser"]

    # invite accepted
    if data["typeFlag"] == 4:
        print data["fromUser"]
        print data["toUser"]

    # game word sent
    if data["typeFlag"] == 5:
        print data["fromUser"]
        print data["toUser"]
        print data["gameId"]
        print data["gameWord"]

    # game over request
    if data["typeFlag"] == 6:
        print data["fromUser"]
        print data["toUser"]
        print data["gameId"]
        print data["gameMessage"]

def subscribe_user_to_channel(user_id):
    global ortc_messenger
    ortc_messenger.ortc_client.subscribe(get_channel_for_user(user_id), True, on_message)

def get_channel_for_user(user_id):
    return BASE_FOR_CHANNEL + user_id




