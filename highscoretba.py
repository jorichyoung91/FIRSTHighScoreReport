import requests
import re
import sys
import copy
from unicodedata import normalize

def get_foul_points(URL):
    redFoulPoints = 0
    blueFoulPoints = 0
    tempRedFoul = 0
    redFound = False
    blueFound = False
    foulsFound = False
    
    response = requests.get(URL)
    html_data = response.text
    html_data = html_data.split('\n')
    
    for line in html_data:
        if redFound:
            p = re.search(r'^\s+(\d+)', line)
            if p is not None:
                tempRedFoul = int(p.group(1))
                redFound = False
                
        if blueFound and foulsFound:
            p = re.search(r'^\s+(\d+)', line)
            if p is not None:
                blueFoulPoints = int(p.group(1))
                redFoulPoints = tempRedFoul
                blueFound = False
                break
        
        if '<td class="redScore" colspan="2">' in line:
            redFound = True
            
        if '<td>Foul Points</td>' in line:
            foulsFound = True
            
        if '<td class="blueScore" colspan="2">' in line:
            blueFound = True
    
    return redFoulPoints, blueFoulPoints

def get_high_score(URL, week, normalizeScores):
    if URL == '':
        sys.exit("No URL supplied! Exiting.")
    if week == '':
        sys.exit("No week supplied! Exiting.")

    response = requests.get(URL)
    html_data = response.text
    html_data = html_data.split('\n')

    MatchURL = ""
    
    HiScoreDict = {
        "HiScore": 0,
        "LosingTeamScore": 0,
        "HiScoreMatchName": "",
        "WinningTeam": "",
        "EventName": "",
        "EventWeek": "",
        "RedTeams": [],
        "BlueTeams": []
    }

    oldHighScoreDict = copy.deepcopy(HiScoreDict)   # store last high score found when normalizing to reset if needed
    
    HiScoreDict["EventWeek"] = week

    lineNum = 0
    currMatchidx = 0
    currTeamScore = 0
    scoreFound = False
    newHighScore = False
    
    for line in html_data:
        # blank line
        if line == '':
            lineNum += 1
            continue
        
        # Page with no scores on it, skip
        if currMatchidx == 0:
            if '<li class="active"><a href="#teams"' in line:
                return HiScoreDict
        #
        
        # get event name
        if HiScoreDict["EventName"] == '':
            # s = re.search(r'<h1 itemprop="summary" id="event-name">([^<]+)', line) - old regex 2025
            s = re.search(r'<h1 id="event-name">([^<]+)', line)
            if s is not None:
                HiScoreDict["EventName"] = s.group(1)
                HiScoreDict["EventName"] = HiScoreDict["EventName"].replace(" 2026", "")
        #
        
        # found a new match
        if '<tr class="visible-lg">' in line:
            currMatchidx = lineNum
        #
        
        # found a score value, check against HiScore
        if scoreFound:
            n = re.search(r'  <span[^>]*>(\d+)', line)
            if n is not None:
                currTeamScore = int(n.group(1))
                if currTeamScore > HiScoreDict["HiScore"]:
                    HiScoreDict["HiScore"] = currTeamScore
                    newHighScore = True
                scoreFound = False
        #
        
        # found a team score
        m = re.search(r'<td class="\w+Score">', line)
        if m is not None:
            scoreFound = True
        #
        
        matchNameFound = False
        teamFound = False
        currTeamColor = ""
        currTeamNum = 0
        redFoulPoints = 0
        blueFoulPoints = 0
        
        # new high score found, get teams and match info
        if '<tr class="hidden-lg compact-row">' in line and newHighScore:
            HiScoreDict["BlueTeams"].clear()
            HiScoreDict["RedTeams"].clear()
            for nline in html_data[currMatchidx:lineNum+1]:
                if nline == '':
                    continue
                
                if normalizeScores:
                    s = re.search('<a href="(/match/[^"]+)', nline)
                    if s is not None:
                        MatchURL = "https://www.thebluealliance.com" + s.group(1)
                        redFoulPoints, blueFoulPoints = get_foul_points(MatchURL)
                
                if matchNameFound:
                    o = re.search('<a href=[^>]+>([^<]+)', nline)
                    if o is not None:
                        HiScoreDict["HiScoreMatchName"] = o.group(1)
                        matchNameFound = False
                        
                if teamFound:
                    q = re.search(r'<a href="/team/[^>]+>(\d+)', nline)
                    if q is not None:
                        currTeamNum = int(q.group(1))
                        if currTeamColor == "Blue":
                            HiScoreDict["BlueTeams"].append(currTeamNum)
                        elif currTeamColor == "Red":
                            HiScoreDict["RedTeams"].append(currTeamNum)
                        currTeamNum = 0
                    
                        teamFound = False
                
                if '<div class="match-name">' in nline:
                    matchNameFound = True
                
                p = re.search(r'class="(?:(blue|red))(?:(\s|"))', nline)
                if p is not None:
                    teamFound = True
                    if p.group(1) == 'blue':
                        currTeamColor = "Blue"
                    elif p.group(1) == 'red':
                        currTeamColor = "Red"
                    
                    if p.group(2) == ' ':
                        HiScoreDict["WinningTeam"] = currTeamColor
                        
                r = re.search(r'(\d+)</span>', nline)
                if r is not None:
                    currScore = int(r.group(1))
                    if currScore != HiScoreDict["HiScore"]:
                        HiScoreDict["LosingTeamScore"] = currScore
                    
            newHighScore = False
            loserTeamHighScore = False
            
            # subtract penalty points if normalize argument is passed
            if normalizeScores:
                resetHiScore = False
                normalizedHighScore = 0
                normalizedLosingScore = 0
                
                winningFoulPoints = 0
                LosingFoulPoints = 0

                if HiScoreDict["WinningTeam"] == "Red":
                    winningFoulPoints = redFoulPoints
                    LosingFoulPoints = blueFoulPoints
                else:
                    winningFoulPoints = blueFoulPoints
                    LosingFoulPoints = redFoulPoints
                
                
                normalizedHighScore = HiScoreDict["HiScore"] - winningFoulPoints
                normalizedLosingScore = HiScoreDict["LosingTeamScore"] - LosingFoulPoints
                
                if normalizedHighScore < oldHighScoreDict["HiScore"]:
                    if normalizedLosingScore > oldHighScoreDict["HiScore"]:
                        loserTeamHighScore = True
                        HiScoreDict["HiScore"] = normalizedLosingScore
                        HiScoreDict["LosingTeamScore"] = normalizedHighScore
                        if HiScoreDict["WinningTeam"] == "Red":
                            HiScoreDict["WinningTeam"] = "Blue"
                        else:
                            HiScoreDict["WinningTeam"] = "Red"
                        oldHighScoreDict = copy.deepcopy(HiScoreDict)
                    else:
                        resetHiScore = True
                            
                if resetHiScore:
                    HiScoreDict = copy.deepcopy(oldHighScoreDict)
                elif not loserTeamHighScore:
                    HiScoreDict["HiScore"] = normalizedHighScore
                    HiScoreDict["LosingTeamScore"] = normalizedLosingScore
                    oldHighScoreDict = copy.deepcopy(HiScoreDict)
            #
        #
        
        lineNum += 1


    if "Match " in HiScoreDict["HiScoreMatchName"]:
        HiScoreDict["HiScoreMatchName"] = "Playoff " + HiScoreDict["HiScoreMatchName"]
    
    # Remove non-ascii characters from Event Name
    HiScoreDict["EventName"] = str(normalize('NFKD', HiScoreDict["EventName"]).encode('ascii','ignore'))
    HiScoreDict["EventName"] = HiScoreDict["EventName"].replace('b\'', '')
    HiScoreDict["EventName"] = HiScoreDict["EventName"].replace('\'', '')

    if HiScoreDict["HiScore"] > 0:
        # store output in one big string to avoid out-of-order printing when parallelized
        consoleText = ("*"*75) + '\n' + \
        HiScoreDict["EventName"] + '\n' + \
        '\n' + \
        "The high score was " + HiScoreDict["HiScoreMatchName"] + " with " + HiScoreDict["WinningTeam"] +" Team winning " + str(HiScoreDict["HiScore"]) + " to " + str(HiScoreDict["LosingTeamScore"]) + "." + '\n' + \
        "Blue Team - " + str(HiScoreDict["BlueTeams"][0]) + " " + str(HiScoreDict["BlueTeams"][1]) + " " + str(HiScoreDict["BlueTeams"][2]) + '\n' + \
        "Red Team - " + str(HiScoreDict["RedTeams"][0]) + " " + str(HiScoreDict["RedTeams"][1]) + " " + str(HiScoreDict["RedTeams"][2]) + '\n' + \
        "*"*75 + '\n'
        
        print(consoleText, flush=True)
        
    return HiScoreDict


if __name__ == '__main__':
    # executed as script
    # URL = "https://www.thebluealliance.com/event/2025mimil"
    # URL = 'https://www.thebluealliance.com/event/2025iscmp'
    URL = 'https://www.thebluealliance.com/event/2025tuis3'
    
    get_high_score(URL, "Week 1", True)
