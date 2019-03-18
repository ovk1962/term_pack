#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  term_alarm.py
#
#=======================================================================
import os, sys, math, time
import logging
import smtplib
import sqlite3
from datetime import datetime, timezone
import operator
if sys.version_info[0] >= 3:
    import PySimpleGUI as sg
else:
    import PySimpleGUI27 as sg
#=======================================================================
class Class_LOGGER():
    def __init__(self, path_log):
        #self.logger = logging.getLogger(__name__)
        self.logger = logging.getLogger('__main__')
        self.logger.setLevel(logging.INFO)
        # create a file handler
        self.handler = logging.FileHandler(path_log)
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
class Class_SQLite():
    def __init__(self, path_db):
        self.path_db = path_db
        self.table_db = []
        self.conn = ''
        self.cur = ''
    #-------------------------------------------------------------------
    def check_db(self):
        '''  check FILE of DB SQLite    -----------------------------'''
        #    return os.stat: if FILE is and size != 0
        r_check_db = [0, '']
        name_path_db = self.path_db
        if not os.path.isfile(name_path_db):
            r_check_db = [1, 'can not find file']
        else:
            buf_st = os.stat(name_path_db)
            if buf_st.st_size == 0:
                r_check_db = [1, buf_st]
            else:
                r_check_db = [0, buf_st]
        return r_check_db
    #-------------------------------------------------------------------
    def reset_table_db(self, name_tbl):
        ''' reset data in table DB  ---------------------------------'''
        r_reset_tbl = [0, '']
        try:
            self.conn = sqlite3.connect(self.path_db)
            self.cur = self.conn.cursor()
            self.cur.execute("DELETE FROM " + name_tbl)
            self.conn.commit()
            self.cur.close()
            self.conn.close()
            r_reset_tbl = [0, 'OK']
        except Exception as ex:
            r_reset_tbl = [1, str(ex)]
        return r_reset_tbl
    #-------------------------------------------------------------------
    def rewrite_table(self, name_tbl, name_list, val = '(?, ?)'):
        ''' rewrite data from table ARCHIV_PACK & PACK_TODAY & DATA ----'''
        r_rewrt_tbl = [0, '']
        try:
            self.conn = sqlite3.connect(self.path_db)
            self.cur = self.conn.cursor()
            self.cur.execute("DELETE FROM " + name_tbl)
            self.cur.executemany("INSERT INTO " + name_tbl + " VALUES" + val, name_list)
            self.conn.commit()
            self.cur.close()
            self.conn.close()
            r_rewrt_tbl = [0, 'OK']
        except Exception as ex:
            r_rewrt_tbl = [1, str(ex)]
        return r_rewrt_tbl
    #-------------------------------------------------------------------
    def write_table_db(self, name_tbl, name_list):
        ''' write data string into table DB  ------------------------'''
        r_write_tbl = [0, '']
        try:
            self.conn = sqlite3.connect(self.path_db)
            self.cur = self.conn.cursor()
            self.cur.executemany("INSERT INTO " + name_tbl + " VALUES(?, ?)", name_list)
            self.conn.commit()
            self.cur.close()
            self.conn.close()
            r_write_tbl = [0, 'OK']
        except Exception as ex:
            r_write_tbl = [1, str(ex)]
        return r_write_tbl
    #-------------------------------------------------------------------
    def get_table_db_with(self, name_tbl):
        ''' read one table DB  --------------------------------------'''
        r_get_table_db = []
        self.conn = sqlite3.connect(self.path_db)
        try:
            with self.conn:
                self.cur = self.conn.cursor()
                #self.cur.execute("PRAGMA busy_timeout = 3000")   # 3 s
                self.cur.execute("SELECT * from " + name_tbl)
                self.table_db = self.cur.fetchall()    # read table name_tbl
                r_get_table_db = [0, self.table_db]
        except Exception as ex:
            r_get_table_db = [1, name_tbl + str(ex)]

        return r_get_table_db
#=======================================================================
class Class_PACK():
    def __init__(self):
        self.ind= 0
        self.dt = ''
        self.tm = ''
        self.pAsk = 0.0
        self.pBid = 0.0
        self.EMAf = 0.0
        self.EMAf_rnd = 0.0
        self.cnt_EMAf_rnd = 0.0
        self.AMA = 0.0
        self.AMA_rnd = 0.0
        self.cnt_AMA_rnd = 0.0
#=======================================================================
class Class_CONTR():
    def __init__(self, db_path_PACK, log_path):
        #
        self.db_path_PACK = db_path_PACK   # path DB archiv
        self.db_PACK      = Class_SQLite(db_path_PACK)
        #
        self.hist_pack       = []   # массив котировок packets 60 s
        self.hist_pack_today = []   # массив котировок packets 60 s
        #
        self.num_packs = 0
        self.str_hist_last = []
        #
        self.log  = Class_LOGGER(log_path)
        self.log.wr_log_info('*** START ***')
#=======================================================================
def error_msg_popup(cntr, msg_log, msg_rq_1, PopUp = True):
    cntr.log.wr_log_error(msg_log + msg_rq_1)
    if PopUp == True:
        sg.PopupError(msg_log + msg_rq_1)
#=======================================================================
def init_cntr(cntr):
    # read table hist_PACK
    rq  = get_hist_PACK(cntr)
    if rq[0] != 0:
        error_msg_popup(cntr, 'hist_PACK => ', str(rq[1]))
        return [1, 'hist_PACK => ' + str(rq[1])]

    # read table hist_PACK_today
    rq  = get_hist_PACK_today(cntr)
    if rq[0] != 0:
        error_msg_popup(cntr, 'hist_PACK_today => ', str(rq[1]))
        return [1, 'hist_PACK_today => ' + str(rq[1])]

    cntr.num_packs = len(cntr.hist_pack)
    if len(cntr.hist_pack_today) == 0:
        for i_mdl in range(cntr.num_packs):
            buf = cntr.hist_pack[i_mdl][-1]
            cntr.str_hist_last.append(buf)
        print('buf = ', len(cntr.str_hist_last))
    else:
        for i_mdl in range(cntr.num_packs):
            buf = cntr.hist_pack_today[i_mdl][-1]
            cntr.str_hist_last.append(cntr.hist_pack_today[i_mdl][-1])
        print('buf = ', len(cntr.str_hist_last))

    print('hist_PACK       = ', len(cntr.hist_pack))
    print('hist_PACK_today = ', len(cntr.hist_pack_today))
    print('init_cntr - OK')
    return [0, 'OK']
#=======================================================================
def conv_hist_PACK(arr_pack):
    if len(arr_pack) == 0: return [1, 'arr_pack is empty']
    str_pack = arr_pack[0][1].split('|')
    #print(str_pack)
    num_pack = len(str_pack) - 1
    hist_pack = []
    for i_mdl in range(num_pack):
        print(i_mdl)
        hist_pack.append([])
        for item in arr_pack:
            str_pack = item[1].replace(',','.').split('|')
            del str_pack[-1]
            str_mdl  = str_pack[0].split(' ')   # dt tm for all packets
            buf_p = Class_PACK()
            buf_p.ind= int(item[0])
            buf_p.dt = str_mdl[0]
            buf_p.tm = str_mdl[1]
            if i_mdl == 0:
                buf_p.pAsk = float(str_mdl[2])
                buf_p.pBid = float(str_mdl[3])
                buf_p.EMAf = float(str_mdl[4])
                buf_p.EMAf_rnd     = float(str_mdl[5])
                buf_p.cnt_EMAf_rnd = float(str_mdl[6])
                buf_p.AMA          = float(str_mdl[7])
                buf_p.AMA_rnd      = float(str_mdl[8])
                buf_p.cnt_AMA_rnd  = float(str_mdl[9])
            else:
                str_mdl  = str_pack[i_mdl].split(' ')
                buf_p.pAsk = float(str_mdl[0])
                buf_p.pBid = float(str_mdl[1])
                buf_p.EMAf = float(str_mdl[2])
                buf_p.EMAf_rnd     = float(str_mdl[3])
                buf_p.cnt_EMAf_rnd = float(str_mdl[4])
                buf_p.AMA          = float(str_mdl[5])
                buf_p.AMA_rnd      = float(str_mdl[6])
                buf_p.cnt_AMA_rnd  = float(str_mdl[7])

            hist_pack[i_mdl].append(buf_p)
    #print(hist_pack[12][-1].dt)
    #print(hist_pack[12][-1].tm)
    #print(hist_pack[12][-1].pAsk)
    #print(hist_pack[12][-1].EMAf)
    return [0, hist_pack]
#=======================================================================
def get_hist_PACK(cntr):
    # read table hist_PACK from DB cntr.db_PACK
    rq  = cntr.db_PACK.get_table_db_with('hist_PACK')
    if rq[0] != 0:
        error_msg_popup(cntr, 'Error hist_PACK! => ', str(rq[1]), PopUp = True)
        return [1, rq[1]]
    print(len(rq[1])   )
    print(    rq[1][0] )
    print(    rq[1][-1])
    req = conv_hist_PACK(rq[1])
    if req[0] == 0:
        cntr.hist_pack  = req[1][:]
    else:
        cntr.hist_pack  = []
    return [0, 'OK']
#=======================================================================
def get_hist_PACK_today(cntr):
    # read table hist_PACK_today from DB cntr.db_PACK
    rq  = cntr.db_PACK.get_table_db_with('hist_PACK_today')
    if rq[0] != 0:
        error_msg_popup(cntr, 'Error hist_PACK_today! => ', str(rq[1]), PopUp = True)
        return [1, rq[1]]
    if len(rq[1]) != 0:
        print(len(rq[1])   )
        print(    rq[1][0] )
        print(    rq[1][-1])
    req = conv_hist_PACK(rq[1])
    if req[0] == 0:
        cntr.hist_pack_today  = req[1][:]
    else:
        cntr.hist_pack_today  = []
    return [0, 'OK']
#=======================================================================
def main():
    # init program config
    dirr, sub_dirr = os.path.abspath(os.curdir), '\\DB\\'
    path_PACK = 'term_pack.sqlite'
    db_path_PACK = dirr + sub_dirr + path_PACK
    name_trm, log_path = 'TERM_ALARM_1.00', dirr + '\\LOG\\term_alarm_logger.log'

    # init CONTR
    cntr = Class_CONTR(db_path_PACK, log_path)
    init_cntr(cntr)

    # init MENU
    menu_def = [
                ['Mode',    ['auto', 'manual', ],],
                ['Help', 'About...'],
                ['Exit', 'Exit']
                ]

    sg_pack=[
            #'0 all FUT   vs  -120:MX',
            #'1 3:GZ,1:LK,1:RS,-60:MX ',
            #'2 1:SR,6:VB,2:SP,-30:MX ',
            #'3 4:HR,1:FS,2:AL,-30:MX ',
            #'4  ____1:SR,2:SP,-20:MX ',
            #'5  ____3:GZ,     -20:MX ',
            #'6  ____1:LK,     -20:MX ',
            #'7  ____1:RS,     -20:MX ',
            #'8  __6:VB,    -10:MX ',
            #'9  __4:HR,    -10:MX ',
            #'10 __1:FS,    -10:MX ',
            #'11 __2:AL,    -10:MX ',
            #'12 1:LK,1:RS,4:HR,2:AL,-60:MX'
            '0 all FUT vs -350:MX',
            '1 2:SR,1:SP,-30:MX',
            '2 5:GZ,-30:MX',
            '3 1:LK,-20:MX',
            '4 2:RS,-30:MX',
            '5 20:VB,-30:MX',
            '6 14:HR,-30:MX',
            '7 4:FS,-30:MX',
            '8 1:TT,-30:MX',
            '9 1:SG,1:SN-30:MX',
            '10 8:AL,-30:MX',
            '11 3:MT,-30:MX',
            '12 special vs -240:MX'
            ]

    tab_PACK = []
    for i in range(13):
        inputs = [sg.T(sg_pack[i], justification='left', size=(24, 1))]
        s = [
            cntr.str_hist_last[i].pAsk,
            cntr.str_hist_last[i].pBid,
            cntr.str_hist_last[i].EMAf_rnd,
            cntr.str_hist_last[i].cnt_EMAf_rnd
            ]
        inputs += [
                    sg.In('{}'.format(int(s[j])),
                    justification='right', size=(7, 1), pad=(1, 1),
                    key=('p', i, j),   do_not_clear=True)
                    for j in range(4)
                    ]
        inputs += [sg.Checkbox((''), key = 'chk_box' + str(i))]
        tab_PACK.append(inputs)

    tab_s_EMA = []
    for i in range(13):
        inputs = [sg.T(sg_pack[i], justification='left', size=(24, 1))]
        inputs += [
                    sg.T('{}_{}'.format(i,j),
                    justification='right', size=(8, 1), pad=(1, 1),
                    key=('e', i, j))
                    for j in range(4)
                    ]
        tab_s_EMA.append(inputs)

    # Display data
    sg.SetOptions(element_padding=(0,0))

    layout = [
                [sg.Menu(menu_def, tearoff=False, key='menu_def')],
                [sg.TabGroup([[sg.Tab('PACK', tab_PACK), sg.Tab('s_EMA', tab_s_EMA)]], key='tab_group')],
                [sg.T('',size=(60,2), font='Helvetica 8', key='txt_status'), sg.Quit(auto_size_button=True)],
             ]

    window = sg.Window(name_trm, grab_anywhere=True).Layout(layout).Finalize()

    mode = 'auto'
    frm_str = '{: <15}{: ^15}'
    # main cycle   -----------------------------------------------------
    while True:
        stroki = []
        if mode == 'auto':
            event, values = window.Read(timeout=25000 )  # period 25 sec
        else:
            event, values = window.Read(timeout=255000)
        #print('event = ', event, ' ..... values = ', values)

        if event is None        : break
        if event == 'Quit'      : break
        if event == 'Exit'      : break
        if event == 'auto'      : mode = 'auto'
        if event == 'manual'    : mode = 'manual'
        if event == 'About...'  :
            location = ('p', 1, 0)
            target_element = window.FindElement(location).Update(sg_pack[0])
            #target_element.Update(sg_pack[0])

        if event == '__TIMEOUT__':
            # read tbl hist_pack_today and check alarms
            if len(cntr.hist_pack_today) != 0:
                for i_mdl in range(cntr.num_packs):
                    buf = cntr.hist_pack_today[i_mdl][-1]
                    cntr.str_hist_last.append(cntr.hist_pack_today[i_mdl][-1])

        txt_frmt = '%Y.%m.%d  %H:%M:%S'
        stts  = time.strftime(txt_frmt, time.localtime()) + '\n'
        stts += 'event = ' + event
        window.FindElement('txt_status').Update(stts)
    return

if __name__ == '__main__':
    import sys
    sys.exit(main())
