import httplib
import json
import urllib2
from collections import Iterator
from oauth import get_oauth_tokens
# from rauth import OAuth1Session
from requests_oauthlib import OAuth1Session
from time import sleep
from unidecode import unidecode
from urlparse import parse_qs, urlparse

from settings import (
    ACCESS_TOKEN,
    ACCESS_TOKEN_SECRET,
    API_KEY,
    API_KEY_SECRET,
    API_ORIGIN,
    DEBUG)
from settings import logger
from utils.utils import random_string, pretty_print_POST

__version__ = '0.1.0'


class SmugmugAPI(object):
    def __init__(self, api_key=API_KEY, api_key_secret=API_KEY_SECRET):
        self.api_key = api_key
        self.api_key_secret = api_key_secret

        if not all((ACCESS_TOKEN, ACCESS_TOKEN_SECRET)):
            new_at, new_ats = get_oauth_tokens(api_key, api_key_secret)
            self.access_token = new_at
            self.access_token_secret = new_ats

            exit()
        else:
            self.access_token = ACCESS_TOKEN
            self.access_token_secret = ACCESS_TOKEN_SECRET

        r = OAuth1Session(
            API_KEY,
            API_KEY_SECRET,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret,
        )

        self.r = r
        self.root_node = None

    def update_image_keywords(self, image_key, keywords):
        uri = image_key

        payload = {
            "KeywordArray": keywords,
        }
        headers = {
            "Accept": "application/json",
            "content-type": "application/json"
        }

        r = self.r.patch(
            API_ORIGIN + uri,
            data=json.dumps(payload),
            headers=headers,
        )
        if DEBUG:
            logger.debug("headers %s, code %s, reason %s, content: %s",
                         r.headers,
                         r.status_code,
                         r.reason,
                         r.content)

        try:
            if r.status_code == 200:
                return True
            else:
                raise Exception("Status is not 200")
        except Exception:
            logger.exception("headers %s, code %s, reason %s, content: %s",
                             r.headers,
                             r.status_code,
                             r.reason,
                             r.content)

    def get_remote_images(self, limit=100):
        class ImagesIter(Iterator):
            def __init__(self, request):
                self.r = request
                self.next_page_params = None

            def __iter__(self):
                return self

            def next(self):
                payload = {}

                if not self.next_page_params:
                    payload = {
                        "start": 0,
                        "count": limit,
                        "Scope": root_node,
                        "SortDirection": "Descending",
                        "SortMethod": "DateUploaded",

                    }

                elif self.next_page_params is StopIteration:
                    raise StopIteration

                else:
                    for qs_name, v in self.next_page_params.items():
                        payload[qs_name] = v[0]

                uri = '/api/v2/image!search'

                headers = {"Accept": "application/json"}

                r = self.r.get(
                    API_ORIGIN + uri,
                    params=payload,
                    headers=headers
                )

                if DEBUG:
                    logger.debug("headers %s, code %s, reason %s, content: %s",
                                 r.headers,
                                 r.status_code,
                                 r.reason,
                                 r.content)

                try:
                    payload = json.loads(r.content)
                    result = payload['Response'].get('Image', [])
                except Exception:
                    logger.exception("Bad json: %s", r.content)
                    raise StopIteration

                if not result:
                    raise StopIteration

                if payload['Response']['Pages'].get('NextPage'):
                    next_page_link = urllib2.unquote(
                        payload['Response']['Pages']['NextPage']
                    )
                    self.next_page_params = parse_qs(
                        urlparse(next_page_link).query,
                        keep_blank_values=False
                    )
                else:
                    self.next_page_params = StopIteration
                return result

        root_node = self.get_root_node()
        return ImagesIter(self.r)

    def _node_iterator(self, parent_node, node_type):
        api_key = self.api_key

        class NodeIter(Iterator):
            def __init__(self, request):
                self.r = request
                self.next_page_params = None

            def __iter__(self):
                return self

            def next(self):
                payload = {}

                if not self.next_page_params:
                    payload = {
                        'start': 0,
                        'count': 200,
                        'SortDirection': 'Descending',
                        'SortMethod': 'Name',
                        'Type': node_type,
                        "APIKey": api_key,

                    }
                    headers = {"Accept": "application/json"}

                    uri = parent_node + '!children'

                    r = self.r.get(
                        API_ORIGIN + uri,
                        params=payload,
                        headers=headers
                    )

                    if DEBUG:
                        logger.debug("Response: %s %s %s",
                                     r.status_code, r.reason, r.headers)
                        logger.debug(
                            json.dumps(json.loads(r.content), indent=4))

                elif self.next_page_params is StopIteration:
                    raise StopIteration

                else:
                    for qs_name, v in self.next_page_params.items():
                        payload[qs_name] = v[0]

                uri = parent_node + '!children'

                headers = {"Accept": "application/json"}

                r = self.r.get(
                    API_ORIGIN + uri,
                    params=payload,
                    headers=headers
                )

                if DEBUG:
                    logger.debug("headers %s, code %s, reason %s, content: %s",
                                 r.headers,
                                 r.status_code,
                                 r.reason,
                                 r.content)

                try:
                    payload = json.loads(r.content)
                    result = payload['Response'].get('Node', [])
                except Exception:
                    logger.exception("Bad json: %s", r.content)
                    logger.info("headers %s, code %s, reason %s, content: %s",
                                r.headers,
                                r.status_code,
                                r.reason,
                                r.content)
                    raise Exception('Something goes wrong. '
                                    'Bad JSON, please retry')

                if not result:
                    raise StopIteration

                if payload['Response']['Pages'].get('NextPage'):
                    next_page_link = urllib2.unquote(
                        payload['Response']['Pages']['NextPage']
                    )
                    self.next_page_params = parse_qs(
                        urlparse(next_page_link).query,
                        keep_blank_values=False
                    )
                else:
                    self.next_page_params = StopIteration
                return result

        return NodeIter(self.r)

    def get_root_node(self):
        if self.root_node:
            return self.root_node

        payload = {"APIKey": self.api_key}
        headers = {"Accept": "application/json"}

        r = self.r.get(
            API_ORIGIN + "/api/v2!authuser",
            params=payload,
            headers=headers
        )

        if DEBUG:
            logger.debug(r.status_code, r.reason, r.headers)
            logger.debug(json.dumps(json.loads(r.content), indent=4))

        response = json.loads(r.content)
        node_uri = response['Response']['User']['Uris']['Node']['Uri']

        if DEBUG:
            logger.debug(["Root node:", node_uri])

        self.root_node = node_uri

        return node_uri

    def get_or_create_node(self, parent_node, node_name, node_type='Folder'):
        attempts = 5
        while attempts:
            r = None
            try:
                node_uri = None

                for node_page in self._node_iterator(parent_node, node_type):
                    for n in node_page:
                        if unidecode(node_name).lower() == n["Name"].lower() \
                                and node_type == n['Type']:
                            if node_type == 'Folder':
                                node_uri = n['Uri']
                            elif node_type == 'Album':
                                node_uri = n['Uris']['Album']['Uri']
                            break
                    if node_uri:
                        return node_uri

                headers = {"Accept": "application/json"}
                full_uri = parent_node + '!children'
                node_name = unidecode(node_name)
                url_name = random_string()
                payload = {
                    "Type": node_type,
                    "Name": node_name,
                    "UrlName": url_name,
                    "Privacy": 'Unlisted',
                }

                r = self.r.post(
                    API_ORIGIN + full_uri,
                    data=payload,
                    headers=headers
                )

                if DEBUG:
                    logger.debug(
                        "Create node %s response. \nparent_node_uri %s "
                        "\nNode type: %s \ncode: %s \nreason: %s \nheaders: %s",
                        node_name, parent_node, node_type, r.status_code,
                        r.reason, r.headers)
                    logger.debug(json.dumps(json.loads(r.content), indent=4))

                response = json.loads(r.content)
                if node_type == 'Folder':
                    uri = response['Response']['Node']['Uri']
                elif node_type == 'Album':
                    uri = response['Response']['Node']['Uris']['Album']['Uri']

                logger.info("Node %s created. Uri: %s", node_name, uri)

                return uri

            except Exception:
                sleep(10)
                attempts -= 1
                if r:
                    logger.exception(
                        "[ERROR CREATING NODE] code: %s, reason: %s, \nheaders: %s",
                        r.content, r.status_code, r.reason
                    )
                else:
                    logger.exception("[ERROR CREATING NODE]")
