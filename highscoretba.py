import requests
import re
import sys
import copy
import html
from unicodedata import normalize

def get_foul_points(URL):
    redFoulPoints = 0
    blueFoulPoints = 0
    tempRedFoul = 0
    redFound = False
    blueFound = False
    foulsFound = False
    lineNum = 0
    currScoreidx = 0
    
    response = requests.get(URL)
    response.encoding = 'utf-8'
    html_data = response.text
    html_data = html_data.split('\n')
    
    for line in html_data:
        # Blank line, ignore. Or, new format has two separate foul categories, only concerned in the one without 'Major Fouls'.
        if line.strip() == '':
            lineNum += 1
            continue
        elif "Major Fouls" in line:
            lineNum += 1
            continue
        
        if '<td class="red' in line: # Found a set of 'scores'
            currScoreidx = lineNum
        
        
        if '<td>Foul' in line: # Only run when we have found the 'foul' section. Only look at lines after the red "score"
            i = 0
            while i < len(html_data[currScoreidx:]):
                nline = html_data[currScoreidx + i]
                # The keys 'redScore' and 'blueScore' are used multiple times in the same page. We are only concerned with the Foul Points.
                # The way the html table is construction has the format:
                # redScore 5
                # Foul Points
                # blueScore 0
                #
                # So we must save every 'redScore' we find, overwriting the last in tempRedFoul, until we find the 'Foul Points' tag, and then save/return those values.
                
                # *The format of foul scores vary on a year to year basis. Above is for 2025 onwards.
                # Format can look like this:
                # redScore
                # 4(+20)
                # 0
                # Foul Points
                # blueScore
                # 0
                # 3(+15)
                # With some variation in each year, some years have negative foul points, which are still "subtracted" from the total score
                if redFound:
                    p = re.search(r'^\s+(\d+)', nline)
                    if p:
                        tempRedFoul = int(p.group(1))
                        redFound = False
                    else:
                        q = re.search(r'([\+|\-]\d+)', nline) # support for 2022/2023 foul format
                        if q:
                            tempRedFoul = int(q.group(1))
                        if '/' in nline: # Go ahead and grab next line for other foul points, then set flag to false.
                            r = re.search(r'([\+|\-]\d+)', html_data[currScoreidx + i + 1])
                            if r:
                                tempRedFoul += int(r.group(1))
                            redFound = False
                        
                if blueFound and foulsFound:
                    p = re.search(r'^\s+(\d+)', nline)
                    if p:
                        blueFoulPoints = int(p.group(1))
                        redFoulPoints = tempRedFoul
                        return redFoulPoints, blueFoulPoints
                    else:
                        q = re.search(r'([\+|\-]\d+)', nline) # support for 2022/2023 foul format
                        if q:
                            blueFoulPoints = int(q.group(1))
                        if '/' in nline: # Go ahead and grab next line for other foul points, then set flag to false.
                            r = re.search(r'([\+|\-]\d+)', html_data[currScoreidx + i + 1])
                            if r:
                                blueFoulPoints += int(r.group(1))
                            redFoulPoints = tempRedFoul
                            return redFoulPoints, blueFoulPoints
                
                # Add support for foul points in older years
                if '<td class="red"' in nline:
                    p = re.search(r'<td class="red"[^>]*>([\-|\+]*\d+)', nline)
                    if p:
                        tempRedFoul = int(p.group(1))
                        q = re.search(r'>[\-|\+]*\d+\s*/\s*([\-|\+]*\d+)<', nline) # support for 2020/2021 foul format
                        if q:
                            tempRedFoul += int(q.group(1))
                    else:
                        redFound = True
                
                if '<td class="blue"' in nline and foulsFound:
                    p = re.search(r'<td class="blue"[^>]*>([\-|\+]*\d+)', nline)
                    if p:
                        blueFoulPoints = int(p.group(1))
                        q = re.search(r'>[\-|\+]*\d+\s*/\s*([\-|\+]*\d+)<', nline) # support for 2020/2021 foul format
                        if q:
                            blueFoulPoints += int(q.group(1))
                        redFoulPoints = tempRedFoul
                        return redFoulPoints, blueFoulPoints
                    else:
                        blueFound = True
                
                if '<td>Fouls' in nline:
                    foulsFound = True
                # Add support for foul points in older years (end)
                
                if '<td class="redScore" colspan="2">' in nline:
                    redFound = True
                    
                if '<td>Foul Points</td>' in nline:
                    foulsFound = True
                    
                if '<td class="blueScore" colspan="2">' in nline:
                    blueFound = True
                
                i += 1
                #
            #        
        #
        
        lineNum += 1
                    
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
            if s:
                HiScoreDict["EventName"] = s.group(1)
                HiScoreDict["EventName"] = re.sub(r'\s\d{4}$', '', HiScoreDict["EventName"]) # Remove year at the end of string
                lineNum += 1
                continue
        #
        
        # Found a new match.
        if '<title>' in line:
            currMatchidx = lineNum
        #
        
        # Found a score value, check against HiScore. Ignores scores of '-1'.
        if '<h1>' in line:
            n = re.search(r'<h1>[\w|\s]+:\s(\d+)</h1>', line)
            if n:
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
                    if s:
                        MatchURL = s.group(1)
                        redFoulPoints, blueFoulPoints = get_foul_points(MatchURL)
                        foulPointsFound = True
                
                if '<title>' in nline and not matchNameFound:
                    o = re.search('<title>(.+)</title>', nline)
                    if o:
                        HiScoreDict["HiScoreMatchName"] = o.group(1)
                        matchNameFound = True
                        
                if '<h1>' in nline:
                    p = re.search(r'<h1>(\w+)\sAlliance:\s(\d+)</h1>', nline)
                    currTeamColor = p.group(1)
                    if currTeamColor == "Blue":
                        blueScore = int(p.group(2))
                    elif currTeamColor == "Red":
                        redScore = int(p.group(2))
                elif '<li>' in nline:
                    q = re.search(r'<li>(\d+)\w*</li>', nline) # A letter is sometimes at the end of a team number in some years
                    if q:
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
    
    # Convert html entities into symbols.
    HiScoreDict["EventName"] = str(normalize('NFKD', HiScoreDict["EventName"]).encode('ascii','ignore'))
    HiScoreDict["EventName"] = HiScoreDict["EventName"].replace('b\'', '')
    HiScoreDict["EventName"] = HiScoreDict["EventName"].replace('\'', '')
    HiScoreDict["EventName"] = html.unescape(HiScoreDict["EventName"])
    
    
    hiScoreStr = ""
    if HiScoreDict["WinningTeam"] != "TIE":
        hiScoreStr = "The high score was in " + HiScoreDict["HiScoreMatchName"] + " with " + HiScoreDict["WinningTeam"] +" Team winning " + \
            str(HiScoreDict["HiScore"]) + " to " + str(HiScoreDict["LosingTeamScore"]) + "." + '\n'
    else:
        hiScoreStr = "The high score was a tie in " + HiScoreDict["HiScoreMatchName"] + " with both teams scoring " + str(HiScoreDict["HiScore"]) + "." + '\n'
    
    redTeamStr = "Red Team - "
    blueTeamStr = "Blue Team - "
    for team in HiScoreDict["RedTeams"]:
        redTeamStr += str(team) + " "
    for team in HiScoreDict["BlueTeams"]:
        blueTeamStr += str(team) + " "
    
    if HiScoreDict["HiScore"] > 0:
        # Store output in one big string to avoid out-of-order printing when parallelized.
        consoleText = ("*"*75) + '\n' + \
        HiScoreDict["EventName"] + '\n' + \
        '\n' + \
        hiScoreStr + \
        redTeamStr + '\n' + \
        blueTeamStr + '\n' + \
        "*"*75 + '\n'
        
        print(consoleText, flush=True)
        
    return HiScoreDict


if __name__ == '__main__':
    # Executed as main script:
    # URL = "https://www.thebluealliance.com/event/2025mimil"
    # URL = 'https://www.thebluealliance.com/event/2025iscmp'
    URL = 'https://www.thebluealliance.com/event/2016mdbb/feed'
    
    get_high_score(URL, "Week 1", True)
