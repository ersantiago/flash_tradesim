#!/home/xinyx/miniconda3/bin/python3
import os
import datetime
import numpy as np
import pprint

fullprint = True

# datdir = "C:\\Scripts\\bons\\trading"
# logfile = "C:\\Scripts\\bons\\trading\\run.log"
datdir = "/home/ec2-user/sims/data"
logfile = "/home/ec2-user/sims/runv3.log"

# ================================== FUNCTIONS ==================================#
def diffchk(current, ref):
    perc = round(((float(current) - float(ref)) / float(ref) * 100), 2)
    return perc
def logger(type,msg):
    if type == 'full':
        if fullprint:
            print(msg)
        lgme = open(logfile, '+a')
        lgme.write(str(msg) + '\n')
        lgme.close()
    elif type == 'save':
        lgme = open(logfile, '+a')
        lgme.write(str(msg) + '\n')
        lgme.close()
    elif type == 'print':
        if fullprint:
            print(msg)
    else:
        print("Argument not recognized. full, save, print")
# ================================== VARIABLES ==================================#
sellnxt = 14
tgtpct_long = 1.0
tgtpct_short = 1.2
lvg = 11
cutloss = -22.0
cutloss_cd = 15
initial = 80.0
buffer = 160.0
trendpct = 2.0
trendchk = True
semi_compounded = True
symbol = '1000LUNCUSDT'
# ================================== INITIALIZE ==================================#
long_hits = 0
long_correct = 0
short_hits = 0
short_correct = 0
vader_hits = 0
vader_correct = 0
cumltvpct = 0.0
cumltvfunds = startfunds = initial + buffer
trendavoid = 0
cutlosses = 0
list_cutlosses = []
list_liquidations = []
liquidations = 0
critical_state = 0
takeprofits = 0
logs = []
i = 0
def simulate(initial, buffer, datdir, input_csv):
    # Flash Crash Catcher
    os.chdir(datdir)
    loadme = open(input_csv, 'r').read().splitlines()
    bname = os.path.basename(input_csv)
    # =============================== INITIALIZE =====================================#
    long_hits = 0
    long_correct = 0
    short_hits = 0
    short_correct = 0
    vader_hits = 0
    vader_correct = 0
    cumltvpct = 0.0
    cumltvfunds = startfunds = buffer + initial
    trendavoid = 0
    cutlosses = 0
    list_cutlosses = []
    list_liquidations = []
    liquidations = 0
    critical_state = 0
    takeprofits = 0
    logs = []
    i = 0
    losstreak = 0
    loss_usdt = 0
    loss_peakcount = 0
    loss_peakusdt = 0
    list_longpnl = []
    list_longs = []
    list_shorts = []
    list_vaders = []
    pnlprev = 1.0
    # =================================================================================#
    while i < (len(loadme) - 1):
        try:
            epochdt, openp, high, low, close = loadme[i].split(',')[0:5]
            epochdt = int(epochdt[:-3])
            rawdt = datetime.datetime.fromtimestamp(epochdt)
            dtstamp = rawdt.strftime("%Y-%m-%d %H:%M")

            # ====== Take profits & initial adjustment
            if semi_compounded and (cumltvfunds >= 4 * initial):
                # cumltvfunds = cumltvfunds - initial
                # takeprofits = takeprofits + initial
                initial = initial * 2
                if initial > 400:
                    initial = 400.0
            # ===== Bids
            shortbid = round((float(openp) * float((100 + tgtpct_short) / 100)), 2)
            longbid = round((float(openp) * float((100 - tgtpct_long) / 100)), 2)
            chklong = longbid >= float(low)
            chkshort = shortbid <= float(high)
            # ====== Check bids hit
            criteria = chklong or chkshort
            if criteria:
                scndl = float(loadme[i + sellnxt].split(',')[4])
                # ======== check lowest/highest in days window
                tmp_high = []
                tmp_low = []
                for j in range(1,sellnxt+1):
                    epochdt1, openp1, high1, low1, close1 = loadme[i + j].split(',')[0:5]
                    tmp_high.append(float(high1))
                    tmp_low.append(float(low1))
                lowest = min(tmp_low)
                highest = max(tmp_high)
                # ====== Check balance
                if cumltvfunds <= 0.0:
                    logger('print', "No more funds!!! Nothing here to trade!!!")
                    break
                elif cumltvfunds < initial:
                    logger('print', "Careful. Funds below initial!!!")
                    critical_state += 1
                # ===== Check trend
                epochdt_ref, openp_ref, high_ref, low_ref, close_ref = loadme[i - 5].split(',')[0:5]
                if trendchk and abs(diffchk(close, close_ref) > trendpct):
                    logger('print', "\tSkip Trading. Trending @ " + str(diffchk(close, close_ref)) + "%")
                    i += cutloss_cd  # trading cooldown
                    # i += 1
                    trendavoid += 1
                    continue
                # =====================================================================================#
                ###print("Order Executed!!!")
                # ===== Check if short or long
                if chkshort and chklong:
                    vader_hits += 1
                    bid_type = "vader"
                    pcntpft = round(((shortbid - longbid) / shortbid) * 100 * lvg, 3)
                    maxdip = min(-(lvg) * diffchk(highest, shortbid),(lvg) * diffchk(lowest, longbid))
                    longgain = round((lvg) * diffchk(max(tmp_high[1:]),longbid),2)
                    shortgain = round(-(lvg) * diffchk(min(tmp_low[1:]), shortbid),2)
                    if longgain >= shortgain:
                        maxgain = longgain
                        bid_type = bid_type + 'long'
                    else:
                        maxgain = shortgain
                        bid_type = bid_type + 'short'
                    if pcntpft >= 0:
                        vader_correct += 1
                    list_vaders.append(maxgain)
                elif chkshort:  # green candle (short)
                    short_hits += 1
                    bid_type = "short"
                    pcntpft = round(((shortbid - scndl) / shortbid) * 100 * lvg, 3)
                    maxdip = -(lvg) * diffchk(highest, shortbid)
                    maxgain = round(-(lvg) * diffchk(min(tmp_low[1:]), shortbid),2)
                    list_shorts.append(maxgain)
                    if pcntpft >= 0:
                        short_correct += 1
                elif chklong:  # red candle (long)
                    long_hits += 1
                    bid_type = "long"
                    pcntpft = round(((scndl - longbid) / longbid) * 100 * lvg, 3)
                    maxdip = (lvg) * diffchk(lowest, longbid)
                    maxgain = round((lvg) * diffchk(max(tmp_high[1:]),longbid),2)
                    list_longs.append(maxgain)
                    if pcntpft >= 0:
                        list_longpnl.append(pcntpft)
                        long_correct += 1
                else:  # gray candle (none)
                    bid_type = "none"
                    bid = "none"
                    pcntpft = 0
                    maxdip = 0
                ###print("\t" + str(maxdip) + '\t' + str(cutloss))
                # ===== Check bid results
                if maxdip <= cutloss:
                    i += cutloss_cd  # Trading cooldown
                    # ===== Check if liquidated
                    value_long = (float(lowest) == float(low)) and maxdip < -80
                    value_short = (float(highest) == float(high)) and maxdip < -80
                    value = value_long or value_short
                    #value = (float(lowest) == float(low)) and maxdip < -80
                    if value:
                        logger('print', "\tLiquidated!!! @" + str(maxdip))
                        usdpft = initial * (maxdip / 100)  # initial mode
                        # usdpft = cumltvfunds * (maxdip / 100) # compounded mode
                        pcntpft = maxdip
                        cumltvfunds = round((usdpft + cumltvfunds), 2)
                        cumltvpct = cumltvpct + maxdip
                        liquidations += 1
                    else:
                        logger('print',"\tCut!!!")
                        # logged(logs,"Cutloss! @ " + str(cutloss) + " bid is @ " + str(bid) + " potentially (" + str(maxdip) + ")")
                        usdpft = round(initial * (cutloss / 100),2)  # initial mode
                        # usdpft = cumltvfunds * (cutloss / 100) # compounded mode
                        pcntpft = cutloss
                        cumltvfunds = round((usdpft + cumltvfunds), 2)
                        cumltvpct = cumltvpct + cutloss
                        cutlosses += 1
                    if float(close) < float(openp):  # red candle (long)
                        if lowest < float(low):
                            logger('print',"\t Long at " + str(longbid) + " => Dived deeper from " + str(low) + " to " + str(lowest) + " for the next " + str(sellnxt -1 ) + " candles.")
                            #logger('print',"\t   " + str(tmp_low))
                        else:
                            logger('print',"\t Long at " + str(longbid) + " => Bottomed at " + str(low) + " for the next " + str(sellnxt - 1) + " candles.")
                    else:  # green candle (short)
                        if highest > float(high):
                            logger('print',"\t Short at " + str(shortbid) + " => Spiked higher from " + str(high) + " to " + str(highest) + " for the next " + str(sellnxt -1 ) + " candles.")
                            #logger('print',"\t   " + str(tmp_high))
                        else:
                            logger('print',"\t Short at " + str(shortbid) + " => Peaked at " + str(high) + " for the next " + str(sellnxt - 1) + " candles.")
                else:
                    cumltvpct = cumltvpct + pcntpft
                    if cumltvfunds >= initial:
                        usdpft = round(0.01 * pcntpft * initial, 2)  # stick with initial
                        # usdpft = round(0.01 * pcntpft * cumltvfunds, 2) # compounded mode
                        cumltvfunds = round((usdpft + cumltvfunds), 2)
                    else:
                        usdpft = round(0.01 * pcntpft * cumltvfunds, 2)
                        cumltvfunds = round((usdpft + cumltvfunds), 2)
                datalist = [openp, str(longbid), low, str(shortbid), high, ]
                if usdpft < 0 and pnlprev < 0:
                    losstreak += 1
                    loss_usdt = round(loss_usdt + usdpft,2)
                    if losstreak > loss_peakcount:
                        loss_peakcount = 0 + losstreak
                    if loss_usdt < loss_peakusdt:
                        loss_peakusdt = 0 + loss_usdt
                else: #reset
                    losstreak = 0
                    loss_usdt = 0
                pnlprev = 0 + usdpft
                if bid_type == 'long':
                    printresult = " : ".join([str(i),bid_type, dtstamp, str(longbid), '=>', str(scndl), str(cumltvfunds), "max:" + str(maxgain)+'%', str(pcntpft)+'%', str(usdpft)])
                elif bid_type == 'short':
                    printresult = " : ".join([str(i),bid_type, dtstamp, str(shortbid), ' => ', str(scndl), str(cumltvfunds), "max:" + str(maxgain)+'%', str(pcntpft)+'%', str(usdpft)])
                elif 'vader' in bid_type:
                    printresult = " : ".join([str(i),bid_type, dtstamp, str(shortbid), ' => ', str(longbid), str(cumltvfunds), "max:" +str(maxgain)+'%', str(pcntpft)+'%', str(usdpft)])
                else:
                    printresult = "None"
                logger('print', printresult)
                #logger('print', '\t\t\thighs : ' + str(tmp_high))
                #logger('print', '\t\t\thighest : ' + str(highest))
                #logger('print', '\t\t\tlows : ' + str(tmp_low))
                #logger('print', '\t\t\tlowest : ' + str(lowest))
                i = i + sellnxt
            else:
                i += 1
        except:
            i += 1
            continue
    if long_hits == 0:
        long_wrate = 0
    else:
        long_wrate = round((long_correct / long_hits) * 100, 2)

    if short_hits == 0:
        short_wrate = 0
    else:
        short_wrate = round((short_correct / short_hits) * 100, 2)

    if vader_hits == 0:
        vader_wrate = 0
    else:
        vader_wrate = round((vader_correct / vader_hits) * 100, 2)
    pnlpcnt = diffchk(cumltvfunds, startfunds)
    # print(i)
    try:
        avgpnl = round((pnlpcnt / (long_correct + short_correct + vader_correct)), 2)
    except:
        avgpnl = 0
    results = [bname, pnlpcnt, avgpnl, long_wrate, short_wrate, vader_wrate, long_correct, long_hits, short_correct, short_hits,
               trendavoid, critical_state, cutlosses, liquidations, loss_peakcount, loss_peakusdt]

    #avg_vader = sum(list_vaders) / len(list_vaders)
    #avg_short = sum(list_shorts) / len(list_shorts)
    #avg_long = sum(list_longs) / len(list_longs)

    logger('print', "Long stats : " + str(long_correct) + " / " + str(long_hits) + "   :   " + str(long_wrate) + " %")
    logger('print', "Short stats : " + str(short_correct) + " / " + str(short_hits) + "   :   " + str(short_wrate) + " %")
    logger('print', "Vader stats : " + str(vader_correct) + " / " + str(vader_hits) + "   :   " + str(vader_wrate) + " %")
    logger('print', "Trends skipped: " + str(trendavoid))
    logger('print', "Cutlosses: " + str(cutlosses))
    logger('print', "Liquidations: " + str(liquidations))
    logger('print', "Critical State: " + str(critical_state))
    logger('print', "Profits Taken: " + str(takeprofits))
    logger('print', str(startfunds) + " => " + str(cumltvfunds) + "  (" + str(pnlpcnt) + " %)")
    logger('print', "Max PnL Vader: " + str(list_vaders))
    logger('print', "Max PnL Short: " + str(list_shorts))
    logger('print', "Max PnL Long: " + str(list_longs))
    logger('print', "Actual Max Long: " + str(list_longpnl))
    logger('print', "Loss Streak Count: " + str(loss_peakcount))
    logger('print', "Loss Streak USDT: " + str(loss_peakusdt))
    return (results)
#====================================== END SIMULATOR =============================================#
fullprint = True
semi_compounded = False
#================================ Ranges =================================#
'''ETCUSDT
tgtpct_long_range = np.arange(0.85,1.1,0.05)
tgtpct_short_range = np.arange(0.85,1.1,0.05)
lvg_range = np.arange(12,22,1)
cutloss_range = np.arange(-18,-30,-2)
cutloss_cd_range = np.arange(6,8,1)
trendpct_range = np.arange(2.0,3,0.5)
sellnxt_range = np.arange(3,11,1)
'''
tgtpct_long_range = np.arange(6.5,8.5,0.5)
tgtpct_short_range = np.arange(4.5,6.5,0.5)
lvg_range = np.arange(12,22,1)
cutloss_range = np.arange(-20,-25,-1)
cutloss_cd_range = np.arange(1,2,1)
trendpct_range = np.arange(4.0,6.0,1.0)
sellnxt_range = np.arange(3,5,1)
initial = 100
buffer = 200
mode = 'single'
semi_compounded = False
#datdir = "C:\\Scripts\\bons\\data_klines\\1000LUNCUSDT\\build"
logfile = "C:\\Scripts\\bons\\trading\\runv3_" + str(mode) + '.log'
#file = 'full-1000LUNCUSDT.csv'
#file = '1000LUNCUSDT-2022-11.csv'
datdir = "C:\\Scripts\\bons\\data_klines\\ETCUSDT\\build"
file = 'ETCUSDT-2023-02.csv'
#================================ Mode (Single or Loop) =================================#
if mode == 'loop':
    header = "tgtpct_long, tgtpct_long, lvg, cutloss, sellnxt, bname, pnlpcnt, avgpnl, long_wrate, short_wrate, vader_wrate, long_correct, long_hits, short_correct, short_hits, trendavoid, critical_state, cutlosses, liquidations, loss_peakcount, loss_peakusdt"
    logger('save', header)
    print(header)
    fullprint = False
    logfile = "/home/ersantiago/Scripts/hist_trade_simulator/runv3_loop.log"
    # Initialize Count
    z = 0
    for a in tgtpct_short_range:
        for a in tgtpct_long_range:
            for c in lvg_range:
                for d in cutloss_range:
                    for e in cutloss_cd_range:
                        for f in trendpct_range:
                            for g in sellnxt_range:
                                z += 1
    print("Total Samples : " + str(z))
    for tgtpct_short in tgtpct_short_range:
        for tgtpct_long in tgtpct_long_range:
            for lvg in lvg_range:
                for cutloss in cutloss_range:
                    for cutloss_cd in cutloss_cd_range:
                        for trendpct in trendpct_range:
                            for sellnxt in sellnxt_range:
                                results = simulate(initial, buffer, datdir, file)
                                output = [round(tgtpct_short, 2),round(tgtpct_long, 2), lvg, cutloss, cutloss_cd, trendpct, sellnxt] + results
                                logger('save', output)
                                print(output)
elif mode == 'single':
    logfile = "C:\\Scripts\\bons\\trading\\runv3_single.log"
    fullprint = True
    #tgtpct_short, tgtpct_long, lvg, cutloss, cutloss_cd, trendpct, sellnxt = [8,6,21,-20,1,5,4]
    tgtpct_short, tgtpct_long, lvg, cutloss, cutloss_cd, trendpct, sellnxt = [0.55,0.55,13,-32,7,2,4]
    results = simulate(initial, buffer, datdir, file)
    output = [round(tgtpct_short, 2),round(tgtpct_long, 2), lvg, cutloss, cutloss_cd, trendpct, sellnxt] + results
    logger('save', output)
elif mode == 'multi':
    fullprint = False
    logfile = "C:\\Scripts\\bons\\trading\\runv3_multifile.log"
    tgtpct_short, tgtpct_long, lvg, cutloss, cutloss_cd, trendpct, sellnxt = [8, 6, 21, -20, 1, 5, 4]
    files = os.listdir(datdir)
    for file in files:
        if file.endswith('.csv') and file.startswith(symbol):
            results = simulate(initial, buffer, datdir, file)
            output = [round(tgtpct_long, 2), lvg, cutloss, sellnxt] + results
            logger('save', output)
            print(output)
elif mode == 'config':
    semi_compounded = False
    fullprint = False
    config_file = 'flash_lunc.cfg'
    load_cfg = open(config_file,'r').read().splitlines()
    for line in load_cfg[1:]:
        tgtpct_short, tgtpct_long, lvg, cutloss, cutloss_cd, trendpct, sellnxt = line.split()
        tgtpct_short = float(tgtpct_short)
        tgtpct_long = float(tgtpct_long)
        lvg = int(lvg)
        cutloss = int(cutloss)
        cutloss_cd = int(cutloss_cd)
        trendpct = float(trendpct)
        sellnxt = int(sellnxt)
        results = simulate(initial, buffer, datdir, file)
        gains = 0
        total = 0
        pnllist = []
        inputs = os.listdir(datdir)
        for input in inputs:
            if input.endswith('.csv') and input.startswith(symbol):
                subresults = simulate(initial, buffer, datdir, input)
                pnlpct = subresults[1]
                pnllist.append(pnlpct)
                if pnlpct > 0:
                    gains += 1
                total += 1
        if total == 0:
            hitrate = 0
        else:
            hitrate = round((gains/total),2)
        results = simulate(initial, buffer, datdir, file)
        output = [hitrate, round(tgtpct_short, 2), round(tgtpct_long, 2), lvg, cutloss, cutloss_cd, trendpct, sellnxt] + results
        logger('save', output)
        print('\t\t\t' + str(pnllist))
        print(output)
elif mode == 'weird':
    fullprint = False
    # Initialize Count
    z = 0
    for a in tgtpct_short_range:
        for a in tgtpct_long_range:
            for c in lvg_range:
                for d in cutloss_range:
                    for e in cutloss_cd_range:
                        for f in trendpct_range:
                            for g in sellnxt_range:
                                z += 1
    print("Total Samples : " + str(z))
    for tgtpct_short in tgtpct_short_range:
        for tgtpct_long in tgtpct_long_range:
            for lvg in lvg_range:
                for cutloss in cutloss_range:
                    for cutloss_cd in cutloss_cd_range:
                        for trendpct in trendpct_range:
                            for sellnxt in sellnxt_range:
                                results = simulate(initial, buffer, datdir, file)
                                gains = 0
                                total = 0
                                pnllist = []
                                inputs = os.listdir(datdir)
                                for input in inputs:
                                    if input.endswith('.csv') and input.startswith(symbol):
                                        subresults = simulate(initial, buffer, datdir, input)
                                        pnlpct = subresults[1]
                                        pnllist.append(pnlpct)
                                        if pnlpct > 0:
                                            gains += 1
                                        total += 1
                                hitrate = round((gains/total),2)
                                results = simulate(initial, buffer, datdir, file)
                                output = [hitrate, round(tgtpct_short, 2), round(tgtpct_long, 2), lvg, cutloss, cutloss_cd, trendpct, sellnxt] + results
                                logger('save', output)
                                print('\t\t\t' + str(pnllist))
                                print(output)
else:
    print("No mode selected. Please choose from 'loop', 'single'")