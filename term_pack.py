#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  term_pack.py
#
#=======================================================================
import os, sys, math, time
import logging
import smtplib
import sqlite3
from datetime import datetime, timezone
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
class Class_ACCOUNT():
    def __init__(self):
        self.acc_date = ''
        self.acc_balance = 0.0
        self.acc_profit  = 0.0
        self.acc_go      = 0.0
        self.acc_depo    = 0.0
#=======================================================================
class Class_FUT():
    def __init__(self):
        self.sP_code = "-"
        self.sRest = 0
        self.sVar_margin = 0.0
        self.sOpen_price = 0.0
        self.sLast_price = 0.0
        self.sAsk =  0.0
        self.sBuy_qty = 0
        self.sBid =  0.0
        self.sSell_qty = 0
        self.sFut_go = 0.0
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
            r_get_table_db = [1, ' *'+ name_tbl + '* '+ str(ex)]

        return r_get_table_db
#=======================================================================
class Class_CONTR():
    ''' There are 2 history tables of FUT -
    file_path_DATA  - file data from terminal QUIK
    db_path_FUT     - TABLE s_hist_1, ask/bid from TERMINAL 1 today (TF = 15 sec)
    '''
    def __init__(self, db_path_FUT, db_path_PACK, log_path, dt_start_date):
        #
        frm = '%Y-%m-%d %H:%M:%S'
        self.dt_start = datetime.strptime(dt_start_date, frm).replace(tzinfo=timezone.utc).timestamp()
        print(dt_start_date, self.dt_start)
        #
        self.db_path_FUT  = db_path_FUT       # path DB data & hist
        self.db_FUT_data  = Class_SQLite(self.db_path_FUT)
        self.dat_FUT_data = 0       # curv stamptime db_path_FUT
        self.dat_FUT_hist = 0       # it's counter of minute
        #
        self.db_path_PACK = db_path_PACK       # path DB data & hist
        self.db_PACK      = Class_SQLite(self.db_path_PACK)
        #
        self.hist_fut        = []   # массив котировок фьючей  60 s
        self.hist_fut_today  = []   # массив котировок фьючей  60 s
        self.hist_pack       = []   # массив котировок packets 60 s
        self.hist_pack_today = []   # массив котировок packets 60 s
        #
        self.data_fut = []    # list of Class_FUT()
        self.account  = ''    # obj Class_ACCOUNT()
        #
        self.koef_pack  = []  # массив списков-характеристик packets
        # init LOGger
        self.log  = Class_LOGGER(log_path)
        self.log.wr_log_info('*** START ***')

#=======================================================================
def init_cntr(cntr):
    # init cntr.koef_pack
    rq  = get_cfg_PACK(cntr)
    if rq[0] != 0:
        error_msg_popup(cntr, 'get_cfg_PACK => ', str(rq[1]), PopUp = True)
        return [1, 'get_cfg_PACK => ' + str(rq[1])]

    # init cntr.data_fut & parse FUT cntr.data_fut & cntr.account
    rq  = copy_data_FUT(cntr)
    if rq[0] != 0:
        error_msg_popup(cntr, 'copy_data_FUT => ', str(rq[1]))
        return [1, 'copy_data_FUT => ' + str(rq[1])]

    # copy hist_today table hist_FUT + filtr TF = 1 min +
    # rewrite into DB cntr.db_PACK
    rq  = copy_hist_FUT_today(cntr)
    if rq[0] != 0:
        error_msg_popup(cntr, 'copy_hist_FUT_today => ', str(rq[1]))
        return [1, 'copy_hist_FUT_today => ' + str(rq[1])]

    # read table hist_FUT + copy into cntr.db_PACK from cntr.start_sec
    rq  = get_hist_FUT(cntr)
    if rq[0] != 0:
        error_msg_popup(cntr, 'get_hist_FUT => ', str(rq[1]))
        return [1, 'get_hist_FUT => ' + str(rq[1])]

    # init + calc cntr.hist_pack for all PACKs
    for i_pack, item in enumerate(cntr.koef_pack):
        calc_hist_PACK(cntr, i_pack)
        sg.OneLineProgressMeter('calc_hist_PACK', i_pack+1, len(cntr.koef_pack), 'key', orientation='h')

    # rewrite table hist_PACK
    rq  = wr_hist_PACK(cntr)
    if rq[0] != 0:
        error_msg_popup(cntr, 'wr_hist_PACK => ', str(rq[1]))
        return [1, 'wr_hist_PACK => ' + str(rq[1])]

    # init + calc cntr.hist_pack_today for all PACKs
    if len(cntr.hist_fut_today) != 0:
        for i_pack, item in enumerate(cntr.koef_pack):
            calc_hist_PACK_today(cntr, i_pack)

        # rewrite table hist_pack_today
        if wr_hist_PACK_today(cntr)[0] != 0:
            error_msg_popup(cntr, 'wr_hist_PACK_today => ', str(rq[1]))
            return [1, 'wr_hist_PACK_today => ' + str(rq[1])]

    print('init_cntr - OK')
    return [0, 'OK']
#=======================================================================
def get_cfg_PACK(cntr):
    # read table cfg_PACK from DB cntr.db_PACK
    # init cntr.koef_pack
    rq  = cntr.db_PACK.get_table_db_with('cfg_PACK')
    if rq[0] != 0:
        sg.Popup('Error cfg_PACK!',  rq[1])
        return [1, rq[1]]
    else:
        for i_mdl, item in enumerate(rq[1]):
            cntr.koef_pack.append([])
            #   ['pckt0', ['0:2:SR, 9:-20:MX'], '222:100', '0.1:0.01:22:100']
            cntr.koef_pack[i_mdl].append(rq[1][i_mdl][0])
            cntr.koef_pack[i_mdl].append(rq[1][i_mdl][1].split(','))
            cntr.koef_pack[i_mdl].append(rq[1][i_mdl][2])
            cntr.koef_pack[i_mdl].append(rq[1][i_mdl][3])
            cntr.koef_pack[i_mdl].append(0) # NULL price for PACK
            print(cntr.koef_pack[i_mdl])
        print('___ Totally PACKETs ___ ', len(cntr.koef_pack))
        for item in cntr.koef_pack:
            cntr.hist_pack.append([])
            cntr.hist_pack_today.append([])
        return [0, 'OK']
#=======================================================================
def copy_data_FUT(cntr):
    # copy data from table data_FUT  into cntr.db_PACK
    rq  = cntr.db_FUT_data.get_table_db_with('data_FUT')
    if rq[0] != 0:
        err_msg = 'cntr.db_FUT_data.get_table_db_with(data_FUT) ' + rq[1]
        return [1, err_msg]

    req = cntr.db_PACK.rewrite_table('data_FUT', rq[1], val = '(?)')
    if req[0] != 0:
        err_msg = 'cntr.db_PACK.rewrite_table(data_FUT) ' + req[1]
        return [1, err_msg]

    cntr.data_fut = rq[1][:]
    parse_data_FUT(cntr)
    #print('data_fut = ', cntr.data_fut)
    return [0, 'ok']
#=======================================================================
def copy_hist_FUT_today(cntr):
    # copy hist_today from TERM to table hist_FUT from DB cntr.db_PACK
    rq  = cntr.db_FUT_data.get_table_db_with('hist_FUT_today')
    if rq[0] == 0:
        cntr.hist_fut_today = []
        buf_60_sec = 0
        if len(rq[1]) != 0:

            for item in rq[1]:
                frm = '%d.%m.%Y %H:%M:%S'
                dtt = datetime.strptime(str(item[1].split('|')[0]), frm)
                if len(cntr.hist_fut_today) == 0:
                    cntr.hist_fut_today.append(item)
                    buf_60_sec = dtt.minute
                else:
                    if dtt.minute != buf_60_sec:
                        cntr.hist_fut_today.append(item)
                        buf_60_sec = dtt.minute

        req = cntr.db_PACK.rewrite_table('hist_FUT_today', cntr.hist_fut_today, val = '(?,?)')
        if req[0] != 0:
            err_msg = 'cntr.db_PACK.rewrite_table(hist_FUT_today) ' + req[1]
            return [1, err_msg]
    else:
        err_msg = 'cntr.db_FUT_data.get_table_db_with(hist_today) ' + rq[1]
        return [1, err_msg]
    return [0, 'ok']
#=======================================================================
def get_hist_FUT(cntr):
    # read table hist_FUT from DB cntr.db_PACK
    rq  = cntr.db_PACK.get_table_db_with('hist_FUT')
    if rq[0] != 0:
        sg.Popup('Error hist_FUT!',  rq[1])
        return [1, rq[1]]
    #print(len(rq[1]), rq[1][0], rq[1][-1])
    # filtr cntr.start_sec
    cntr.hist_fut  = []
    for item in rq[1]:
        if item[0] > cntr.dt_start:  #cntr.start_sec:
            cntr.hist_fut.append([item[0], item[1]])
    #print(len(cntr.hist_fut), cntr.hist_fut[0], cntr.hist_fut[-1])
    return [0, 'OK']
#=======================================================================
def calc_hist_PACK(cntr, i_pack):
    cntr.hist_pack[i_pack] = []
    arr_HIST = cntr.hist_fut    # archiv of FUT 60 sec
    const_UP, const_DW = +50, -50
    k_EMA     = int(cntr.koef_pack[i_pack][2].split(':')[0])
    k_EMA_rnd = int(cntr.koef_pack[i_pack][2].split(':')[1])
    koef_EMA = round(2/(1+k_EMA),5)
    ind = []
    kf  = []
    for elem in cntr.koef_pack[i_pack][1]:
        ind.append(int(elem.split(':')[0]))
        kf.append(int(elem.split(':')[1]))
    koef_AMA = cntr.koef_pack[i_pack][3]
    fSC       = float(koef_AMA.split(':')[0])
    sSC       = float(koef_AMA.split(':')[1])
    nn        = int(koef_AMA.split(':')[2])
    k_ama_rnd = int(koef_AMA.split(':')[3])

    for idx, item_HIST in enumerate(arr_HIST):
        ask_p, bid_p = 0, 0
        buf_c_pack = Class_PACK()
        buf_c_pack.ind = item_HIST[0]
        item = (item_HIST[1].replace(',', '.')).split('|')
        #print(item)
        buf_c_pack.dt, buf_c_pack.tm  = item[0].split(' ')
        for jdx, jtem in enumerate(kf):
            ask_j = float(item[1 + 2*ind[jdx]])
            bid_j = float(item[1 + 2*ind[jdx] + 1])
            if jtem > 0 :
                ask_p = ask_p + jtem * ask_j
                bid_p = bid_p + jtem * bid_j
            if jtem < 0 :
                ask_p = ask_p + jtem * bid_j
                bid_p = bid_p + jtem * ask_j

        ask_bid_AVR = 0
        if idx == 0:
            null_prc = int((ask_p + bid_p)/2)
            cntr.koef_pack[i_pack][-1] = null_prc
            buf_c_pack.pAsk, buf_c_pack.pBid = 0, 0
            buf_c_pack.EMAf, buf_c_pack.EMAf_rnd = 0, 0
            buf_c_pack.AMA, buf_c_pack.AMA_rnd = 0, 0
            buf_c_pack.cnt_EMAf_rnd = 0
            buf_c_pack.cnt_AMA_rnd = 0

        else:
            ask_p = int(ask_p - null_prc)
            bid_p = int(bid_p - null_prc)
            buf_c_pack.pAsk = ask_p
            buf_c_pack.pBid = bid_p
            ask_bid_AVR = int((ask_p + bid_p)/2)

            prev_EMAf = cntr.hist_pack[i_pack][idx-1].EMAf
            buf_c_pack.EMAf = round(prev_EMAf + (ask_bid_AVR - prev_EMAf) * koef_EMA, 1)
            buf_c_pack.EMAf_rnd = k_EMA_rnd * math.ceil(buf_c_pack.EMAf / k_EMA_rnd )

            prev_EMAf_rnd = cntr.hist_pack[i_pack][idx-1].EMAf_rnd
            i_cnt = cntr.hist_pack[i_pack][idx-1].cnt_EMAf_rnd
            if prev_EMAf_rnd > buf_c_pack.EMAf_rnd:
                buf_c_pack.cnt_EMAf_rnd = 0 if i_cnt > 0 else i_cnt-1
            elif prev_EMAf_rnd < buf_c_pack.EMAf_rnd:
                buf_c_pack.cnt_EMAf_rnd = 0 if i_cnt < 0 else i_cnt+1
            else:
                buf_c_pack.cnt_EMAf_rnd = i_cnt

        cntr.hist_pack[i_pack].append(buf_c_pack)
#=======================================================================
def calc_hist_PACK_today(cntr, i_pack):
    cntr.hist_pack_today[i_pack] = []
    arr_HIST = cntr.hist_fut_today    # archiv of FUT 60 sec
    const_UP, const_DW = +50, -50
    k_EMA     = int(cntr.koef_pack[i_pack][2].split(':')[0])
    k_EMA_rnd = int(cntr.koef_pack[i_pack][2].split(':')[1])
    koef_EMA = round(2/(1+k_EMA),5)
    ind = []
    kf  = []
    for elem in cntr.koef_pack[i_pack][1]:
        ind.append(int(elem.split(':')[0]))
        kf.append(int(elem.split(':')[1]))
    koef_AMA = cntr.koef_pack[i_pack][3]
    fSC       = float(koef_AMA.split(':')[0])
    sSC       = float(koef_AMA.split(':')[1])
    nn        = int(koef_AMA.split(':')[2])
    k_ama_rnd = int(koef_AMA.split(':')[3])

    for idx, item_HIST in enumerate(arr_HIST):
        ask_p, bid_p = 0, 0
        buf_c_pack = Class_PACK()
        buf_c_pack.ind = item_HIST[0]
        item = (item_HIST[1].replace(',', '.')).split('|')
        #print(item)
        buf_c_pack.dt, buf_c_pack.tm  = item[0].split(' ')
        for jdx, jtem in enumerate(kf):
            ask_j = float(item[1 + 2*ind[jdx]])
            bid_j = float(item[1 + 2*ind[jdx] + 1])
            if jtem > 0 :
                ask_p = ask_p + jtem * ask_j
                bid_p = bid_p + jtem * bid_j
            if jtem < 0 :
                ask_p = ask_p + jtem * bid_j
                bid_p = bid_p + jtem * ask_j

        ask_bid_AVR = 0
        if idx == 0:
            null_prc = cntr.koef_pack[i_pack][-1]
            ask_p = int(ask_p - null_prc)
            bid_p = int(bid_p - null_prc)
            buf_c_pack.pAsk = ask_p
            buf_c_pack.pBid = bid_p
            ask_bid_AVR = int((ask_p + bid_p)/2)

            prev_EMAf = cntr.hist_pack[i_pack][idx-1].EMAf
            buf_c_pack.EMAf = round(prev_EMAf + (ask_bid_AVR - prev_EMAf) * koef_EMA, 1)
            buf_c_pack.EMAf_rnd = k_EMA_rnd * math.ceil(buf_c_pack.EMAf / k_EMA_rnd )

            prev_EMAf_rnd = cntr.hist_pack[i_pack][idx-1].EMAf_rnd
            i_cnt = cntr.hist_pack[i_pack][idx-1].cnt_EMAf_rnd
            if prev_EMAf_rnd > buf_c_pack.EMAf_rnd:
                buf_c_pack.cnt_EMAf_rnd = 0 if i_cnt > 0 else i_cnt-1
            elif prev_EMAf_rnd < buf_c_pack.EMAf_rnd:
                buf_c_pack.cnt_EMAf_rnd = 0 if i_cnt < 0 else i_cnt+1
            else:
                buf_c_pack.cnt_EMAf_rnd = i_cnt
        else:
            ask_p = int(ask_p - null_prc)
            bid_p = int(bid_p - null_prc)
            buf_c_pack.pAsk = ask_p
            buf_c_pack.pBid = bid_p
            ask_bid_AVR = int((ask_p + bid_p)/2)

            prev_EMAf = cntr.hist_pack_today[i_pack][idx-1].EMAf
            buf_c_pack.EMAf = round(prev_EMAf + (ask_bid_AVR - prev_EMAf) * koef_EMA, 1)
            buf_c_pack.EMAf_rnd = k_EMA_rnd * math.ceil(buf_c_pack.EMAf / k_EMA_rnd )

            prev_EMAf_rnd = cntr.hist_pack_today[i_pack][idx-1].EMAf_rnd
            i_cnt = cntr.hist_pack_today[i_pack][idx-1].cnt_EMAf_rnd
            if prev_EMAf_rnd > buf_c_pack.EMAf_rnd:
                buf_c_pack.cnt_EMAf_rnd = 0 if i_cnt > 0 else i_cnt-1
            elif prev_EMAf_rnd < buf_c_pack.EMAf_rnd:
                buf_c_pack.cnt_EMAf_rnd = 0 if i_cnt < 0 else i_cnt+1
            else:
                buf_c_pack.cnt_EMAf_rnd = i_cnt


        cntr.hist_pack_today[i_pack].append(buf_c_pack)
#=======================================================================
def prepair_hist_PACK(cntr, b_today = False):
    name_list =[]
    if b_today :
        arr_hist_pack = cntr.hist_pack_today
    else:
        arr_hist_pack = cntr.hist_pack
    for i_hist, item_hist in enumerate(arr_hist_pack[0]):
        buf_dt = item_hist.dt + ' ' + item_hist.tm + ' '
        buf_s = ''
        for i_mdl, item_mdl in enumerate(arr_hist_pack):
            buf = arr_hist_pack[i_mdl][i_hist]
            buf_s += str(buf.pAsk) + ' ' + str(buf.pBid)     + ' '
            buf_s += str(buf.EMAf) + ' ' + str(buf.EMAf_rnd) + ' ' + str(buf.cnt_EMAf_rnd) + ' '
            buf_s += str(buf.AMA)  + ' ' + str(buf.AMA_rnd)  + ' ' + str(buf.cnt_AMA_rnd) + '|'
        name_list.append((item_hist.ind, buf_dt + buf_s.replace('.', ',')))
    return name_list
#=======================================================================
def wr_hist_PACK(cntr):
    name_list = []
    name_list = prepair_hist_PACK(cntr)
    rq = cntr.db_PACK.rewrite_table('hist_PACK', name_list, val = '(?,?)')
    if rq[0] != 0:
        err_msg = 'rewrite_table hist_PACK ' + rq[1]
        #cntr.log.wr_log_error(err_msg)
        #sg.Popup('Error !', err_msg)
        return [1, err_msg]
    else:
        cntr.log.wr_log_info('rewrite_table hist_PACK  - OK')
        #sg.Popup('OK !', 'ok rewrite_table hist_PACK  ' + str(len(name_list)))
        return [0, 'OK']
#=======================================================================
def wr_hist_PACK_today(cntr):
    name_list = []
    name_list = prepair_hist_PACK(cntr, b_today = True)
    rq = cntr.db_PACK.rewrite_table('hist_PACK_today', name_list, val = '(?,?)')
    if rq[0] != 0:
        err_msg = 'rewrite_table hist_PACK_today   ' + rq[1]
        #cntr.log.wr_log_error(err_msg)
        #sg.Popup('Error !', err_msg)
        return [1, err_msg]
    else:
        #cntr.log.wr_log_info('rewrite_table hist_PACK_today  - OK')
        #sg.Popup('OK !', 'ok rewrite_table hist_PACK_today  ' + str(len(name_list)))
        return [0, 'OK']
#=======================================================================
def parse_data_FUT(cntr):
    try:
        cntr.account  = Class_ACCOUNT()
        # format of list data_fut:
        #   0   => string of DATA / account.acc_date
        #   1   => [account.acc_balance/acc_profit/acc_go/acc_depo]
        #   2 ... 22  => Class_FUT()
        #print(self.str_in_file)
        data_fut = []
        for i, item in enumerate(list(cntr.data_fut)):
            list_item = ''.join(item[0]).replace(',','.').split('|')
            if   i == 0:
                cntr.account.acc_date  = list_item[0]
                #cntr.data_fut.append(self.account.acc_date)
            elif i == 1:
                cntr.account.acc_balance = float(list_item[0])
                cntr.account.acc_profit  = float(list_item[1])
                cntr.account.acc_go      = float(list_item[2])
                cntr.account.acc_depo    = float(list_item[3])
            else:
                b_fut = Class_FUT()
                b_fut.sP_code      = list_item[0]
                b_fut.sRest        = int  (list_item[1])
                b_fut.sVar_margin  = float(list_item[2])
                b_fut.sOpen_price  = float(list_item[3])
                b_fut.sLast_price  = float(list_item[4])
                b_fut.sAsk         = float(list_item[5])
                b_fut.sBuy_qty     = int  (list_item[6])
                b_fut.sBid         = float(list_item[7])
                b_fut.sSell_qty    = int  (list_item[8])
                b_fut.sFut_go      = float(list_item[9])
                data_fut.append(b_fut)
        cntr.data_fut = data_fut[:]
        #print('account = ', cntr.account.acc_date)
        #print('cntr.data_fut => \n', cntr.data_fut[0].sP_code)
    except Exception as ex:
        err_msg = 'parse_str_in_file / ' + str(ex)
        print(err_msg)
        #cntr.log.wr_log_error(err_msg)
        return [1, err_msg]
    return [0, 'ok']
#=======================================================================
def error_msg_popup(cntr, msg_log, msg_rq_1, PopUp = True):
    cntr.log.wr_log_error(msg_log + msg_rq_1)
    if PopUp == True:
        sg.PopupError(msg_log + msg_rq_1)
#=======================================================================
def check_stat_DB(cntr):
    # check time modificated of file
    buf_stat_time = int(os.stat(cntr.db_path_FUT).st_mtime)
    if cntr.dat_FUT_data == 0:
        cntr.dat_FUT_data = buf_stat_time
        return [1, '  first start  ']
    else:
        if ((buf_stat_time - cntr.dat_FUT_data) < 3):
            str_dt_file = datetime.fromtimestamp(cntr.dat_FUT_data).strftime('%H:%M:%S')
            return [3, str_dt_file + ' is not modifed 55 sec']
        else:
            cntr.dat_FUT_data = buf_stat_time
    return [0, 'ok']
#=======================================================================
def update_db(cntr):
    rq  = copy_data_FUT(cntr)
    if rq[0] != 0:
        error_msg_popup(cntr, 'copy_data_FUT => ', str(rq[1]), PopUp = False)
        return [1, 'Error copy_data_FUT => ']

    # if cntr.account.acc_date.minute has changed:
    frm = '%d.%m.%Y %H:%M:%S'
    dtt = datetime.strptime(str(cntr.account.acc_date), frm)
    if cntr.dat_FUT_hist != dtt.minute:
        cntr.dat_FUT_hist = dtt.minute

        rq  = copy_hist_FUT_today(cntr)
        if rq[0] != 0:
            error_msg_popup(cntr, 'copy_hist_FUT_today => ', str(rq[1]), PopUp = False)
            return [1, 'Error copy_hist_FUT_today => ']

        if len(cntr.hist_fut_today) != 0:
            for i_pack, item in enumerate(cntr.koef_pack):
                calc_hist_PACK_today(cntr, i_pack)

            # rewrite table hist_pack_today
            if wr_hist_PACK_today(cntr)[0] != 0:
                error_msg_popup(cntr, 'wr_hist_PACK_today => ', str(rq[1]), PopUp = False)
                return [1, 'Error wr_hist_PACK_today => ']
    return [0, 'ok']
#=======================================================================
def service_data_FUT(cntr):
    rq  = cntr.db_FUT_data.get_table_db_with('data_FUT')
    if rq[0] == 0:
        sg.Popup(
                 'data_FUT',
                 '\n'.join(map(str,rq[1]))
                )
#=======================================================================
def service_hist_FUT(cntr):
    fut_F, fut_S, fut_L = cntr.hist_fut[0][1], cntr.hist_fut[1][1], cntr.hist_fut[-1][1]
    pack_F, pack_S, pack_L = cntr.hist_pack[0][0], cntr.hist_pack[0][1], cntr.hist_pack[0][-1]
    sg.Popup(
             'hist_FUT/PACK   ',
             '____________________________________________',
             'len(hist_FUT)   ' + str(len(cntr.hist_fut)),
             'first...' + fut_F.split('|')[0],
             'second..' + fut_S.split('|')[0],
             '........',
             'last....' + fut_L.split('|')[0],
             '____________________________________________',
             'len(hist_pack)   ' + str(len(cntr.hist_pack[0])),
             'first...' + pack_F.dt + '     ' + pack_F.tm,
             'second..' + pack_S.dt + '     ' + pack_S.tm,
             '........',
             'last....' + pack_L.dt + '     ' + pack_L.tm,
            )
#=======================================================================
def service_hist_TODAY(cntr):
    fut_F, fut_S, fut_L = cntr.hist_fut_today[0][1], cntr.hist_fut_today[1][1], cntr.hist_fut_today[-1][1]
    pack_F, pack_S, pack_L = cntr.hist_pack_today[0][0], cntr.hist_pack_today[0][1], cntr.hist_pack_today[0][-1]
    sg.Popup(
             'hist_FUT/PACK   ',
             '____________________________________________',
             'len(hist_FUT)   ' + str(len(cntr.hist_fut_today)),
             'first...' + fut_F.split('|')[0],
             'second..' + fut_S.split('|')[0],
             '........',
             'last....' + fut_L.split('|')[0],
             '____________________________________________',
             'len(hist_pack)   ' + str(len(cntr.hist_pack_today[0])),
             'first...' + pack_F.dt + '     ' + pack_F.tm,
             'second..' + pack_S.dt + '     ' + pack_S.tm,
             '........',
             'last....' + pack_L.dt + '     ' + pack_L.tm,
            )
#=======================================================================
def service_cfg_PACK(cntr):
    s_koef = []
    for item in cntr.koef_pack :
        s_jtem = ''
        for jtem in item:
            if type(jtem) is list:  s_jtem += ' ; '.join(jtem) + '  '
            else:                   s_jtem += str(jtem) + '  '
        s_koef.append(s_jtem)
    sg.Popup(
             'cfg_PACK',
             '\n'.join(s_koef)
            )
#=======================================================================
def main():
    # init program config
    dirr, sub_dirr = os.path.abspath(os.curdir), '\\DB\\'
    path_FUT, path_PACK = 'term_today.sqlite', 'term_pack.sqlite'
    db_path_FUT  = dirr + sub_dirr + path_FUT
    db_path_PACK = dirr + sub_dirr + path_PACK
    name_trm, log_path, dt_start_date =  '', '', ''

    path_DB  = Class_SQLite(db_path_PACK)
    rq  = path_DB.get_table_db_with('cfg_SOFT')
    if rq[0] != 0:
        print('Can not read DB => ' + db_path_PACK)
        sg.PopupError('Can not read DB => term_pack.sqlite !', rq[1])
        return
    for item in rq[1]:
        if item[0] == 'titul'         : name_trm        = item[1]
        if item[0] == 'path_file_LOG' : log_path        = dirr + item[1]
        if item[0] == 'dt_start'      : dt_start_date   = item[1]

    #print('{: <15}\n{: <25}\n{: <15}'.format(name_trm, log_path, dt_start_date))

    # init CONTR
    cntr = Class_CONTR(db_path_FUT, db_path_PACK, log_path, dt_start_date)
    init_cntr(cntr)

    # init MENU
    menu_def = [
                ['Mode',    ['auto', 'manual', ],],
                ['Service', ['Test SQL', ['data_FUT', 'hist_FUT', 'hist_FUT_TODAY', 'cfg_PACK', ], ['Reserve']],],
                ['Help', 'About...'],
                ['Exit', 'Exit']
                ]

    def_txt, frm = [], '{: <15}  => {: ^15}\n'
    def_txt.append(frm.format('path_db_FUT'  , path_FUT)  )
    def_txt.append(frm.format('path_db_PACK' , path_PACK) )
    def_txt.append(frm.format('dt_start_date', dt_start_date))

    tab_DATA = sg.Multiline( default_text=''.join(def_txt),
                size=(55, 5), key='txt_data', autoscroll=False, focus=False)

    # Display data
    sg.SetOptions(element_padding=(0,0))

    layout = [
                [sg.Menu(menu_def, tearoff=False, key='menu_def')],
                [tab_DATA],
                [sg.T('',size=(60,2), font='Helvetica 8', key='txt_status'), sg.Quit(auto_size_button=True)],
             ]

    window = sg.Window(name_trm, grab_anywhere=True).Layout(layout).Finalize()

    mode = 'auto'
    frm_str = '{: <15}{: ^15}'
    # main cycle   -----------------------------------------------------
    while True:
        stroki = []
        if mode == 'auto':
            event, values = window.Read(timeout=1500 )  # period 1,5 sec
        else:
            event, values = window.Read(timeout=15000)  # period 15 sec)
        #print('event = ', event, ' ..... values = ', values)

        if event is None        : break
        if event == 'Quit'      : break
        if event == 'Exit'      : break
        if event == 'auto'      : mode = 'auto'
        if event == 'manual'    : mode = 'manual'

        # menu SERVICE
        if event == 'data_FUT'      : service_data_FUT(cntr)
        if event == 'hist_FUT'      : service_hist_FUT(cntr)
        if event == 'hist_FUT_TODAY': service_hist_TODAY(cntr)
        if event == 'cfg_PACK'      : service_cfg_PACK(cntr)

        if event == '__TIMEOUT__':
            if check_stat_DB(cntr)[0] == 0:
                rg = update_db(cntr)
                if rq[0] != 0:
                    error_msg_popup(cntr, 'update_db => ', str(rq[1]), PopUp = False)
                    stroki.append('update_db => ERROR')
                else:
                    stroki.append(cntr.account.acc_date)
                    stroki.append(str(cntr.dat_FUT_data) + '   DB is modifed !')
            else:
                stroki.append(cntr.account.acc_date)

        window.FindElement('txt_data').Update('\n'.join(stroki))
        txt_frmt = '%Y.%m.%d  %H:%M:%S'
        stts  = time.strftime(txt_frmt, time.localtime()) + '\n'
        stts += 'event = ' + event
        window.FindElement('txt_status').Update(stts)
    return

if __name__ == '__main__':
    import sys
    sys.exit(main())
