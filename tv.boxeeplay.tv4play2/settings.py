#encoding:utf-8
#author:Andreas Pehrson
#project:boxeeplay.tv

import mc
from logger import BPLog, Level

BITRATE_LIMIT_KEY = "bitrate_limit"
SHOW_PREMIUM_KEY = "show_premium"

def conf():
    return mc.GetApp().GetLocalConfig()

def activate():
    decision = mc.ShowDialogSelect("Jag vill ändra...", [ get_option_bitrate_limit(), get_option_show_premium() ])
    if decision == 0:
        activate_bitrate_limit_selection()
    if decision == 1:
        activate_show_premium_selection()

def activate_bitrate_limit_selection():
    cont = mc.ShowDialogConfirm("Ändra bandbreddsbegränsning", "Normalt spelar vi upp strömmarna med högsta möjliga kvalitet. Har du då problem med hackig och buffrande uppspelning kan du här ställa in en gräns för hur hög bitrate vi får välja.", "Avbryt", "Fortsätt")
    if not cont:
        return

    options = [ "Obegränsat", "2500 Kbps", "2000 Kbps", "1500 Kbps", "1000 Kbps", "500 Kbps" ]
    option_values = [ -1, 2500, 2000, 1500, 1000, 500 ]
    limit = bitrate_limit()
    active_value_index = 0
    try: active_value_index = option_values.index(limit)
    except: BPLog("Value %d not found in list of bitrate limit options" %limit, Level.WARNING)
    options[active_value_index] = "[valt] " + options[active_value_index]
    decision = mc.ShowDialogSelect("Begränsa bandbredd", options)

    if decision == -1:
        BPLog("Bitrate limit dialog cancelled")
        return

    chosen_limit = option_values[decision]
    set_bitrate_limit(chosen_limit)
    BPLog("Bitrate limit set to %d kbps (%s)" %(chosen_limit, options[decision]))

def bitrate_limit():
    limit = conf().GetValue(BITRATE_LIMIT_KEY)
    if limit == "": return -1
    else: return int(limit)

def set_bitrate_limit(limit):
    conf().SetValue(BITRATE_LIMIT_KEY, str(limit))

def get_option_bitrate_limit():
    opt = "Bandbreddsbegränsning: "
    limit = bitrate_limit()
    if limit == -1:
        opt += "Obegränsat"
    else:
        opt += "%d kbps" %limit
    return opt

def activate_show_premium_selection():
    cont = mc.ShowDialogConfirm("Premiumprogram", "De flesta premiumprogram har inget gratisinnehåll utan dyker då upp tomma i programlistan. Aktivera för att kunna bläddra bland dessa program (en del har gratisklipp). Videor som är premium stöds inte.", "Avbryt", "Fortsätt")
    if not cont:
        return

    options = [ "Visa premiumprogram", "Visa inte premiumprogram" ]
    option_values = [ True, False ]
    activated = show_premium()
    active_value_index = 0
    try: active_value_index = option_values.index(activated)
    except: BPLog("Value %s not found in list of show premium options" %str(activated), Level.WARNING)
    options[active_value_index] = "[valt] %s" %options[active_value_index]
    decision = mc.ShowDialogSelect("Ändra visning av premiumprogram", options)

    if decision == -1:
        BPLog("Show premium dialog cancelled")

    set_show_premium(option_values[decision])
    BPLog("Show premium set to %s (%s)" %(str(option_values[decision]), options[decision]))

def show_premium():
    return conf().GetValue(SHOW_PREMIUM_KEY) != "False"

def set_show_premium(show_premium):
    conf().SetValue(SHOW_PREMIUM_KEY, str(show_premium))

def get_option_show_premium():
    opt = "Visa premium: "
    if show_premium():
        opt += "Ja"
    else:
        opt += "Nej"
    return opt
