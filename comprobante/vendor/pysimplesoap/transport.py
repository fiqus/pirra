#!/usr/bin/python
# -*- coding: latin-1 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"Pythonic simple SOAP Client implementation"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2008 Mariano Reingart"
__license__ = "LGPL 3.0"

TIMEOUT = 60

import logging

log = logging.getLogger(__name__)
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.WARNING)

#
# We store metadata about what available transport mechanisms we have available.
#
_http_connectors = {} # libname: classimpl mapping
_http_facilities = {} # functionalitylabel: [sequence of libname] mapping

class TransportBase:
    @classmethod
    def supports_feature(cls, feature_name):
        return cls._wrapper_name in _http_facilities[feature_name]

#
# httplib2 support.
#
try:
    import httplib2
except ImportError:
    TIMEOUT = None # timeout not supported by urllib2
    pass
else:
    class Httplib2Transport(httplib2.Http, TransportBase):
        _wrapper_version = "httplib2 %s" % httplib2.__version__
        _wrapper_name = 'httplib2'
        def __init__(self, timeout, proxy=None, cacert=None, sessions=False):
            ##httplib2.debuglevel=4
            kwargs = {}
            if proxy:
                import socks
                kwargs['proxy_info'] = httplib2.ProxyInfo(proxy_type=socks.PROXY_TYPE_HTTP, **proxy)
                print("using proxy", proxy)

            # set optional parameters according supported httplib2 version
            if httplib2.__version__ >= '0.3.0':
                kwargs['timeout'] = timeout
            if httplib2.__version__ >= '0.7.0':
                kwargs['disable_ssl_certificate_validation'] = cacert is None
                kwargs['ca_certs'] = cacert    
            httplib2.Http.__init__(self, **kwargs)

    _http_connectors['httplib2'] = Httplib2Transport
    _http_facilities.setdefault('proxy', []).append('httplib2')
    _http_facilities.setdefault('cacert', []).append('httplib2')

    import inspect
    if 'timeout' in inspect.getargspec(httplib2.Http.__init__)[0]:
        _http_facilities.setdefault('timeout', []).append('httplib2')

#
# urllib2 support.
#
import urllib.request, urllib.error, urllib.parse
class urllib2Transport(TransportBase):
    # _wrapper_version = "urllib2 %s" % urllib2.__version__
    _wrapper_name = 'urllib2' 
    def __init__(self, timeout=None, proxy=None, cacert=None, sessions=False):
        if (timeout is not None) and not self.supports_feature('timeout'):
            raise RuntimeError('timeout is not supported with urllib2 transport')
        if proxy:
            raise RuntimeError('proxy is not supported with urllib2 transport')
        if cacert:
            raise RuntimeError('cacert is not support with urllib2 transport')

        self.request_opener = urllib.request.urlopen
        if sessions:
            from http.cookiejar import CookieJar
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
            self.request_opener = opener.open
            
        self._timeout = timeout

    def request(self, url, method="GET", body=None, headers={}):
        req = urllib.request.Request(url, body, headers)
        try:
            f = self.request_opener(req, timeout=self._timeout)
        except urllib.error.HTTPError as f:
            if f.code != 500:
                raise
        return f.info(), f.read()

_http_connectors['urllib2'] = urllib2Transport
_http_facilities.setdefault('sessions', []).append('urllib2')

import sys
if sys.version_info >= (2,6):
    _http_facilities.setdefault('timeout', []).append('urllib2')
del sys

#
# pycurl support.
# experimental: pycurl seems faster + better proxy support (NTLM) + ssl features
#
try:
    import pycurl
except ImportError:
    pass
else:
    try:
        from io import StringIO
    except ImportError:
        from io import StringIO

    class pycurlTransport(TransportBase):
        _wrapper_version = pycurl.version
        _wrapper_name = 'pycurl'
        def __init__(self, timeout, proxy=None, cacert=None, sessions=False):
            self.timeout = timeout 
            self.proxy = proxy or {}
            self.cacert = cacert
               
        def request(self, url, method, body, headers):
            c = pycurl.Curl()
            c.setopt(pycurl.URL, str(url))
            if 'proxy_host' in self.proxy:
                c.setopt(pycurl.PROXY, self.proxy['proxy_host'])
            if 'proxy_port' in self.proxy:
                c.setopt(pycurl.PROXYPORT, self.proxy['proxy_port'])
            if 'proxy_user' in self.proxy:
                c.setopt(pycurl.PROXYUSERPWD, "%(proxy_user)s:%(proxy_pass)s" % self.proxy)
            self.buf = StringIO()
            c.setopt(pycurl.WRITEFUNCTION, self.buf.write)
            #c.setopt(pycurl.READFUNCTION, self.read)
            #self.body = StringIO(body)
            #c.setopt(pycurl.HEADERFUNCTION, self.header)
            if self.cacert:
                c.setopt(c.CAINFO, str(self.cacert)) 
            c.setopt(pycurl.SSL_VERIFYPEER, self.cacert and 1 or 0)
            c.setopt(pycurl.SSL_VERIFYHOST, self.cacert and 2 or 0)
            c.setopt(pycurl.CONNECTTIMEOUT, self.timeout/6) 
            c.setopt(pycurl.TIMEOUT, self.timeout)
            if method=='POST':
                c.setopt(pycurl.POST, 1)
                c.setopt(pycurl.POSTFIELDS, body)            
            if headers:
                hdrs = ['%s: %s' % (str(k), str(v)) for k, v in list(headers.items())]
                ##print hdrs
                c.setopt(pycurl.HTTPHEADER, hdrs)
            c.perform()
            ##print "pycurl perform..."
            c.close()
            return {}, self.buf.getvalue()

    _http_connectors['pycurl'] = pycurlTransport
    _http_facilities.setdefault('proxy', []).append('pycurl')
    _http_facilities.setdefault('cacert', []).append('pycurl')
    _http_facilities.setdefault('timeout', []).append('pycurl')


class DummyTransport:
    "Testing class to load a xml response"
    
    def __init__(self, xml_response):
        self.xml_response = xml_response
        
    def request(self, location, method, body, headers):
        if False:
            print(method, location)
            print(headers)
            print(body)
        return {}, self.xml_response


def get_http_wrapper(library=None, features=[]):
    # If we are asked for a specific library, return it.
    if library is not None:
        try:
            return _http_connectors[library]
        except KeyError:
            raise RuntimeError('%s transport is not available' % (library,))

    # If we haven't been asked for a specific feature either, then just return our favourite
    # implementation.
    if not features:
        return _http_connectors.get('httplib2', _http_connectors['urllib2'])

    # If we are asked for a connector which supports the given features, then we will
    # try that.
    current_candidates = list(_http_connectors.keys())
    new_candidates = []
    for feature in features:
        for candidate in current_candidates:
            if candidate in _http_facilities.get(feature, []):
                new_candidates.append(candidate)
        current_candidates = new_candidates
        new_candidates = []

    # Return the first candidate in the list.
    try:
        candidate_name = current_candidates[0]
    except IndexError:
        raise RuntimeError("no transport available which supports these features: %s" % (features,))
    else:
        return _http_connectors[candidate_name]

def set_http_wrapper(library=None, features=[]):
    "Set a suitable HTTP connection wrapper."
    global Http
    Http = get_http_wrapper(library, features)
    return Http


def get_Http():
    "Return current transport class"
    global Http
    return Http

    
# define the default HTTP connection class (it can be changed at runtime!):
set_http_wrapper()


