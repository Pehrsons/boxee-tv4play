#encoding:utf-8

import mc

outside_sweden = False

def set_outside_sweden(out_of_swe):
    global outside_sweden
    outside_sweden = out_of_swe

def category_to_list_item(item):
    list_item = mc.ListItem(mc.ListItem.MEDIA_UNKNOWN)
    list_item.SetProperty("id", item["id"])
    list_item.SetTitle(item["name"])
    list_item.SetLabel(item["name"])
    return list_item

def show_to_list_item(item, category="undefined"):
    list_item = mc.ListItem(mc.ListItem.MEDIA_UNKNOWN)
    list_item.SetProperty("category", item["category_id"])
    list_item.SetProperty("id", item["id"])
    list_item.SetTitle(item["name"])
    list_item.SetLabel(item["name"])
    if "text" in item: list_item.SetDescription(item["text"])
    # Legacy SVT stuff, leaving it for reference.
    #list_item.SetPath(item["image_highres"])
    #if "viewable_in" in item and outside_sweden and item["viewable_in"] == 2: list_item.SetWriter("can't watch")
    #if "kind_of" in item and item["kind_of"] == 2: list_item.SetDirector("this is a clip")
    #if "kind_of" in item and item["kind_of"] == 3: list_item.SetArtist("this is live material")
    #if "kind_of" in item and item["kind_of"] > 0: list_item.SetProperty("playable", "True")
    if item["image_highres"] != "":
        # Set thumbnail only if it is not the default tv4 image. UI can handle
        # it better when it can detect whether a real thumb exists or not.
        list_item.SetThumbnail(get_image_size(item["image_highres"], "480x270"))
        #list_item.SetIcon(item["logo"]) # ListItem.Icon in UI shows the Thumbnail ...
    return list_item

def episode_to_list_item(item, category="undefined", show="undefined"):
    if item["full_program"]: # EPISODE
        list_item = mc.ListItem(mc.ListItem.MEDIA_VIDEO_EPISODE)
        list_item.SetProperty("episode", "true")
    else: # CLIP
        list_item = mc.ListItem(mc.ListItem.MEDIA_VIDEO_CLIP)
        list_item.SetProperty("clip", "true")
    # XXX API does not provide info on recommended episodes.
    #if item["recommended"]: list_item.SetProperty("recommended", "true")
    if not item["availability"]["geo_restricted"]: list_item.SetProperty("viewable_in_world", "true")
    if outside_sweden and item["availability"]["geo_restricted"]: list_item.SetWriter("can't watch")
    if not item["full_program"]: list_item.SetDirector("this is a clip")
    if item["availability"]["live"]: list_item.SetArtist("this is live material")
    list_item.SetProperty("playable", "True")
    if category == "undefined": list_item.SetProperty("category", item["categoryids"][0])
    else: list_item.SetProperty("category", category)
    if show == "undefined": list_item.SetProperty("show", item["categoryids"][-1])
    else: list_item.SetProperty("show", show)
    list_item.SetPath("%s/%s" %(item["nid"], item["vmanprogid"]))
    list_item.SetProperty("id", item["vmanprogid"])
    list_item.SetTitle(item["name"])
    list_item.SetLabel(item["name"])
    if item["lead"] is not None: list_item.SetDescription(item["lead"])
    list_item.SetProperty("date_available_until", repr(item["offdate"]))
    list_item.SetProperty("date_broadcasted", repr(item["ontime"]))
    date_time = repr(item["ontime"])
    year = date_time[0:4]
    month = date_time[4:6]
    day = date_time[6:8]
    list_item.SetDate(int(year),
                      int(month),
                      int(day))

    # XXX No length in api yet (2013-12-29). Add duration when available.
    #list_item.SetProperty("length", item["length"])
    #duration_array = item["length"].split()
    #duration = sum(map(parse_duration, zip(duration_array[1::2], duration_array[::2])))
    #list_item.SetDuration(duration)
    #info = "Längd: " + item["length"]

    # We have human readable availability info available, so use that instead.
    #info += "\nPublicerat: %s/%s/%s" %(year,month,day)
    #info += "\nTillgänglig till och med " + item["date_available_until"].split("T")[0]
    #if outside_sweden:
    #    info += {
    #        "false": "\nKan ses i hela världen",
    #        "true":  "\nKan bara ses i Sverige"
    #    }[item["availability"]["geo_restricted"]]
    info = item["availability"]["human"]
    info += {
        True:  "\nTyp: Avsnitt",
        False: "\nTyp: Klipp"
    }[item["full_program"]]
    list_item.SetStudio(info)
    list_item.SetThumbnail(get_image_size(item["metaimage"], "480x270"))
    list_item.SetIcon(get_image_size(item["metaimage"], "480x270")) # ListItem.Icon in UI shows the Thumbnail ...
    return list_item

def get_image_size(url, size):
    if "[width]" in url:
        url = url.replace("[width]", size, 1)
    elif "520x292" in url:
        url = url.replace("520x292", size, 1)
    return url

def episode_list_item_to_playable(item):
    play = mc.ListItem(item.GetMediaType())
    play.SetPath("http://tv4play.se/program/x?video_id=%s" %item.GetProperty("id"))
    play.SetDescription(item.GetDescription())
    play.SetTitle(item.GetTitle())
    play.SetLabel(item.GetLabel())
    play.SetDuration(item.GetDuration())
    play.SetThumbnail(item.GetThumbnail())
    play.SetIcon(item.GetIcon())
    return play

