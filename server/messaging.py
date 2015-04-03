__author__ = 'divanshu'

import ortc

class Messaging:
    ortc_client = None
    def __init__(self):
        cluster_url = "http://ortc-developers.realtime.co/server/2.1"
        application_key = "NMRZDS"
        private_key = "HPr4bQwJUssL"
        authentication_token = "poll_token"

        def on_exception(sender, exception):
            print "exception: " + exception

        def on_connected(sender):
            print "connected"

        def on_subscribed(sender):
            print "subscribed"

        def on_authenticated(result, error):
            print "authenticated"
            self.ortc_client.connect(application_key, authentication_token)

        self.ortc_client = ortc.OrtcClient()
        self.ortc_client.cluster_url = cluster_url
        self.ortc_client.connection_metadata = 'concatenateGame'
        self.ortc_client.set_on_exception_callback(on_exception)
        self.ortc_client.set_on_connected_callback(on_connected)
        self.ortc_client.set_on_subscribed_callback(on_subscribed)

        self.ortc_client.connect(application_key, authentication_token)


def send(ortc_client,channel, message):
    ortc_client.send(channel, message)