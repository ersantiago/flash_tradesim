import os
import requests
from bs4 import BeautifulSoup as bfs
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time

from selenium.webdriver.chrome.options import Options
chrome_options = Options()
#chrome_options.add_argument("--headless")

#========================== Functions ============================#
def write(logfile, input):
    encode_input = input.encode('ascii', 'ignore')
    with open(logfile, 'wb') as f:
        f.write(encode_input)
        f.close()

#========================== Variables ============================#
rawdir = "C:\\Scripts\\bons\\data_klines\\1000LUNCUSDT\\raw"
builddir = "C:\\Scripts\\bons\\data_klines\\1000LUNCUSDT\\build"
logfile = "C:\\Scripts\\bons\\1000LUNCUSDT\\build_db.log"
symbol = '1000LUNCUSDT'

#========================== Main Function ========================#
os.chdir(rawdir)
csvfiles = os.listdir()

#========================== Get groups ===========================#
monthlist = []
tempskipped = []
for file in csvfiles:
    print(file)
    if file.endswith('.csv'):
        try:
            sym, win, year, mo, day = file.strip('.csv').split('-')
            if sym == symbol:
                lname = ('-').join([sym, year, mo]) + '.csv'
                if lname not in monthlist:
                    monthlist.append(lname)
        except:
            print("Skip file : " + file)
            tempskipped.append(file)
            #time.sleep(1)
for monthfile in monthlist:
    print("\nMonthfile: " + str(monthfile))
    fpath = os.path.join(builddir, monthfile)
    print(fpath)
    loadmonthfile = open(fpath, 'w')
    templist = []
    for file in csvfiles:
        if file.endswith('.csv'):
            try:
                sym, win, year, mo, day = file.strip('.csv').split('-')
                lname = ('-').join([sym, year, mo]) + '.csv'
                if lname == monthfile:
                    print(file)
                    csvload = open(file, 'r').read().splitlines()
                    templist = templist + csvload
                    templist.sort()
            except:
                print("Skip file : " + file)
                time.sleep(3)
    for line in templist:
        if 'open' not in line:
            loadmonthfile.write(line + '\n')
    loadmonthfile.close()
print("DONE")
print("Skipped Files:")
for skip in tempskipped:
    print(skip)