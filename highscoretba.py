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
        
        # Page with no scores on it, skip.
        if currMatchidx == 0:
            if '<li class="active"><a href="#teams"' in line:
                return HiScoreDict
        #
        
        # Get event name.
        if HiScoreDict["EventName"] == '':
            s = re.search(r'<h1 [\w|=|"]*\s?id="event-name">([^<]+)', line)
            if s is not None:
                HiScoreDict["EventName"] = s.group(1)
                HiScoreDict["EventName"] = HiScoreDict["EventName"].replace(" 2026", "")
        #
        
        # Found a new match.
        if '<tr class="visible-lg">' in line:
            currMatchidx = lineNum
        #
        
        # Found a score value, check against HiScore.
        if scoreFound:
            n = re.search(r'  <span[^>]*>(\d+)', line)
            if n is not None:
                currTeamScore = int(n.group(1))
                if currTeamScore > HiScoreDict["HiScore"]:
                    HiScoreDict["HiScore"] = currTeamScore
                    newHighScore = True
                scoreFound = False
        #
        
        # Found a team score.
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
        
        # New high score found, get teams and match info.
        if '<tr class="hidden-lg compact-row">' in line and newHighScore:
            HiScoreDict["BlueTeams"].clear()
            HiScoreDict["RedTeams"].clear()
            # Re-iterate from when we first found the match until the current line.
            for nline in html_data[currMatchidx:lineNum+1]:
                if nline == '':
                    continue
                
                # Get found points awarded to each team.
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
                    
                    # If there is a space in the red/blue team tag, it must say "red/blue winner". Losing team has no space here.
                    if p.group(2) == ' ':
                        HiScoreDict["WinningTeam"] = currTeamColor
                        
                r = re.search(r'(\d+)</span>', nline)
                if r is not None:
                    currScore = int(r.group(1))
                    if currScore != HiScoreDict["HiScore"]:
                        HiScoreDict["LosingTeamScore"] = currScore
                    
            newHighScore = False
            loserTeamHighScore = False
            
            # Subtract penalty points if normalize argument is passed.
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
                
                # First check if normalized high score is less than the old high score found - if so, check if the normalized losing score is higher than the old high score.
                # If the normalized losing score is now the highest score, we must flip around the losing/winning scores and WinningTeam values.
                #
                # example scenario - Match 1 is Red Team 10 and Blue Team 15 with no penalty points.
                # Match 2 is Red Team 20 and Blue Team 50 with Blue Team being awarded 40 penalty points.
                # After normalizing, Red Team has 20 and Blue Team has 10. So we must now show that red team is the "winner" with their normalized score of 20.
                #
                # If the normalized losing score is not the highest score, and the normalized winning score is less than the old high score, reset the HiScoreDict to its old value.
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
                # If normalized high score is actually the highest, set them in HiScoreDict and make a copy of the dictionary in oldHighScoreDict.
                elif not loserTeamHighScore:
                    HiScoreDict["HiScore"] = normalizedHighScore
                    HiScoreDict["LosingTeamScore"] = normalizedLosingScore
                    oldHighScoreDict = copy.deepcopy(HiScoreDict)
            #
        #
        
        lineNum += 1
    
    # Remove non-ascii characters and escaped characters from Event Name.
    HiScoreDict["EventName"] = str(normalize('NFKD', HiScoreDict["EventName"]).encode('ascii','ignore'))
    HiScoreDict["EventName"] = HiScoreDict["EventName"].replace('b\'', '')
    HiScoreDict["EventName"] = HiScoreDict["EventName"].replace('\'', '')
    HiScoreDict["EventName"] = HiScoreDict["EventName"].replace('amp;', '')

    if HiScoreDict["HiScore"] > 0:
        # Store output in one big string to avoid out-of-order printing when parallelized.
        consoleText = ("*"*75) + '\n' + \
        HiScoreDict["EventName"] + '\n' + \
        '\n' + \
        "The high score was in " + HiScoreDict["HiScoreMatchName"] + " with " + HiScoreDict["WinningTeam"] +" Team winning " + str(HiScoreDict["HiScore"]) + " to " + str(HiScoreDict["LosingTeamScore"]) + "." + '\n' + \
        "Blue Team - " + str(HiScoreDict["BlueTeams"][0]) + " " + str(HiScoreDict["BlueTeams"][1]) + " " + str(HiScoreDict["BlueTeams"][2]) + '\n' + \
        "Red Team - " + str(HiScoreDict["RedTeams"][0]) + " " + str(HiScoreDict["RedTeams"][1]) + " " + str(HiScoreDict["RedTeams"][2]) + '\n' + \
        "*"*75 + '\n'
        
        print(consoleText, flush=True)
        
    return HiScoreDict


if __name__ == '__main__':
    # Executed as main script:
    # URL = "https://www.thebluealliance.com/event/2025mimil"
    # URL = 'https://www.thebluealliance.com/event/2025iscmp'
    URL = 'https://www.thebluealliance.com/event/2025tuis3'
    
    get_high_score(URL, "Week 1", True)
