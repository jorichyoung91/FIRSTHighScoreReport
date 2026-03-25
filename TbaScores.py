import requests
import re
import sys
import time
from highscoretba import get_high_score
from joblib import Parallel, delayed
from tabulate import tabulate

start_time = time.time()

mainTbaURL = "https://www.thebluealliance.com/events"
numThreads = 56
evntURLs = []

HighestScore = 0

currScoreDict = {}
HighestScoreDict = {}
allScores = []
currWeek = ""
normalizeScores = False

if len(sys.argv) > 1:
    if sys.argv[1] == "-n":
        print("Normalizing Scores! Team Scores will have foul points deducted.\n")
        normalizeScores = True
    elif sys.argv[1] != "":
        print("Warning: unrecognized command entered: ", sys.argv[1])

response = requests.get(mainTbaURL)
html_data = response.text
html_data = html_data.split('\n')

for line in html_data:
    r = re.search(r'<a href="/event/([^"]+)', line)
    if r is not None:
        evntURLs.append(["https://www.thebluealliance.com/event/" + r.group(1), currWeek])
    
    s = re.search(r'<h2 id="[\w|-]+">([\w|\s|\d]+)\s', line)
    if s is not None:
        currWeek = s.group(1)
        
# call high score subroutine for events in parallel
results = Parallel(n_jobs=numThreads)(delayed(get_high_score)(event[0], event[1], normalizeScores) for event in evntURLs)

for result in results:
    if result["HiScore"] > HighestScore:
        HighestScore = result["HiScore"]
        HighestScoreDict = result
    if result["HiScore"] != 0:
        allScores.append({'Event': result['EventName'], 'Week': result['EventWeek'], 'Match': result['HiScoreMatchName'], 'High Score': result['HiScore']})
#

# # old single thread implementation
# for event in evntURLs:
    # currScoreDict = get_high_score(event[0], event[1])
    # if currScoreDict["HiScore"] > HighestScore:
        # HighestScore = currScoreDict["HiScore"]
        # HighestScoreDict = currScoreDict
    # allScores.append({'Event': currScoreDict['EventName'], 'Week': currScoreDict['EventWeek'], 'High Score': currScoreDict['HiScore']})
#

allScores = sorted(allScores, key=lambda d: d['High Score'], reverse=True)

header = allScores[0].keys()
rows =  [x.values() for x in allScores]
print('')
print(tabulate(rows, header))

print('\n')
print("!"*75)

if normalizeScores:
    print("The highest *normalized* score for this year is " + str(HighestScore) + " at " + HighestScoreDict["EventName"] + ":")
else:
    print("The highest score for this year is " + str(HighestScore) + " at " + HighestScoreDict["EventName"] + ":")
    
print('')

print(HighestScoreDict["WinningTeam"] + " won " + str(HighestScore) + " to " + str(HighestScoreDict["LosingTeamScore"]) + " in " + HighestScoreDict["HiScoreMatchName"] + ".")
print("Red Team - " + str(HighestScoreDict["RedTeams"][0]) + " " + str(HighestScoreDict["RedTeams"][1]) + " " + str(HighestScoreDict["RedTeams"][2]))
print("Blue Team - " + str(HighestScoreDict["BlueTeams"][0]) + " " + str(HighestScoreDict["BlueTeams"][1]) + " " + str(HighestScoreDict["BlueTeams"][2]))

print("!"*75)
print('')

print("--- Execution time: %s seconds ---" % (round(time.time() - start_time, 2)))
