import urllib, os
from bs4 import BeautifulSoup
import re
import humble
import time
import datetime

# Pattern for ldb information
LDB = 'http://ojp.nationalrail.co.uk/service/ldbboard/dep/{dep}/{arr}/To'
#LDB = 'http://ojp.nationalrail.co.uk/service/ldbboard/dep/{dep}'

# Departure and Arrival
DEP = 'HTC'
#DEP = 'HTC'
ARR = 'MAN'

STATIONS = {'Manchester Piccadilly':'MAN',
            'Wigan Wallgate':'WGW',
            'Manchester Airport': 'MIA',
            'London Euston': 'EUS',
            'Stockport': 'SPT',
            'Manchester Oxford Road': 'MCO',
            'Southport': 'SOP',
            'Blackpool North': 'BPN',
            'Liverpool Lime Street': 'LIV',
            'Birmingham New Street': 'BHM',
            'Crewe via Stockport': 'CRE',
            'Crewe': 'CRE',
            'Macclesfield': 'MAC',
            'York': 'YRK',
            'Buxton': 'BUX',
            'Chester': 'CTR',
            'Wilmslow': 'WML',
            'Alderley Edge': 'ALD'}

DELAY = 2
CYCLES = 15
NEXT = 2
FORMAT = '{time:<5} {dest:<3} {estimate:<5}'
WALKING = 12
WAITING = 10
DANGER = 3

def green():
    humble.green(True)
    humble.yellow(False)
    humble.red(False)
    print "Green"

def yellow():
    humble.green(False)
    humble.yellow(True)
    humble.red(False)
    print "Yellow"

def red():
    humble.green(False)
    humble.yellow(False)
    humble.red(True)
    print "Red"

def off():
    humble.green(False)
    humble.yellow(False)
    humble.red(False)
    print "Off"


def lights(now, times):
    # status(g,y)
    greenLight = False
    yellowLight = False
    # If it's the case that any train yields green, then show green. Same for yellow. 
    for i in range (0,len(times)):
        togo = times[i] - now
        print str(togo) + " Minutes"
        if (togo) > (WAITING + WALKING):
            pass
        elif (togo) > (DANGER + WALKING):
            greenLight = True
        elif (togo) > WALKING:
            yellowLight = True
        else:
            pass

    if (greenLight):
        green()
    elif (yellowLight):
        yellow()
    else:
        red()

def shorten(station):
    if STATIONS.has_key(station):
        return STATIONS[station]
    else:
        return station[:3]

# Strip out the table of train times. Relies on knowing where the table occurs. 
def getTrains(soup):
    trains = []
    for div in soup.find_all('div'):
        if (div.attrs.has_key('class') and ("tbl-cont" in div['class']) ):
            body = div.table.tbody
            rows = body.find_all('tr')
            for r in range(0,len(rows)):
                row = rows[r]
                cells = row.find_all('td')
                #print '{time} {dest} {report}'.format(time=cells[0].contents[0].strip(),
                #                                      dest=cells[1].contents[0].strip(),
                #                                      report=cells[2].contents[0].strip())
                train = {}
                train['time'] = cells[0].contents[0].strip()
                train['dest'] = cells[1].contents[0].strip()
                # Collapse all white space
                train['dest'] = re.sub(r"\s+", ' ', train['dest'])
                train['report'] =cells[2].contents[0].strip()
                if re.match('[0-9][0-9]:[0-9][0-9]',train['report']):
                    train['est'] = train['report']
                else:
                    train['est'] = ""
                trains.append(train)
    return trains

# Pretty print details
def printTrains(trains):
    destLength = 10
    printFormat = ' {time:<6}| {estimate:<6}| {dest:<' + str(destLength) + '}| {report:<20}'
    printFormat = '{time:<5} {dest:<' + str(destLength) + '} {estimate:<5}'
    print printFormat.format(time="Time",
                             dest="To",
                             estimate="Est",
                             report="Report")
    print "========================================================="
    print "1234567890123456"
    for train in trains:
        print printFormat.format(time=train['time'],
                                 dest=train['dest'][:destLength],
                                 estimate=train['est'],
                                 report=train['report'])
    print "========================================================="

def checkForShutDown():
    if (humble.switch3()):
        humble.line(humble.LINE2, "")
        humble.scroll(humble.LINE2, "Shutting Down...")
        humble.line(humble.LINE2, "Shutting Down...")
        humble.line(humble.LINE1, "")
        humble.line(humble.LINE2, "")
        os.system("sudo halt")

def reportTrains(trains):
    train = trains[0]
    humble.line(humble.LINE1,FORMAT.format(num="1",
                                     time=train['time'],
                                     dest=shorten(train['dest']),
                                     estimate=train['est'],
                                     report=train['report']))
    times = []
    for i in range(0,NEXT):
        if i < len(trains):
            trainTime = trains[i]['time']
            if (trains[i]['est'] != ""):
                trainTime = trains[i]['est']
            trainH = int(trainTime[0:2])
            trainM = int(trainTime[3:5])
            if (trainH == 0):
                trainH = 24
            trainMinutes = trainH*60 + trainM
            times.append(trainMinutes)

    for i in range(0,CYCLES):
        now = datetime.datetime.now()
        nowH = int(now.strftime('%H'))
        nowM = int(now.strftime('%M'))
        if (nowH == 0):
            nowH = 24
        nowMinutes = nowH*60 + nowM
        lights(nowMinutes, times)

        for j in range(1,NEXT+1):
            if j < len(trains):
                train = trains[j]
                humble.line(humble.LINE2,FORMAT.format(num=str(j+1),
                                                 time=train['time'],
                                                 dest=shorten(train['dest']),
                                                 estimate=train['est'],
                                                 report=train['report']))
                checkForShutDown()
                time.sleep(DELAY)
    
print LDB.format(dep=DEP,arr=ARR)
humble.init()
while(True):
    f = urllib.urlopen(LDB.format(dep=DEP,arr=ARR))
    stuff = f.read()
    o = open('tmp.html','w')
    o.write(stuff)
    soup = BeautifulSoup(stuff)
    trains = getTrains(soup)
    printTrains(trains)
    reportTrains(trains)

            
