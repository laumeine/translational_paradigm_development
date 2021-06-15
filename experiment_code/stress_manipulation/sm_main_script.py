#  -*- coding: utf-8 -*-
# For German instructions: write a u before every string that contains Umlaute (u'...')

import ConfigParser

import os

from utils.dialog_box import DialogBox

# from human_shuttlebox import HumanShuttlebox
# import parameters as params
from groups import Groups
from utils.shock_handler import Shocker
#from utils.shock_handler import Empty_Shocker


CONFIG_PATH = "stress_manipulation/configs/default_config_%s"

def ConfigSectionMap(Config, section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option.upper()] = Config.get(section, option)
            if dict1[option.upper()] == -1:
                print("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option.upper()] = None
    return dict1


def main(dlg_data):
    # files = gui.fileOpenDlg('C:\\KatjaExp', prompt='Choose a sibling')
    # print files
    config_path = CONFIG_PATH%dlg_data[1]
    print os.path.abspath(config_path)
    conf = ConfigParser.ConfigParser()

    # send event marker for physiological measures - start of stress manipulation
    shocker = Shocker()
    #shocker = Empty_Shocker() # original
    shocker.send_event_marker()

    
    conf.read(config_path)
    config = ConfigSectionMap(conf, "SM")
    if dlg_data[1] == "EC":
        group = Groups(1, dlg_data, config)
        group.sm_group_1()
    elif dlg_data[1] == "YC":
        group = Groups(2, dlg_data, config)
        group.sm_group_2()
    elif dlg_data[1] == "CC":
        group = Groups(3, dlg_data, config)
        group.sm_group_3()

    shocker.send_event_marker()

    # close the window
    group.win.winHandle.minimize() # Minimize to avoid black screen.
    group.win.close()


if __name__ == '__main__':
    # Display dialog
    dlg = DialogBox({})
    data = dlg.show_dlg()
    # run
    main(dlg_data=data)
