#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  term_today.py
#
#=======================================================================
import os
import sys
import math
import time
import logging
import smtplib
import sqlite3
from datetime import datetime
from datetime import timezone
if sys.version_info[0] >= 3:
    import PySimpleGUI as sg
else:
    import PySimpleGUI27 as sg
#=======================================================================
class Class_LOGGER():
    def __init__(self):
        #self.logger = logging.getLogger(__name__)
        self.logger = logging.getLogger('__main__')
        self.logger.setLevel(logging.INFO)
        # create a file handler
        self.handler = logging.FileHandler('_logger.log')
        self.handler.setLevel(logging.INFO)
        # create a logging format
        #self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.handler.setFormatter(self.formatter)

        # add the handlers to the logger
        self.logger.addHandler(self.handler)
    #-------------------------------------------------------------------
    def wr_log_info(self, msg):
        self.logger.info(msg)
    #-------------------------------------------------------------------
    def wr_log_error(self, msg):
        self.logger.error(msg)
#=======================================================================

#=======================================================================
def main():
    name_trm = 'TRM_TODAY_1.00'
    menu_def = [
                ['Test', ['Test SQL',  ['SQL tbl DATA', 'SQL tbl TODAY', ],],],
                ['Help', 'About...'],
                ['Exit', 'Exit']
                ]
    tab_BALANCE =  [
                    [sg.T('This is inside tab_BALANCE', key='BALANCE')],
                   ]
    tab_DATA    =  [
                    [sg.T('This is inside tab_DATA', key='DATA')],
                   ]
    #-------------------------------------------------------------------
    # Display data in a table format
    #-------------------------------------------------------------------
    sg.SetOptions(element_padding=(0,0))

    layout = [
                [sg.Menu(menu_def, tearoff=False, key='menu_def')],
                [sg.TabGroup([[sg.Tab('BALANCE', tab_BALANCE), sg.Tab('DATA', tab_DATA)]], key='tab_group')],
             ]

    #form = sg.FlexForm(name_trm, return_keyboard_events=True, grab_anywhere=False, use_default_focus=False)
    #form.Layout(layout)

    window = sg.Window(name_trm, grab_anywhere=True).Layout(layout).Finalize()

    mode = 'auto'
    tm_out = 3000
    # main cycle   -----------------------------------------------------
    while True:
        if mode == 'auto':
            event, values = window.Read(timeout=tm_out)  # period 52 sec
        else:
            event, values = window.Read()  # period 3 sec
        print('event = ', event, ' ..... values = ', values)

        if event is None            : break
        if event == 'Exit'          : break

#=======================================================================
if __name__ == '__main__':
    import sys
    sys.exit(main())
