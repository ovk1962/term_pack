#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  term_graph.py
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
    ''' There are 2 history tables of FUT -
    file_path_DATA  - file data from terminal QUIK
    db_path_FUT     - TABLE s_hist_1, ask/bid from TERMINAL 1 today (TF = 15 sec)
    db_path_FUT_arc - TABLE archiv,   ask/bid for period  (TF = 60 sec)
    TABLE total_pack_archiv should update one time per DAY
    TABLE total_pack_today  should update one time per MINUTE
    '''
    def __init__(self, db_path_PACK, log_path):
        #
        self.db_path_PACK = db_path_PACK   # path DB archiv
        self.db_PACK      = Class_SQLite(db_path_PACK)
        #
        self.hist_pack       = []   # массив котировок packets 60 s
        self.hist_pack_today = []   # массив котировок packets 60 s
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
        error_msg_popup(cntr, 'get_hist_PACK => ', str(rq[1]))
        return [1, 'get_hist_PACK => ' + str(rq[1])]

    # read table hist_PACK_today
    rq  = get_hist_PACK_today(cntr)
    if rq[0] != 0:
        error_msg_popup(cntr, 'hist_PACK_today => ', str(rq[1]))
        return [1, 'hist_PACK_today => ' + str(rq[1])]

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
def refresh_graph(cntr, values, graph):
    graph.Erase()
    y_pack, y_gr_1, y_gr_2, y_gr_12 , y_gr_22 = [], [], [], [], []
    x_up, x_down   = [], []
    f_mode = [1, 5, 15, 30, 60, 120]

    if   values['TF'][0] == ' 1 min':   TF_mode = 0
    elif values['TF'][0] == ' 5 min':   TF_mode = 1
    elif values['TF'][0] == '15 min':   TF_mode = 2
    elif values['TF'][0] == '30 min':   TF_mode = 3
    elif values['TF'][0] == '60 min':   TF_mode = 4
    elif values['TF'][0] == '120 min':  TF_mode = 5
    else:                               TF_mode = 0

    print('len = ', len(cntr.hist_pack))
    for i_pack, item in enumerate(cntr.hist_pack):
        y_pack.append([])
        y_pack[i_pack] = [x for x in cntr.hist_pack[i_pack]]
    if len(cntr.hist_pack_today) != 0:
        for i_pack, item in enumerate(cntr.hist_pack_today):
            y_pack[i_pack] += [x for x in cntr.hist_pack_today[i_pack]]

    x_dt = [x.dt for x in y_pack[0]]
    x_tm = [x.tm for x in y_pack[0]]

    y_pack_1  = [int((y.pAsk+y.pBid)/2) for y in y_pack[0]]
    y_emaf_1  = [y.EMAf_rnd             for y in y_pack[0]]
    nom_PACK = int(values['PACK'].split(' ')[0])
    y_pack_2  = [int((y.pAsk+y.pBid)/2) for y in y_pack[nom_PACK]]
    y_emaf_2  = [y.EMAf_rnd             for y in y_pack[nom_PACK]]

    len_y = len(y_pack_1)
    sz_L, sz_W = graph.TopRight[0]-5, graph.TopRight[1]-5

    x_scale = f_mode[TF_mode]
    if len_y > x_scale * sz_L:   i_start = len_y - x_scale * sz_L
    else:                        i_start = 0

    for x in range(i_start, len_y-1, x_scale):
        if x < len_y:
            x_up.append(x_dt[x])
            x_down.append(x_tm[x])
            y_gr_1.append (y_pack_1[x])
            y_gr_2.append (y_emaf_1[x])
            y_gr_12.append(y_pack_2[x])
            y_gr_22.append(y_emaf_2[x])

    k_max = [max(y_gr_1), max(y_gr_2)]
    index, value = max(enumerate(k_max), key=operator.itemgetter(1))
    if   index == 0: k_max = 100 + max(y_gr_1)
    elif index == 1: k_max = 100 + max(y_gr_2)

    k_min = [min(y_gr_1), min(y_gr_2)]
    index, value = min(enumerate(k_min), key=operator.itemgetter(1))
    if   index == 0: k_min = min(y_gr_1) - 100
    elif index == 1: k_min = min(y_gr_2) - 100

    k_max = 100 * math.ceil(k_max/100)
    k_min = 100 * int(k_min/100)
    k_gr = sz_W / (k_max - k_min)

    k_max_2 = [max(y_gr_12), max(y_gr_22)]
    index, value = max(enumerate(k_max_2), key=operator.itemgetter(1))
    if   index == 0: k_max_2 = 100 + max(y_gr_12)
    elif index == 1: k_max_2 = 100 + max(y_gr_22)

    k_min_2 = [min(y_gr_12), min(y_gr_22)]
    index, value = min(enumerate(k_min_2), key=operator.itemgetter(1))
    if   index == 0: k_min_2 = min(y_gr_12) - 100
    elif index == 1: k_min_2 = min(y_gr_22) - 100

    k_max_2 = 100 * math.ceil(k_max_2/100)
    k_min_2 = 100 * int(k_min_2/100)
    k_gr_2 = sz_W / (k_max_2 - k_min_2)

    # Draw axis X
    for x in range(104, len(x_up), 104):
        graph.DrawLine((x,25), (x,sz_W-0), color='lightgrey')
        graph.DrawText( x_up[x], (x,3), color='black')
        graph.DrawText( x_down[x], (x,18), color='black')

    # Draw axis Y
    for y in range(50, sz_W , 50):
        graph.DrawLine((25, y), (sz_L, y), color='lightgrey')
        k_text = int(k_min + y / k_gr)
        graph.DrawText(k_text , (15, y), color='green')

    graph.DrawText('Delta Y = ' + str(k_max - k_min) ,
        (35, sz_W - 5),
        color='green')
    graph.DrawText('Delta Y2 = ' + str(k_max_2 - k_min_2) ,
        (sz_L - 55, sz_W - 5),
        color='blue')

    # Draw Graph Y1 (Left)
    for i, item in enumerate(y_gr_1):
        if i != 0:
            prev = int((pr_item - k_min) * k_gr)
            cur  = int((item - k_min) * k_gr)
            graph.DrawLine((i-1, prev), (i, cur), color='green')
        pr_item = item
    for i, item in enumerate(y_gr_2):
        cur  = int((item - k_min) * k_gr)
        graph.DrawCircle((i, cur), 2, line_color='red', fill_color='red')
    # Draw Graph Y2 (Right)
    for i, item in enumerate(y_gr_12):
        if i != 0:
            prev = int((pr_item - k_min_2) * k_gr_2)
            cur  = int((item - k_min_2) * k_gr_2)
            graph.DrawLine((i-1, prev), (i, cur), color='blue')
        pr_item = item
    for i, item in enumerate(y_gr_22):
        cur  = int((item - k_min_2) * k_gr_2)
        graph.DrawCircle((i, cur), 2, line_color='lightblue', fill_color='lightblue')
#=======================================================================
def main():
    # init program config
    dirr, sub_dirr = os.path.abspath(os.curdir), '\\DB\\'
    path_PACK = 'term_pack.sqlite'
    db_path_PACK = dirr + sub_dirr + path_PACK
    name_trm, log_path = 'TERM_GRAPH_1.00', dirr + '\\LOG\\term_graph_logger.log'

    # init CONTR
    cntr = Class_CONTR(db_path_PACK, log_path)
    init_cntr(cntr)

    #-------------------------------------------------------------------
    # init PySimpleGUI
    #-------------------------------------------------------------------
    sz_W, sz_L = 500, 1040
    sg.SetOptions(element_padding=(0,0))

    grafic = sg.Graph(canvas_size=(sz_L, sz_W),
                    graph_bottom_left=(  -5,     -5),
                    graph_top_right=(sz_L+5, sz_W+5),
                    background_color= 'lightyellow', #'white',
                    key='graph')
    sg_txt= [sg.T(' Just for sure MODE =        ',  font='Helvetica 8')]
    sg_pack=[
            #'0 ___all FUT vs -120:MX',
            #'1 3:GZ,1:LK,1:RS,-60:MX',
            #'2 1:SR,6:VB,2:SP,-30:MX',
            #'3 4:HR,1:FS,2:AL,-30:MX',
            #'4 _____1:SR,2:SP,-20:MX',
            #'5 _____3:GZ,     -20:MX',
            #'6 _____1:LK,     -20:MX',
            #'7 _____1:RS,     -20:MX',
            #'8  __6:VB,    -10:MX',
            #'9  __4:HR,    -10:MX',
            #'10 __1:FS,    -10:MX',
            #'11 __2:AL,    -10:MX',
            #'12 1:GZ,1:RS,6:VB,4:HR,2:AL,-60:MX'
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
    layout= [
                [
                 sg.Radio('AUTO',   "RADIO1", key='auto',   enable_events=True, default=True),
                 sg.Radio('MANUAL', "RADIO1", key='manual', enable_events=True),
                 sg.T(' ' * 15),
                 sg.Listbox(values=(' 1 min', ' 5 min', '15 min', '30 min', '60 min', '120 min'),
                    size=(10, 2), default_values=' 1 min' , key='TF', bind_return_key=True),
                 sg.T(' ' * 10),
                 sg.InputOptionMenu(( sg_pack[0],
                    sg_pack[1],sg_pack[2],sg_pack[3],sg_pack[4],sg_pack[5],sg_pack[6],
                    sg_pack[7],sg_pack[8],sg_pack[9],sg_pack[10],sg_pack[11],sg_pack[12] ),
                    key='PACK', default_value='12 special vs -240:MX'),
                 sg.T(' ' * 10),  sg.Submit(),  sg.T(' ' * 55),
                 sg.Quit(auto_size_button=True)
                 ],
                [grafic]
            ]
    window = sg.Window(name_trm, grab_anywhere=True).Layout(layout).Finalize()
    graph = window.FindElement('graph')
    graph.Erase()
    event, values = '', {'TF':[' 1 min']}
    mode = 'manual'
    tm_out = 52000
    # main cycle   -----------------------------------------------------
    while True:
        if mode == 'auto':
            event, values = window.Read(timeout=tm_out)  # period 52 sec
        else:
            event, values = window.Read()  # period 3 sec
        print('event = ', event, ' ..... values = ', values)

        if event is None        : break
        if event == 'Quit'      : break

        if event == 'auto'      : mode = 'auto'
        if event == 'manual'    : mode = 'manual'
        if event == 'Submit'    : refresh_graph(cntr, values, graph)

        if event == '__TIMEOUT__'   :
            pass

    return
#=======================================================================
if __name__ == '__main__':
    import sys
    sys.exit(main())
