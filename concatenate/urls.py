from django.conf.urls import patterns, include, url
from django.contrib import admin
import serverApi
import server.init_server

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'concatenate.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^subscribe_user/$', server.init_server.subscribeUser), # only this used until now. All others dummy
    url(r'^game_word_entered/$', server.init_server.gameWordEntered),
    # url(r'^invite/$', server.views.inviteFriend ),
    # url(r'^accept_invite/$', server.views.acceptInvite ),
    # url(r'^game_word_send/$', server.views.gameWordSend ),
    # url(r'^end_game_request/$', server.views.endGameRequest ),
    # url(r'^end_invite_request/$', server.views.endInviteRequest ),
)
