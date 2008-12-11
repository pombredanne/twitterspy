#!/usr/bin/env python
"""
Twisted Twitter interface.

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import time
import base64
import urllib

from twisted.python import log
from twisted.internet import reactor, defer
from twisted.web import client

import txml

BASE_URL="http://twitter.com"
SEARCH_URL="http://search.twitter.com/search.atom"

class Twitter(object):

    def __init__(self, user=None, passwd=None,
        base_url=BASE_URL, search_url=SEARCH_URL):

        self.base_url = BASE_URL
        self.search_Url = SEARCH_URL
        self.username = user
        self.password = passwd

    def __makeAuthHeader(self, headers=None):
        if not headers:
            headers = {}
        authorization = base64.encodestring('%s:%s'
            % (self.username, self.password))[:-1]
        headers['Authorization'] = "Basic %s" % authorization
        return headers

    def __urlencode(self, h):
        rv = []
        for k,v in h.iteritems():
            rv.append('%s=%s' %
                (urllib.quote(k.encode("utf-8")),
                urllib.quote(v.encode("utf-8"))))
        return '&'.join(rv)

    def __post(self, path, args={}):
        h = {'Content-Type': 'application/x-www-form-urlencoded'}
        return client.getPage((BASE_URL + "%s") % path, method='POST',
            postdata=self.__urlencode(args), headers=self.__makeAuthHeader(h))

    def __get(self, path, delegate, params={}):
        url = BASE_URL + path
        if params:
            url += '?' + self.__urlencode(params)
        return client.downloadPage(url, txml.Feed(delegate),
            headers=self.__makeAuthHeader())

    def verify_credentials(self):
        "Verify a user's credentials."
        return self.__post("/account/verify_credentials.xml")

    def __parsed_post(self, hdef, parser):
        deferred = defer.Deferred()
        hdef.addErrback(lambda e: deferred.errback(e))
        hdef.addCallback(lambda p: deferred.callback(parser(p)))
        return deferred

    def update(self, status):
        "Update your status.  Returns the ID of the new post."
        return self.__parsed_post(self.__post("/statuses/update.xml",
            {'status': status}), txml.parseUpdateResponse)

    def friends(self, delegate, params={}):
        """Get updates from friends.

        See search for example of how results are returned."""
        return self.__get("/statuses/friends_timeline.atom", delegate, params)

    def user_timeline(self, delegate, user=None, params={}):
        """Get the most recent updates for a user.

        If no user is specified, the statuses for the authenticating user are
        returned.

        See search for example of how results are returned."""
        if user:
            params['id'] = user
        return self.__get("/statuses/user_timeline.atom", delegate, params)

    def direct_messages(self, delegate, params={}):
        """Get direct messages for the authenticating user.

        See search for example of how results are returned."""
        return self.__get("/direct_messages.atom", delegate, params)

    def replies(self, delegate, params={}):
        """Get the most recent replies for the authenticating user.

        See search for example of how results are returned."""
        return self.__get("/statuses/replies.atom", delegate, params)

    def follow(self, user):
        """Follow the given user.

        Returns no useful data."""
        return self.__post('/friendships/create/%s.xml' % user)

    def leave(self, user):
        """Stop following the given user.

        Returns no useful data."""
        return self.__post('/friendships/destroy/%s.xml' % user)

    def list_friends(self, delegate, user=None, params=None):
        """Get the list of friends for a user.

        Calls the delegate with each user object found."""
        if user:
            url = BASE_URL + '/statuses/friends/' + user + '.xml'
        else:
            url = BASE_URL + '/statuses/friends.xml'
        if params:
            url += '?' + self.__urlencode(params)
        return client.downloadPage(url, txml.Users(delegate),
            headers=self.__makeAuthHeader())

    def list_followers(self, delegate, user=None, params=None):
        """Get the list of followers for a user.

        Calls the delegate with each user object found."""
        if user:
            url = BASE_URL + '/statuses/followers/' + user + '.xml'
        else:
            url = BASE_URL + '/statuses/followers.xml'
        if params:
            url += '?' + self.__urlencode(params)
        return client.downloadPage(url, txml.Users(delegate),
            headers=self.__makeAuthHeader())

    def search(self, query, delegate, args=None):
        """Perform a search query.

        Results are given one at a time to the delegate.  An example delegate
        may look like this:

        def exampleDelegate(entry):
            print entry.title"""
        if args is None:
            args = {}
        args['q'] = query
        return client.downloadPage(SEARCH_URL + '?' + self.__urlencode(args),
            txml.Feed(delegate))