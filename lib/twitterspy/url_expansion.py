import re

from twisted.internet import task, reactor, defer

import longurl

class Expander(object):

    def __init__(self):
        self.lu = longurl.LongUrl('twitterspy')
        self.regex = None

    def initialize(self):
        self.lu.getServices().addCallback(self._registerServices)

    def _registerServices(self, svcs):
        domains = set()
        for s in svcs.values():
            domains.update(s.domains)

        self.regex_str = "(http://(" + '|'.join(self.__fixup(d) for d in domains) + r")/\S+)"
        self.regex = re.compile(self.regex_str)

    def __fixup(self, d):
        return d.replace('.', r'\.')

    def expand(self, plain, html=None):
        rv = defer.Deferred()

        m = self.regex.search(plain)
        if m:
            u, k = m.groups()
            def gotErr(e):
                log.err(e)
                rv.callback((plain, html))
            def gotRes(res):
                plainSub = plain.replace(u, "%s (from %s)" % (res, u))
                if html:
                    htmlSub = html.replace(u, "%s" % (res,))
                else:
                    htmlSub = None
                rv.callback((plainSub, htmlSub))
            self.lu.expand(u).addErrback(gotErr).addCallback(gotRes)
        else:
            # No match, immediately hand the message back.
            def passThrough():
                rv.callback((plain, html))
            reactor.callWhenRunning(passThrough)

        return rv

expander = Expander()