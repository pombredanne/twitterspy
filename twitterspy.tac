import sys
sys.path.insert(0,"lib/twitty-twister/lib")
sys.path.insert(0,"lib/wokkel")
sys.path.insert(0,"lib")

from twisted.application import service
from twisted.internet import task, reactor
from twisted.words.protocols.jabber import jid
from wokkel.client import XMPPClient
from wokkel.generic import VersionHandler
from wokkel.keepalive import KeepAlive
from wokkel.disco import DiscoHandler
import twitter

from twitterspy import config
from twitterspy import protocol
from twitterspy import xmpp_ping
from twitterspy import scheduling
from twitterspy import moodiness

# Set the user agent for twitter
twitter.Twitter.agent = "twitterspy"

application = service.Application("twitterspy")

xmppclient = XMPPClient(jid.internJID(config.SCREEN_NAME),
    config.CONF.get('xmpp', 'pass'))
xmppclient.logTraffic = False

# Stream handling protocols for twitterspy
protocols = [protocol.TwitterspyPresenceProtocol,
    protocol.TwitterspyMessageProtocol]

for p in protocols:
    handler=p()
    handler.setHandlerParent(xmppclient)

DiscoHandler().setHandlerParent(xmppclient)
VersionHandler('twitterspy', config.VERSION).setHandlerParent(xmppclient)
xmpp_ping.PingHandler().setHandlerParent(xmppclient)
KeepAlive().setHandlerParent(xmppclient)
xmppclient.setServiceParent(application)

task.LoopingCall(moodiness.moodiness).start(60)
