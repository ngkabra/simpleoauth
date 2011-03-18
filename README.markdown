**WARNING: DON'T USE THIS YET. THIS CODE IS NEITHER COMPLETE NOR PROPERLY TESTED. Of course, if you want the help me to finish this, then please use it and send me a pull request. Thanks. It appears to work for twitter, facebook, linked-in (at least for simple cases).**

This is a very simplified python interface to OAuth version 1 and version 2, for those who find the python-oauth2 too complex. This depends upon my own version of [python-oauth2](https://github.com/ngkabra/python-oauth2), which is essentially a very minor variation on [zbowling/python-oauth2](https://github.com/zbowling/python-oauth2) (and which is very different form [simplegeo/python-oauth2](https://github.com/simplegeo/python-oauth2)). 


### QuickStart

**Trivial usage when we already have an access_token**

This section shows how to use simpleoauth to access a service when you already have an access_token. (For example, if you're building a facebook app, then every request from a user who has authorized your app, already contains the access_token). Note: access_tokens (and access_token_secret in case of OAuth 1.0) can be stored persistently in a database or session or cookie for long-term use.

This is an example of using the Twitter API 

    # Twitter (example of OAuth v1)
    from simpleoauth import Client, providers
    
    consumer = ('<YOUR_CONSUMER_KEY>', '<YOUR_CONSUMER_SECRET>')
    tok = '<YOUR_ACCESS_TOKEN>'
    tok_secret = '<YOUR_ACCESS_TOKEN_SECRET>'

    client = Client(consumer, providers.twitter, 
                    access_token=tok,
                    access_token_secret=tok_secret)

    # Now the client is ready for API calls
    # You don't need to specify the base_url for the API
    # because that is already configured into the Provider
    # Just provide the actual path for the request.
    # Parameters can be provided as additional keyword arguments
    # as shown
    data = client.get('users/show.json', screen_name='ngkabra')

    # The returned data is automatically parsed using simplejson.loads
    # and made available as a python dict
    print 'Hello, %s' % (data['name'])

    # You can also post updates
    client.post('statuses/update.json', status='I can now post to twitter using simpleoauth')

Facebook uses OAuth v2, but the code is otherwise very similar. Note: facebook insists that the callback_url be specified and it should match the callback url registered with facebook along with your app. Please include that in the "consumer" tuple as shown:

    # Facebook (example of OAuth v2)
    from simpleoauth import Client, providers

    consumer = ('<YOUR_CLIENT_ID>', '<YOUR_CLIENT_SECRET>',
                'http://<YOUR_CALLBACK_URL>/')

    tok = '<YOUR_ACCESS_TOKEN>'
    client = Client(consumer, providers.facebook, access_token=tok)

    # Now the client is ready for api calls
    data = client.get('me')

    # As before, the data is available as a python dict
    print 'Hello, %s %s' % (data['first_name'], data['last_name'])

    # Update using post
    client.post('me/feed', message='I can post to facebook using simpleoauth', access_token=tok)

**How to get an access_token - command line version**

**Code for OAuth v1**

    from simpleoauth import Client, providers

    consumer = ('my_consumer_key', 'my_consumer_secret')
    client = Client(consumer, providers.twitter)
    req_token, req_token_secret, auth_url = client.auth_part1()
    # At this point ask user to visit 'auth_url'
    verifier = raw_input('Please input the oauth_verifier')
    client.auth_part2(req_token, req_token_secret, oauth_verifier=verifier)

    # Now you're read to start using the API
    user_info = client.get('users/show.json', screen_name='ngkabra')
    print "Hello", user_info['name']

**Code for OAuth v2**

    # The code looks very similar for OAuth v2
    consumer = ('my_client_id', 'my_client_secret', 
                'http://example.com/my_callback_url')
    client = Client(consumer, providers.facebook)
    ignore1, ignore2, auth_url = client.auth_part1()
    # At this point ask user to visit 'auth_url'
    code = raw_input('Please input the verification code')
    client.auth_part2(ignore1, ignore2, code=verifier)

    # Now you're read to start using the API
    user_info = client.get('me')
    print 'Hello, %s %s' % (data['first_name'], data['last_name'])

### Gentler (Longer) Introduction    

simpleoauth consists of a Client, which is used for authentication and for making the actual api calls, and a Provider class which encapsulates information about the Provider, including the various urls (for example, the access_token url), and other settings (for example, whether it uses OAuth v1 or OAuth v2, whether it uses GET or POST for authentication, etc). 

simpleoauth also comes with pre-defined providers for popular OAuth service providers like facebook, twitter, linkedin, so you don't have to do any configuration for them. For other providers, it is fairly easy to add a provider class of your own.

OAuth allows you to get and persistently store an access_token for a user. Once you have the access_token, until it expires, you can use it anytime to access the service without requiring any further authentication step.  

Note: To be able to use OAuth, you are required to have a consumer_key and a consumer_secret (in case of OAuth v1) or a client_id and a client_secret (in case of OAuth v2). Please check the website of the service provider for how to get a consumer_key/secret or client_id/secret. 

### Authenticating a user and getting an access token

Getting an access token is a two-step process. First we need to contact the service provider and get an "authorization_url", and redirect the user to this url. This url takes the user to a webpage on the service providers site where the user is prompted to authorize our application to access their data. 

Once authorized, the service provider redirects the user to a callback_url supplied by us. This callback url has either an 'oauth_verifier' (OAuth v1) or a 'code' (OAuth v2) encoded as a url parameter. 

Our code that will be handling this callback_url needs to take the 'oauth_verifier' or 'code' and use it to do step two of the OAuth authorization process. Step 2 uses this information to generate an access_token (and possibly an access_token_secret). This access_token can then be stored persistently.

The following django code illustrates the usage:

    from simpleoauth import Client, providers
    from django.conf import settings
    from django.http import HttpResponseRedirect

    consumer = (settings.TWITTER_CLIENT_ID, 
                settings.TWITTER_CLIENT_SECRET,
                settings.TWITTER_CALLBACK_URL)

    def login_using_twitter(request):
       '''This view does the first part of the authentication protocol
       '''
       client = Client(consumer, providers.twitter)
       req_tok, req_tok_secret, auth_url = client.auth_part1()
       request.session['req_tok'] = req_tok
       request.session['req_tok_secret'] = req_tok_secret       
       return HttpResponseRedirect(auth_url)

    
    def callback(request):
       '''This handles the callback. 

       You need to ensure that settings.TWITTER_CALLBACK_URL is mapped
       to this view'''

       client = Client(consumer, providers.twitter)
       req_tok = request.session.get('req_tok')
       req_tok_secret = request.session.get('req_tok_secret')
       (access_token, 
        access_token_secret) = client.auth_part2(req_tok, req_toke_secret,
                                                 callback_params=request.GET)

       # req_tok and req_tok_secret are no longer needed
       del request.session['req_tok']
       del request.session['req_tok_secret']


       # You'll can also store this in the database, instead of the session
       request.session['access_token'] = access_token
       request.session['access_token_secret'] = access_token_secret
       return HttpResponseRedirect(reverse('do_something'))


    def do_something(request):
       ac = request.session.get('access_token')
       ac_secret = request.session.get('access_token_secret')
       if not ac:
           return HttpResponseRedirect(reverse('login_using_twitter'))
       client = Client(consumer, providers.twitter, 
                       access_token=ac,
                       access_token_secret=ac_secret)
       data = client.get('users/show.json', screen_name='ngkabra')
       return render_to_response('do_something.html', {'twitter_data': data})

Exactly the same code will work for getting an access token for OAuth v2.

Points to note: OAuth v2 does not have the concept of request_token, or request_token_secret. Nor does it have the concept of access_token_secret. However, for uniformity of code, simpleoauth returns appropriate "None" objects in the correct places s that the above code will work. However, in the "login_using_facebook" view, you can simply ignore request_token and request_token_secret instead of storing them in the session (because they will both be None). In the callback, you can send in None and None for them. 

### Creating your own Provider

You can also create your own simpleouath.providers.Provider objects. Here is an example using Linked-in (an OAuth v1 provider):

    linkedin = Provider(url_base = 'https://api.linkedin.com/uas/oauth/',
                        request_token_url = 'requestToken',
                        access_token_url = 'accessToken',
                        authorization_url = 'authorize',
                        api_url_base = 'https://api.linkedin.com/v1/',
                        api_extra_headers = {'x-li-format': 'json'})

- url_base is the base url to be prefixed to request_token_url, access_token_url, and authorization url. 
- api_url_base it the base url to be prefixed to all API calls. 
- api_extra_headers can be used to send in any extra headers if necessary

Here is how the Facebook provider is defined (an OAuth v2 provider):

    facebook = Provider(oauth_version='2',
                        url_base = 'https://graph.facebook.com/oauth/',
                        authorization_url = 'authorize',
                        access_token_url = 'access_token',
                        api_url_base='https://graph.facebook.com/',
                        default_auth_http_method='GET')

- Note that request_token_ur is not requred for OAuth v2.
- You must specify oauth_version='2'

Other parameters to the Provider constructor that you might need in case your OAuth provider is a little non-standard:

- default_auth_http_method: can be 'POST' or 'GET'. The http method used for the authentication calls
- default_api_http_method: can be 'POST' or 'GET'. The http method used for the API calls (after authentication is already done)
- callback_for_request_token: required in case of Yahoo! OAuth api. 
- default_data_type: if it is 'json' all API call results are processed with simplejson.loads before returning. If it is 'xml' all API call results are processed with xml.etree.ElementTree.fromstring befor returning. In all other cases, the data is returned without any processing.

### Why?

Why does simpleoauth exist? Because I found that OAuth libraries in python were very confusing. Should I use oauth, or oauth2? OAuth comes standard with python, but to do anything really useful, you want oauth2. And it turns out that oauth2 does not actually support OAuth-2.0 (as implemented by facebook, for example). For that there is zbowling/python-oauth2. And the examples given with all these packages are out-of-date or confusing enough that it takes a very long time to figure out what's going on. And there are a lot of urls you have to configure.

There are good reasons why the oauth2 library is that way - I assume all of that functionality is needed for maximum flexibility.

By contrast, `simpleoauth` tries to handle the simple cases only, but in a very simple way. It has in-built support for the more common websites where you would like to use OAuth (facebook, twitter, linked-in, yahoo). And adding new ones is easy. I hope it is useful to somebody.

The main design goals for this module were:

- Simple interface for the common cases, at the expense of flexibility
- Should work with OAuth v1 or OAuth v2 with the same or similar interface
- Should be easy to incorporate into Django

### TODO

This is not even an _alpha_ version. This is just a proof-of-concept right now. Lots of work needs to be done before it can be "released" for use by others. Here are some of the most important.

- Add tests
- Packaging so that it can be put on pypi, and works with easy_install and pip.
- Add a good, comprehensive django example
