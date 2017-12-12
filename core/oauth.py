import sys
from rauth import OAuth1Service
from rauth import OAuth1Session

import settings


def get_oauth_tokens(API_KEY, API_KEY_SECRET):
    """
    :param API_KEY: Smugmug API key
    :param API_KEY_SECRET: Smugmug Secret key
    :return: (access_token, secret_token)
    :rtype: tuple
    """

    SERVICE = OAuth1Service(
        name='smugmug-oauth',
        consumer_key=API_KEY,
        consumer_secret=API_KEY_SECRET,
        request_token_url=settings.REQUEST_TOKEN_URL,
        access_token_url=settings.ACCESS_TOKEN_URL,
        authorize_url=settings.AUTHORIZE_URL,
        base_url=settings.BASE_URL)

    rt, rts = SERVICE.get_request_token(params={'oauth_callback': 'oob'})
    auth_url = SERVICE.get_authorize_url(rt)
    print('Go to %s in a web browser.' % auth_url)
    sys.stdout.write('Enter the six-digit code: ')
    sys.stdout.flush()
    verifier = sys.stdin.readline().strip()
    at, ats = SERVICE.get_access_token(rt, rts, params={'oauth_verifier': verifier})
    print("NEW ACCESS_TOKEN:", at)
    print("NEW ACCESS_TOKEN_SECRET:", ats)
    session = OAuth1Session(API_KEY, API_KEY_SECRET, access_token=at, access_token_secret=ats)
    print(
        session.get(
            settings.API_ORIGIN + '/api/v2!authuser', headers={'Accept': 'application/json'}
        ).json()
    )
    return at, ats
