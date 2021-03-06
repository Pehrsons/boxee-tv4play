﻿#encoding:utf-8
#author:Andreas Pehrson
#project:boxeeplay.tv

import mc, ip_info, settings
from api4 import Api4Client as ApiClient
from api4_mc import category_to_list_item, show_to_list_item, episode_to_list_item, set_outside_sweden, episode_list_item_to_playable
from pirateplay import pirateplayable_item, NoStreamsError, NoSuitableStreamError
from logger import BPLog,BPTraceEnter,BPTraceExit,Level,IsEnabled
from itertools import islice
from trackerjob import TrackerJob
from jobmanager import BoxeeJobManager
from async_task import AsyncTask

VERSION = "TV4Play 2.03"
NO_SHOWS_TEXT = "Inga program laddade"
NO_EPISODES_TEXT = "Inga avsnitt för det här programmet"

initiated = False
category_list_index = -1
show_list_index = -1
episode_list_index = -1
focused_group = 100
labelPrograms = ""
labelEpisodes = ""
client = None
country_code = "unknown"
is_sweden = True
job_manager = BoxeeJobManager()
ip_getter = ip_info.IpGetter()
last_search_term = ""

def initiate():
    global category_list_index
    global show_list_index
    global episode_list_index
    global labelPrograms
    global labelEpisodes
    global country_code
    global is_sweden
    global client
    global initiated

    BPTraceEnter()
    mc.ShowDialogWait()

    if not initiated:
        job_manager.start()
        ip_getter.start()

        try:
            client = ApiClient()
        except Exception, e:
            track ("Wlps Init Error", { "Locale": mc.GetGeoLocation(),
                                        "Platform": mc.GetPlatform(),
                                        "Country Code": country_code,
                                        "Id": mc.GetUniqueId()
                                      })
            BPLog("Could not set up API client: " + str(e))
            show_error_and_exit(message="Kunde inte kontakta API-servern. Appen stängs ner...")

        latest_thread = AsyncTask(target=iterate, kwargs={"iterable":client.get_latest_full_episodes(), "limit":200})
        latest_thread.start()

        ip_getter.join(3.0)
        try:
            country_code = ip_getter.get_country_code()
            is_sweden = country_code == "SE"
        except Exception, e:
            BPLog("Could not retreive physical location of client: " + str(e))

        BPLog("We are in sweden: " + str(is_sweden))
        if not is_sweden:
            set_outside_sweden(True)
            mc.GetWindow(14000).GetLabel(14002).SetLabel("Du är inte i Sverige\nAllt material kan inte visas")
        else:
            set_outside_sweden(False)
            mc.GetWindow(14000).GetLabel(14002).SetLabel("")

        BPLog("No programs in program listing. Loading defaults.", Level.DEBUG)
        loadCategories()

        latest_thread.join()
        latest_item = mc.ListItem()
        latest_item.SetLabel("Senaste program")
        latest_item.SetProperty("category", "preset-category")
        load_episodes(latest_thread.get_result(), latest_item)

        initiated = True

        track("Initated", { "Locale": mc.GetGeoLocation(),
                            "Platform": mc.GetPlatform(),
                            "Country Code": country_code,
                            "Id": mc.GetUniqueId(),
                            "In Sweden": str(is_sweden)
                          })
    else:
        #Restore last focus
        mc.GetWindow(14000).GetLabel(2002).SetLabel(labelPrograms)
        mc.GetWindow(14000).GetLabel(3002).SetLabel(labelEpisodes)

        mc.GetWindow(14000).GetControl(focused_group).SetFocus()
        mc.GetWindow(14000).GetList(1000).SetFocusedItem(category_list_index)
        mc.GetWindow(14000).GetList(2001).SetFocusedItem(show_list_index)
        mc.GetWindow(14000).GetList(3001).SetFocusedItem(episode_list_index)

    mc.HideDialogWait()
    BPLog("Initiate complete.")
    BPTraceExit()

def loadCategories():
    BPTraceEnter()
    win = mc.GetWindow(14000)
    target = win.GetList(1000)
    win.GetLabel(2003).SetLabel(NO_SHOWS_TEXT)
    win.GetLabel(3003).SetLabel(NO_EPISODES_TEXT)
    items = mc.ListItems()
    for cat in client.categories:
        items.append(category_to_list_item(cat))
    target.SetItems(items)
    BPLog("Successfully loaded all categories.", Level.DEBUG)
    BPTraceExit()

def click_search():
    global last_search_term

    search_term = mc.ShowDialogKeyboard("Ange sökterm", last_search_term, False)
    if not search_term or search_term == "":
        BPLog("Search cancelled")
        return

    last_search_term = search_term

    searched_episodes_item = mc.ListItem()
    searched_episodes_item.SetLabel("Avsnitt för \"%s\"" %search_term)
    searched_episodes = client.get_episodes_from_search_term(search_term)
    searched_episodes_thread = AsyncTask(target=iterate, kwargs={"iterable":searched_episodes, "limit": 50})
    searched_episodes_thread.start()

    searched_shows_item = mc.ListItem()
    searched_shows_item.SetLabel("Program för \"%s\"" %search_term)
    searched_shows = client.get_shows_from_search_term(search_term, settings.show_premium())
    searched_shows = islice(searched_shows, 200)
    load_shows(searched_shows, searched_shows_item)

    mc.ShowDialogWait()
    searched_episodes_thread.join()
    searched_episodes = searched_episodes_thread.get_result()
    add_episodes(searched_episodes, searched_episodes_item)
    mc.HideDialogWait()

def click_settings():
    settings.activate()
def load_shows_from_category():
    global focused_group

    cList = mc.GetWindow(14000).GetList(1000)
    focused_group = 100
    cItem = cList.GetItem(cList.GetFocusedItem())
    category_id = cItem.GetProperty("id")

    episodes = client.get_episodes_from_category_id(category_id)
    latest_episodes_thread = AsyncTask(target=iterate, kwargs={"iterable":episodes, "limit":200})
    latest_episodes_thread.start()

    shows = client.get_shows_from_id(category_id, settings.show_premium())
    load_shows(shows, cItem)

    mc.ShowDialogWait()
    latest_episodes_thread.join()
    latest_episodes_item = mc.ListItem()
    latest_episodes_item.SetLabel("Senaste " + cItem.GetLabel())
    latest_for_category = latest_episodes_thread.get_result()
    add_episodes(latest_for_category, latest_episodes_item)
    mc.HideDialogWait()

def load_shows(shows, category_item):
    BPTraceEnter()
    mc.ShowDialogWait()
    set_shows([], mc.ListItem())
    set_episodes([], mc.ListItem())
    try:
        set_shows(shows, category_item)
        mc.HideDialogWait()
    except Exception, e:
        mc.HideDialogWait()
        track("Category Error", { "title": category_item.GetLabel(),
                                  "Id": mc.GetUniqueId()
                                })
        show_error_and_continue(message="Laddning av program misslyckades. Kollat internetanslutningen?\n\n" + str(e))
    track("Load Category", { "title": category_item.GetLabel(),
                             "Id": mc.GetUniqueId()
                           })
    BPLog("Finished loading programs in category %s." %category_item.GetLabel(), Level.DEBUG)
    BPTraceExit()

def load_recommended_episodes():
    recommended_item = mc.ListItem()
    recommended_item.SetLabel("Rekommenderade program")
    recommended_item.SetProperty("category", "preset-category")
    set_shows([], mc.ListItem())
    load_episodes(iterate(client.get_recommended_episodes(), 40), recommended_item)

def load_latest_full_episodes():
    mc.ShowDialogWait()
    latest_item = mc.ListItem()
    latest_item.SetLabel("Senaste program")
    latest_item.SetProperty("category", "preset-category")
    set_shows([], mc.ListItem())
    load_episodes(iterate(client.get_latest_full_episodes(), 200), latest_item)
    mc.HideDialogWait()

def load_live():
    live_item = mc.ListItem()
    live_item.SetLabel("Kanaler")
    live_item.SetProperty("category", "preset-category")
    set_shows([], mc.ListItem())
    load_shows(client.get_channels(), live_item)

def load_episodes_from_show():
    global focused_group

    cList = mc.GetWindow(14000).GetList(2001)
    focused_group = 2000
    cItem = cList.GetItem(cList.GetFocusedItem())
    if cItem.GetProperty("playable"):
        play_item(cItem)
    else:
        episodes = client.get_episodes_from_id(cItem.GetProperty("id"))
        store_show_list()
        load_episodes(episodes, cItem)

def load_episodes(episodes, show_item):
    BPTraceEnter()
    mc.ShowDialogWait()
    set_episodes([], mc.ListItem())
    try:
        set_episodes(episodes, show_item)
        mc.HideDialogWait()
    except Exception, e:
        mc.HideDialogWait()
        track("Show Error", { "title": show_item.GetLabel(),
                              "Id": mc.GetUniqueId(),
                              "category": show_item.GetProperty("category")
                            })
        show_error_and_continue(message="Laddning av avsnitt misslyckades. Kollat internetanslutningen?\n\n" + str(e), exception=e)
    track("Load Show", { "title": show_item.GetLabel(),
                         "Id": mc.GetUniqueId(),
                         "category": show_item.GetProperty("category")
                       })
    BPLog("Finished loading episodes in category %s." %show_item.GetLabel(), Level.DEBUG)
    BPTraceExit()

def set_shows(items, category_item):
    global labelPrograms
    global show_list_index

    BPTraceEnter()
    win = mc.GetWindow(14000)

    title = category_item.GetLabel()
    labelPrograms = title
    win.GetLabel(2002).SetLabel(title)

    target = win.GetList(2001)
    mc_list = mc.ListItems()
    for item in items:
        mc_list.append(show_to_list_item(item, title))
    target.SetItems(mc_list)
    show_list_index = 0
    if len(mc_list) > 0:
        win.GetLabel(2003).SetLabel("")
        target.SetFocus()
    else:
        win.GetLabel(2003).SetLabel(NO_SHOWS_TEXT)
    BPTraceExit()

def add_shows(items, category_item):
    BPTraceEnter()
    win = mc.GetWindow(14000)
    target = win.GetList(2001)
    mc_list = target.GetItems()
    for item in items:
        mc_list.append(show_to_list_item(item, category_item.GetLabel()))
    focusedIndex = target.GetFocusedItem()
    target.SetItems(mc_list)
    target.SetFocusedItem(focusedIndex)
    BPTraceExit()

def set_episodes(items, show_item):
    global labelEpisodes
    global episode_list_index

    BPTraceEnter()
    win = mc.GetWindow(14000)

    title = show_item.GetLabel()
    win.GetLabel(3002).SetLabel(title)
    labelEpisodes = title

    target = win.GetList(3001)
    mc_list = mc.ListItems()
    for item in items:
        mc_list.append(episode_to_list_item( item
                                           , show_item.GetProperty("category")
                                           , title
                                           ))
    target.SetItems(mc_list)
    episode_list_index = 0

    if len(mc_list) > 0:
        win.GetLabel(3003).SetLabel("")
        target.SetFocus()
    else:
        win.GetLabel(3003).SetLabel(NO_EPISODES_TEXT)

    BPTraceExit()

def add_episodes(items, show_item):
    global labelEpisodes

    BPTraceEnter()
    win = mc.GetWindow(14000)

    title = show_item.GetLabel()
    win.GetLabel(3002).SetLabel(title)
    labelEpisodes = title

    target = win.GetList(3001)
    mc_list = target.GetItems()
    for item in items:
        mc_list.append(episode_to_list_item( item
                                           , show_item.GetProperty("category")
                                           , show_item.GetLabel()
                                           ))
    if len(mc_list) > 0:
        win.GetLabel(3003).SetLabel("")

    focusedIndex = target.GetFocusedItem()
    target.SetItems(mc_list)
    target.SetFocusedItem(focusedIndex)
    BPTraceExit()

def click_episode():
    global focused_group

    focused_group = 3000
    item_list = mc.GetWindow(14000).GetList(3001)
    item = item_list.GetItem(item_list.GetFocusedItem())
    play_item(item)

def play_item(item):
    global category_list_index
    global show_list_index
    global episode_list_index
    BPTraceEnter()

    # Remember the selections in the lists
    store_category_list()
    store_show_list()
    store_episode_list()

    play_item = episode_list_item_to_playable(item)
    if (item.GetProperty("episode")):
        item_type="Episode"
    else:
        item_type="Clip"

    try:
        play_item = pirateplayable_item(play_item, settings.bitrate_limit())
    except NoStreamsError:
        track("Error",
                { "title": item.GetLabel(),
                  "url": item.GetPath(),
                  "Id": mc.GetUniqueId(),
                  "type": item_type,
                  "show": item.GetProperty("show"),
                  "category": item.GetProperty("category"),
                  "error_type": "No Streams"
                })
        show_error_and_continue(title="Inga strömmar", message="%s hade inga strömmar! Vi är beroende av pirateplay här, de kanske har problem." %play_item.GetLabel())
        BPTraceExit()
        return
    except NoSuitableStreamError:
        track("Error",
                { "title": item.GetLabel(),
                  "url": item.GetPath(),
                  "Id": mc.GetUniqueId(),
                  "type": item_type,
                  "show": item.GetProperty("show"),
                  "category": item.GetProperty("category"),
                  "error_type": "No Suitable Streams"
                })
        show_error_and_continue(title="Fel format", message="%s hade inga strömmar i rätt format. Vi vet inte hur vi ska spela upp de här strömmarna." %play_item.GetLabel())
        BPTraceExit()
        return

    BPLog("Playing clip \"%s\" with path \"%s\" and bitrate %s." %(play_item.GetLabel(), play_item.GetPath(), item.GetProperty("bitrate")))
    mc.GetPlayer().Play(play_item)

    track("Play", { "title": item.GetLabel(),
                    "url": item.GetPath(),
                    "Id": mc.GetUniqueId(),
                    "type": item_type,
                    "show": item.GetProperty("show"),
                    "category": item.GetProperty("category")
                  })
    BPTraceExit()

def move_left_from_episode_list():
    store_episode_list()
    win = mc.GetWindow(14000)
    menu = win.GetControl(100)
    shows = win.GetList(2001)
    if shows.GetItems():
        restore_show_list()
    else:
        menu.SetFocus()

def move_right_from_menu():
    win = mc.GetWindow(14000)
    shows = win.GetList(2001)
    episodes = win.GetList(3001)
    if shows.GetItems():
        restore_show_list()
    elif episodes.GetItems():
        restore_episode_list()

def move_left_from_show_list():
    store_show_list()
    mc.GetWindow(14000).GetControl(100).SetFocus()

def move_right_from_show_list():
    store_show_list()
    win = mc.GetWindow(14000)
    episodes = win.GetList(3001)
    if episodes.GetItems():
        restore_episode_list()

def store_show_list():
    global show_list_index
    show_list_index = mc.GetWindow(14000).GetList(2001).GetFocusedItem()

def restore_show_list():
    win = mc.GetWindow(14000)
    win.GetControl(2000).SetFocus()
    win.GetList(2001).SetFocusedItem(show_list_index)

def store_episode_list():
    global episode_list_index
    episode_list_index = mc.GetWindow(14000).GetList(3001).GetFocusedItem()

def restore_episode_list():
    win = mc.GetWindow(14000)
    win.GetControl(3001).SetFocus()
    win.GetList(3001).SetFocusedItem(episode_list_index)

def store_category_list():
    global category_list_index
    category_list_index = mc.GetWindow(14000).GetList(1000).GetFocusedItem()

def restore_category_list():
    win = mc.GetWindow(14000)
    win.GetControl(100).SetFocus()
    win.GetList(1000).SetFocusedItem(category_list_index)

def show_error_and_exit(title = "Tyvärr", message = "Ett oväntat fel har inträffat. Appen stängs...", exception = None):
    if exception is not None and IsEnabled(Level.DEBUG):
        raise
    BPLog("EXIT_ERROR_HANDLER. Title: %s, Message: %s" %(title, message), Level.ERROR)
    mc.ShowDialogOk(title, message)
    mc.CloseWindow()

def show_error_and_continue(title = "Tyvärr", message = "Ett oväntat fel har inträffat.", exception = None):
    if exception is not None and IsEnabled(Level.DEBUG):
        raise
    BPLog("CONTINUE_ERROR_HANDLER. Title: %s, Message: %s" %(title, message), Level.ERROR)
    mc.ShowDialogOk(title, message)

def track(name, data):
    if not initiated:
        return

    job_manager.addJob(TrackerJob(name, data))

def iterate(iterable, limit=None):
    if limit is None:
        return list(iterable)
    return list(islice(iterable, 0, limit))
