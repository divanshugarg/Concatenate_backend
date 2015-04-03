from django.shortcuts import render
import init_server
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
# Create your views here.

#subscribe user to listen to its activities
@csrf_exempt
def subscribeUser(request):
    print "hello"
    user_id = request.body
    print user_id
    init_server.subscribe_user_to_channel(user_id)
    return HttpResponse("Done", content_type='text/html')

# invite a user id from senders id via host game
def inviteFriend(request=None):
    x = 1

# accept a join game request for user id
def acceptInvite(request=None):
    x = 1

# send a game word from one channel to another
def gameWordSend(request=None):
    x = 1

# end a game because of timeout or wrong word
def endGameRequest(request=None):
    x = 1

# end a invite request because of timeout or cancel by sender
def endInviteRequest(request=None):
    x = 1
