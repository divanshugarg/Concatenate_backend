__author__ = 'divanshu'

import server.init_server
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import enchant
import json
import server.init_server

dictionary = enchant.Dict("en_US")

@csrf_exempt
def subscribeUser(request):
    server.init_server.subscribe_user_to_channel(request.body)
    return HttpResponse("Done", content_type='text/html')

@csrf_exempt
def gameWordEntered(request):
    data = json.loads(request.body) # gameid, fromuser, touser, enteredword
    game = server.init_server.games[data["gameId"]]
    word = data["enteredWord"]
    is_present_in_dict = dictionary.check(word)
    common_part_with_last_word = getMaxPrefixMatchingSuffix(data["enteredWord"], game.last_word)
    # perform according to game over or not
    return HttpResponse("Done", content_type='text/html')

def getMaxPrefixMatchingSuffix(next_word,last_word):
    for idx in range(0,len(last_word)):
        if next_word.find(last_word[idx:]) == 0:
            return len(last_word) - idx
    return 0