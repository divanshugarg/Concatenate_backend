__author__ = 'divanshu'

import server.init_server
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

@csrf_exempt
def subscribeUser(request):
    server.init_server.subscribe_user_to_channel(request.body)
    return HttpResponse("Done", content_type='text/html')