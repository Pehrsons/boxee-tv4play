#encoding:utf-8

# Must be run from same folder for relative import path to work!
# Run with python 2.4 for full boxee compatibility
import sys
sys.path.append("../tv.boxeeplay.tv4play2/")
from api4 import Api4Client as ApiClient
from api4_mc import category_to_list_item, show_to_list_item, episode_to_list_item, episode_list_item_to_playable
from logger import Level, SetEnabledPlus
from pirateplay import NoSuitableStreamError, NoStreamsError, pirateplayable_item
import itertools
import ip_info
import unittest

class IntegrationTestApi4(unittest.TestCase):

    def setUp(self):
        SetEnabledPlus(Level.DEBUG, True)
        self.client = ApiClient()

    def test_fetch_categories(self):
        categories = []
        categories.extend(self.client.categories)
        self.assertTrue(len(categories) > 3)

    def test_convert_categories(self):
        mc_categories = itertools.imap(category_to_list_item, self.client.categories)
        mc_cat_list = []
        mc_cat_list.extend(mc_categories)
        self.assertEquals(len(self.client.categories), len(mc_cat_list))
        for cat in mc_cat_list:
            self.assertCategory(cat)

    def test_fetch_shows(self):
        categories = self.client.categories
        shows = []
        shows.extend(self.client.get_shows(categories[2]))
        self.assertTrue(len(shows) > 0)

    def test_convert_shows(self):
        categories = self.client.categories
        shows = []
        shows.extend(itertools.imap(show_to_list_item, self.client.get_shows(categories[2])))
        for show in shows:
            self.assertShow(show)

    def test_fetch_episodes(self):
        categories = self.client.categories
        shows = []
        shows.extend(self.client.get_shows(categories[3]))
        episodes = []
        episodes.extend(itertools.islice(self.client.get_episodes(shows[7]), 1000))
        self.assertTrue(len(episodes) > 0)

    def test_convert_episodes(self):
        categories = self.client.categories
        shows = []
        shows.extend(self.client.get_shows(categories[4]))
        episodes = []
        episodes.extend(itertools.islice(self.client.get_episodes(shows[7]), 150))
        mc_episodes = []
        mc_episodes.extend(itertools.imap(episode_to_list_item, episodes))
        for episode in mc_episodes:
            self.assertEpisode

    def test_latest_full_episodes(self):
        episodes = []
        episodes.extend(itertools.islice(self.client.get_latest_full_episodes(), 140))
        self.assertEquals(len(episodes), 140)
        mc_episodes = []
        mc_episodes.extend(itertools.imap(episode_to_list_item, episodes))
        for episode in mc_episodes:
            self.assertEpisode(episode)
            self.assertEquals(episode.GetProperty("episode"), "true")

        try:
            episode = episode_list_item_to_playable(episode)
            self.assertString(pirateplayable_item(episode).GetPath())
        except NoSuitableStreamError, e:
            print str(e)
            self.assertTrue(False)
        except NoStreamsError, e:
            print str(e)
            self.assertTrue(False)

    def test_latest_episodes(self):
        episodes = []
        episodes.extend(itertools.islice(self.client.get_latest_episodes(), 40))
        self.assertEquals(len(episodes), 40)
        mc_episodes = []
        mc_episodes.extend(itertools.imap(episode_to_list_item, episodes))
        for episode in mc_episodes:
            self.assertEpisode(episode)

    def assertCategory(self, category):
        self.assertString(category.GetTitle())
        self.assertString(category.GetLabel())
        self.assertString(category.GetProperty("id"))

    def assertShow(self, show):
        self.assertString(show.GetTitle())
        self.assertString(show.GetLabel())
        self.assertString(show.GetDescription())
        self.assertString(show.GetProperty("id"))
        self.assertString(show.GetProperty("category"))

    def assertEpisode(self, episode):
        self.assertString(episode.GetTitle())
        self.assertString(episode.GetLabel())
        self.assertString(episode.GetDescription())
        self.assertString(episode.GetStudio())
        self.assertString(episode.GetProperty("category"))
        self.assertTrue(episode.GetProperty("category") != "undefined")
        self.assertString(episode.GetProperty("show"))
        self.assertTrue(episode.GetProperty("show") != "undefined")
        self.assertString(episode.GetProperty("id"))

    def assertString(self, obj):
        self.assertTrue(isinstance(obj, basestring) or isinstance(obj, unicode))

    def test_geo_ip(self):
        self.assertString(ip_info.get_country_name())
        self.assertString(ip_info.get_country_code())

if __name__ == '__main__':
    unittest.main()
