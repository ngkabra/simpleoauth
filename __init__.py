import httplib2
import oauth2
from simplejson import loads
from urllib import urlencode

class Error(Exception): pass
class ApiError(Error): pass

class Provider(object):
    def __init__(self,
                 url_base,
                 access_token_url,
                 authorization_url,
                 request_token_url='',
                 api_url_base=None, # defaults to url_base
                 api_extra_headers={},
                 default_auth_http_method='POST',
                 default_api_http_method='GET',
                 callback_for_request_token=None,
                 oauth_version='1',
                 default_data_type='json'):
        self.request_token_url = url_base + request_token_url
        self.access_token_url = url_base + access_token_url
        self.authorization_url = url_base + authorization_url

        self.api_url_base = api_url_base or url_base
        self.api_extra_headers = api_extra_headers
        self.auth_http_method = default_auth_http_method
        self.api_http_method = default_api_http_method

        self.callback_for_request_token = callback_for_request_token
        self.oauth_version = oauth_version
        self.default_data_type = default_data_type

    def __unicode__(self):
        return unicode(self.__dir__)

class Client(object):
    '''A simplified OAuth client

    Intended usage:
        provider = providers.twitter 
                           # see Provider docs for details of how to
                           # instantiate a provider
        consumer = (consumer_key, consumer_secret)
        access_token = get_access_token_if_exists(foobar)

        if not access_token:
          auth = Client(consumer, provider)
          tmp_token, url = auth.auth_part1(callback_url='http://example.com/callback/')
          request.session['tmp_token'] = tmp_token
          return HttpRedirect(url)
    '''

    def __init__(self, 
                 consumer,
                 provider,
                 access_token=None,
                 access_token_secret=None):
        self.provider = provider
        self.consumer = consumer
        self._is_version2 = provider.oauth_version == '2'

        if self._is_version2:
            self._client = oauth2.Client2(consumer[0], consumer[1],
                                          provider.authorization_url)
        else:
            self._client = oauth2.Client(oauth2.Consumer(consumer[0], 
                                                         consumer[1]))

        self._headers = provider.api_extra_headers.copy()
        self._data_type = provider.default_data_type
        self._extra_args = {}

        self.callback_url = len(consumer)==3 and consumer[2] or ''
                   # Take default callback_url from consumer tuple
                   # if it is specified, else ''

        if access_token:
            self.auth(access_token, access_token_secret)

    def _set_Token(self, token, verifier=None):
        self._client.token = token
        if verifier:
            self._client.token.verifier = verifier

    def auth_part1(self, callback_url=None):
        '''Returns (request_token, request_token_secret, auth_url)

        Basically, for OAuth version 1, this gets the temporary
        request_token and secret, and the authorization url. Caller
        is expected to store the request_token and secret, and
        then redirect the user to the auth_url. (The request_token
        and secret will be needed later when the callback comes
        from the provider, after verification).

        For OAuth version 2, the request_token and secret will be None
        and caller simply redirects user to the authorization url.
        '''
        if callback_url:
            self.callback_url = callback_url

        if self._is_version2:
            'OAuth v2 does not have any request_token'
            return None, None, self._client.authorization_url(redirect_uri=self.callback_url)
        else:
            # do the hairy, three-legged, version 1 processing
            r, c = self._client.request(self.provider.request_token_url,
                                        method=self.provider.auth_http_method,
                                        parameters=self._get_req_token_params())
            if r['status'] == '200':
                tmp_token = oauth2.Token.from_string(c)
            else:
                raise ApiError(r, c)

            req2 = oauth2.Request.from_token_and_callback(token=tmp_token,
                                                          callback=callback_url,
                                                          http_url=self.provider.authorization_url)
            return tmp_token.key, tmp_token.secret, req2.to_url()

    def auth_part2(self, 
                   req_token, 
                   req_token_secret, 
                   oauth_verifier=None,
                   code=None,
                   callback_params=None):
        '''Authenticate and return (access_token, access_token_secret)

        the req_token, and req_token_secret should be the same as those
        returned by auth_part1. 

        You need to specify only one of oauth_verifier OR
        code or callback_params.

        oauth_verifier will be the verifier embedded in the callback_url
        by OAuth version 1.

        code will be the 'code' embedded in the callback_url by
        OAuth version 2.

        If you don't want to get into those details, simply send
        the params from the callback url as a dict or dict-like object.
        e.g. in django, do this: callback_params=request.REQUEST 
        '''
        if self._is_version2:
            if not code:
                if not callback_params:
                    raise Error("You must provide either 'code' or 'callback_params'")
                code = callback_params.get('code')
            ac = self._client.access_token(code, self.callback_url)
            if 'access_token' in ac:
                actok = ac['access_token']
                self.auth(actok, None)
                return actok, None
            else:
                raise ApiError(ac)
        else:
            if not oauth_verifier:
                if not callback_params:
                    raise Error("You must provide either 'oauth_verifier' or 'callback_params'")
                oauth_verifier = callback_params.get('oauth_verifier')

            self._set_Token(oauth2.Token(req_token, req_token_secret),
                            verifier=oauth_verifier)
            r, c = self._client.request(self.provider.access_token_url,
                                        method=self.provider.auth_http_method)

            if r['status'] == '200':
                ac = oauth2.Token.from_string(c)
                self.auth(ac.key, ac.secret)
                return ac.key, ac.secret
            else:
                raise ApiError(r, c)

            

    def auth(self, access_token, access_token_secret):
        if self._is_version2:
            self.access_token = access_token
        else:
            self._set_Token(oauth2.Token(access_token, access_token_secret))
            

    def update_headers(self, **kwargs):
        '''Set headers to be used for API calls'''
        self._headers.update(kwargs)

    def set_data_type(self, data_type):
        '''Set data type of values returned by API

        Currently we understand json and xml'''
        self._data_type = data_type.lower()

    def set_request_args(self, **kwargs):
        self._extra_args.update(kwargs)

    def _get_req_token_params(self):
        if self.provider.callback_for_request_token:
            return dict(oauth_callback=self.provider.callback_for_request_token)
        else:
            return None

    def get(self, path, **params):
        '''Make an API call to 'path' with all keyword arguments as params
        '''
        
        '''Sadly, we need to do two different types
        of call to _client.request, because they take 
        slightly different parameters'''
        if self._is_version2:
            r, c = self._client.request(self.provider.api_url_base+path,
                                        access_token=self.access_token,
                                        method=self.provider.api_http_method,
                                        headers=self._headers,
                                        params=params,
                                        **self._extra_args)
        else:
            uri = self.provider.api_url_base+path
            if params:
                if self.provider.api_http_method != 'GET':
                    raise Error('Can not specify params with POST. Use body')
                uri = "%s?%s" % (uri, urlencode(params))
            print 'URI=', uri
            r,c = self._client.request(uri,
                                       method=self.provider.api_http_method,
                                       headers=self._headers,
                                       **self._extra_args)

        if r['status'] == '200':
            if self._data_type == 'json':
                return loads(c)
            elif self._data_type == 'xml':
                from xml.etree import ElementTree
                return ElementTree.fromstring(c)
            else:
                return c        # no idea what the data-type is. return as-is
        else:
            raise ApiError(r, c)
