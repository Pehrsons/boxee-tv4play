#encoding:utf-8
#author:Andreas Pehrson
#project:boxeeplay.tv

from utilities import load_json, Url
from logger import BPLog, Level
from operator import itemgetter

BASE_URL = "http://mobapi.tv4play.se"

__all__ = [ "Api4Client", "Api4Iterable" ]

class Api4Client:
    def __init__(self):
        self.endpoints = {'category': "/video/categories/list",
                          'show'    : "/video/program_formats/list",
                          'episode' : "/video/programs/search",
                          'channels': "/tvdata/channels"}
        self.categories = sorted(self.get_iterable(self.get_list_endpoint("category")),
                                 key=itemgetter("name"))

    def url(self, location):
        if location is None:
            return None
        url = Url(BASE_URL + location)
        return url

    def get_list_endpoint(self, key):
        return self.url(self.endpoints[key])

    def get_json(self, url):
        return load_json(url)

    def get_iterable(self, endpoint):
        return Api4Iterable(self, endpoint)

    def get_shows(self, category):
        return self.get_shows_from_id(category["id"])

    def get_shows_from_id(self, ident, hide_premium=False):
        url = self.get_list_endpoint("show")
        url.add_param("sorttype", "name")
        url.add_param("categoryid", ident)
        if hide_premium:
            url.add_param("premium_filter", "free")
        return self.get_iterable(url)

    def get_shows_from_search_term(self, term, hide_premium=False):
        url = self.get_list_endpoint("show")
        url.add_param("name", term)
        if hide_premium:
            url.add_param("premium_filter", "free")
        return self.get_iterable(url)

    def get_latest_full_episodes(self):
        url = self.get_list_endpoint("episode")
        url.add_param("platform", "web")
        url.add_param("premium", "false")
        url.add_param("sorttype", "date")
        url.add_param("livepublished", "false")
        url.add_param("rows", "100")
        url.add_param("video_types", "programs")
        return self.get_iterable(url)

    def get_latest_episodes(self):
        url = self.get_list_endpoint("episode")
        url.add_param("platform", "web")
        url.add_param("premium", "false")
        url.add_param("sorttype", "date")
        url.add_param("livepublished", "false")
        url.add_param("rows", "100")
        return self.get_iterable(url)

    def get_episodes(self, show):
        return self.get_episodes_from_id(show["id"])

    def get_episodes_from_id(self, ident):
        url = self.get_list_endpoint("episode")
        url.add_param("platform", "web")
        url.add_param("premium", "false")
        url.add_param("sorttype", "date")
        url.add_param("livepublished", "false")
        url.add_param("categoryids", ident)
        url.add_param("rows", "1000")
        return self.get_iterable(url)

    def get_episodes_from_category_id(self, category_id):
        url = self.get_list_endpoint("episode")
        url.add_param("platform", "web")
        url.add_param("premium", "false")
        url.add_param("sorttype", "date")
        url.add_param("livepublished", "false")
        url.add_param("categoryids", category_id)
        url.add_param("rows", "100")
        return self.get_iterable(url)

    def get_episodes_from_search_term(self, term):
        url = self.get_list_endpoint("episode")
        url.add_param("text", term)
        url.add_param("premium", "false")
        url.add_param("rows", "200")
        return self.get_iterable(url)

    def get_channels(self):
#        svt1 = {"id": "1"
#               ,"kind_of": 3
#               ,"thumbnail_url": "http://www.boxeeplay.tv/images/svt1.jpg"
#               ,"title": "SVT1"
#               ,"url": "http://www.svtplay.se/kanaler/svt1"
#               ,"viewable_in": 2,
#               }
        return []

# NOT thread safe
class Api4Iterable:
    def __init__(self, client, url):
        self.client = client
        self.next_url = url
        self.objects = []
        self.current_limit = 0
        self.size = 1

    def __iter__(self):
        return Api4Iterator(self, self.client)

    def set_meta(self, current_limit, size, next_url):
        self.current_limit = current_limit
        self.size = size
        self.next_url = next_url

# NOT thread safe
class Api4Iterator:
    def __init__(self, iterable, client):
        self.iterable = iterable
        self.client = client
        self.current = -1

    def __iter__(self):
        return self

    def next(self):
        self.current += 1
        if self.current >= self.iterable.size:
            raise StopIteration
        if self.current >= self.iterable.current_limit:
            json = self.client.get_json(self.iterable.next_url)
            if "total_hits" in json:
                current_limit = self.iterable.current_limit + len(json["results"])
                next_url = self.iterable.next_url.add_param("start", repr(current_limit))
                self.iterable.set_meta(current_limit, json["total_hits"], next_url)
                self.iterable.objects.extend(json["results"])
            else:
                size = len(json)
                self.iterable.set_meta(size, size, None)
                self.iterable.objects.extend(json)
        if self.current >= len(self.iterable.objects):
            BPLog("API reported length of " + str(self.iterable.size) +
                  " but I reached the end at " + str(self.current) +
                  " items. Stopping.", Level.DEBUG)
            raise StopIteration # if we got more objects but the list was not filled as expected
        #BPLog("objects length: " + str(len(self.iterable.objects)) + ", current: " + str(self.current - 1) + ", size: " + str(self.iterable.size) + ", current_limit: " + str(self.iterable.current_limit))
        return self.iterable.objects[self.current]

