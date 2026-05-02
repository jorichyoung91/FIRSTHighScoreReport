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
        # The keys 'redScore' and 'blueScore' are used multiple times in the same page. We are only concerned with the Foul Points.
        # The way the html table is construction has the format:
        # redScore 5
        # Foul Points
        # blueScore 0
        #
        # So we must save every 'redScore' we find, overwriting the last in tempRedFoul, until we find the 'Foul Points' tag, and then save/return those values.
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
    
    # Local Testing
    # with open('C:/Users/joric/Desktop/feed.rss', 'r') as file:
        # html_data = [line.strip() for line in file]
    
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
    
    # Store last high score found when normalizing to reset if needed.
    # deepcopy must be used as assigning one dictionary to another only sets them to the same reference in memory.
    oldHighScoreDict = copy.deepcopy(HiScoreDict)
    
    HiScoreDict["EventWeek"] = week

    lineNum = 0
    currMatchidx = 0
    currTeamScore = 0
    scoreFound = False
    newHighScore = False
    
    for line in html_data:
        # Blank line, ignore.
        if line == '':
            lineNum += 1
            continue
        
        # Get event name.
        if HiScoreDict["EventName"] == '':
            s = re.search(r'<title>(.+)</title>', line) # First <title> entry is event name
            if s is not None:
                HiScoreDict["EventName"] = s.group(1)
                HiScoreDict["EventName"] = re.sub(r'\s\d{4}$', '', HiScoreDict["EventName"]) # Remove year at the end of string
                lineNum += 1
                continue
        #
        
        # Found a new match.
        if '<title>' in line:
            currMatchidx = lineNum
        #
        
        # Found a score value, check against HiScore.
        if '<h1>' in line:
            n = re.search(r'<h1>[\w|\s]+:\s(\d+)</h1>', line)
            if n is not None:
                currTeamScore = int(n.group(1))
                if currTeamScore > HiScoreDict["HiScore"]:
                    HiScoreDict["HiScore"] = currTeamScore
                    newHighScore = True

        
        matchNameFound = False
        foulPointsFound = False
        currTeamColor = ""
        currTeamNum = 0
        redScore = 0
        blueScore = 0
        redFoulPoints = 0
        blueFoulPoints = 0
        
        # New high score found, get teams and match info. Use </description> tag to indicate end of match info.
        if '</description>' in line and newHighScore:
            HiScoreDict["BlueTeams"].clear()
            HiScoreDict["RedTeams"].clear()
            # Re-iterate from when we first found the match until the current line.
            for nline in html_data[currMatchidx:lineNum+1]:
                if nline == '':
                    continue
                
                # Get found points awarded to each team.
                if normalizeScores and not foulPointsFound:
                    s = re.search('<link>(.+)</link>', nline)
                    if s is not None:
                        MatchURL = s.group(1)
                        redFoulPoints, blueFoulPoints = get_foul_points(MatchURL)
                        foulPointsFound = True
                
                if '<title>' in nline and not matchNameFound:
                    o = re.search('<title>(.+)</title>', nline)
                    if o is not None:
                        HiScoreDict["HiScoreMatchName"] = o.group(1)
                        matchNameFound = True
                        
                if '<h1>' in nline:
                    p = re.search(r'<h1>(\w+)\sAlliance:\s(\d+)</h1>', nline)
                    # teamFound = True
                    currTeamColor = p.group(1)
                    if currTeamColor == "Blue":
                        blueScore = int(p.group(2))
                    elif currTeamColor == "Red":
                        redScore = int(p.group(2))
                elif '<li>' in nline:
                    q = re.search(r'<li>(\d+)</li>', nline)
                    currTeamNum = int(q.group(1))
                    if currTeamColor == "Blue":
                        HiScoreDict["BlueTeams"].append(currTeamNum)
                    elif currTeamColor == "Red":
                        HiScoreDict["RedTeams"].append(currTeamNum)
                    currTeamNum = 0
            
            if redScore > blueScore:
                HiScoreDict["WinningTeam"] = "Red"
                HiScoreDict["LosingTeamScore"] = blueScore
            elif blueScore > redScore:
                HiScoreDict["WinningTeam"] = "Blue"
                HiScoreDict["LosingTeamScore"] = redScore
            elif redScore == blueScore:
                HiScoreDict["WinningTeam"] = "TIE"
                HiScoreDict["LosingTeamScore"] = 0
            
            newHighScore = False
            loserTeamHighScore = False
            
            # Subtract penalty points if normalize argument is passed.
            if normalizeScores:
                resetHiScore = False
                normalizedRedScore = 0
                normalizedBlueScore = 0
                
                normalizedRedScore = redScore - redFoulPoints
                normalizedBlueScore = blueScore - blueFoulPoints
                
                # First level of comparison is normalized red score vs normalized blue score. Whichever is highest, compare that to the previous high score.
                # If the higher normalized score is lower than or equal to the previous high score, simply reset HiScoreDict to the previous score.
                # If the higher normalized score is higher than the previous high score, update the HiScoreDict as necessary and set it to the previous score dict for proceeding comparisons.
                if normalizedRedScore > normalizedBlueScore:
                    # If normalized score is lower than or equal to previous high score. Reset HiScoreDict to previous values
                    if normalizedRedScore <= oldHighScoreDict["HiScore"]:
                        resetHiScore = True
                    # Normalized score is still the highest, set these values in HiScoreDict
                    elif normalizedRedScore > oldHighScoreDict["HiScore"]:
                        HiScoreDict["HiScore"] = normalizedRedScore
                        HiScoreDict["LosingTeamScore"] = normalizedBlueScore
                        HiScoreDict["WinningTeam"] = "Red"
                elif normalizedBlueScore > normalizedRedScore:
                    if normalizedBlueScore <= oldHighScoreDict["HiScore"]:
                        resetHiScore = True
                    elif normalizedBlueScore > oldHighScoreDict["HiScore"]:
                        HiScoreDict["HiScore"] = normalizedBlueScore
                        HiScoreDict["LosingTeamScore"] = normalizedRedScore
                        HiScoreDict["WinningTeam"] = "Blue"
                # Normalized scores are tied
                elif normalizedRedScore == normalizedBlueScore:
                    if normalizedBlueScore <= oldHighScoreDict["HiScore"]:
                        resetHiScore = True
                    elif normalizedBlueScore > oldHighScoreDict["HiScore"]:
                        HiScoreDict["HiScore"] = normalizedBlueScore
                        HiScoreDict["LosingTeamScore"] = 0
                        HiScoreDict["WinningTeam"] = "TIE"

                if resetHiScore:
                    HiScoreDict = copy.deepcopy(oldHighScoreDict)
                else:
                    oldHighScoreDict = copy.deepcopy(HiScoreDict)
            #
        #
        
        lineNum += 1
    
    # Remove non-ascii characters and escaped characters from Event Name.
    HiScoreDict["EventName"] = str(normalize('NFKD', HiScoreDict["EventName"]).encode('ascii','ignore'))
    HiScoreDict["EventName"] = HiScoreDict["EventName"].replace('b\'', '')
    HiScoreDict["EventName"] = HiScoreDict["EventName"].replace('\'', '')
    HiScoreDict["EventName"] = HiScoreDict["EventName"].replace('amp;', '')
    
    
    hiScoreStr = ""
    if HiScoreDict["WinningTeam"] != "TIE":
        hiScoreStr = "The high score was in " + HiScoreDict["HiScoreMatchName"] + " with " + HiScoreDict["WinningTeam"] +" Team winning " + str(HiScoreDict["HiScore"]) + " to " + str(HiScoreDict["LosingTeamScore"]) + "." + '\n'
    else:
        hiScoreStr = "The high score was a tie in " + HiScoreDict["HiScoreMatchName"] + " with both teams scoring " + str(HiScoreDict["HiScore"]) + "." + '\n'
    
    if HiScoreDict["HiScore"] > 0:
        # Store output in one big string to avoid out-of-order printing when parallelized.
        consoleText = ("*"*75) + '\n' + \
        HiScoreDict["EventName"] + '\n' + \
        '\n' + \
        hiScoreStr + \
        "Blue Team - " + str(HiScoreDict["BlueTeams"][0]) + " " + str(HiScoreDict["BlueTeams"][1]) + " " + str(HiScoreDict["BlueTeams"][2]) + '\n' + \
        "Red Team - " + str(HiScoreDict["RedTeams"][0]) + " " + str(HiScoreDict["RedTeams"][1]) + " " + str(HiScoreDict["RedTeams"][2]) + '\n' + \
        "*"*75 + '\n'
        
        print(consoleText, flush=True)
        
    return HiScoreDict


if __name__ == '__main__':
    # Executed as main script:
    # URL = "https://www.thebluealliance.com/event/2025mimil"
    # URL = 'https://www.thebluealliance.com/event/2025iscmp'
    URL = 'https://www.thebluealliance.com/event/2026txwac/feed'
    
    get_high_score(URL, "Week 1", True)
