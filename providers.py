from __init__ import Provider
linkedin = Provider(url_base = 'https://api.linkedin.com/uas/oauth/',
                    request_token_url = 'requestToken',
                    access_token_url = 'accessToken',
                    authorization_url = 'authorize',
                    api_url_base = 'https://api.linkedin.com/v1/',
                    api_extra_headers = {'x-li-format': 'json'})

twitter = Provider(url_base = 'https://api.twitter.com/oauth/',
                    request_token_url = 'request_token',
                    access_token_url = 'access_token',
                    authorization_url = 'authorize',
                    api_url_base = 'http://api.twitter.com/1/')

delicious = Provider(url_base = 'https://api.login.yahoo.com/oauth/v2/',
                     request_token_url = 'get_request_token',
                     access_token_url = 'get_token',
                     authorization_url = 'request_auth',
                     api_url_base = 'http://api.del.icio.us/v2/',
                     api_extra_headers = {'x-li-format': 'json'},
                     default_auth_http_method='GET',
                     callback_for_request_token='oob')
facebook = Provider(oauth_version='2',
                    url_base = 'https://graph.facebook.com/oauth/',
                    authorization_url = 'authorize',
                    access_token_url = 'access_token',
                    api_url_base='https://graph.facebook.com/',
                    default_auth_http_method='GET')
