import requests
import re
import sys
import time
import argparse
from highscoretba import get_high_score
from joblib import Parallel, delayed
from tabulate import tabulate
from datetime import date

start_time = time.time()

mainTbaURL = "https://www.thebluealliance.com/events/"
numThreads = 56
evntURLs = []

HighestScore = 0

# currScoreDict = {}
HighestScoreDict = {}
allScores = []
currWeek = ""

currentYear = date.today().year
parser = argparse.ArgumentParser()
parser.add_argument('-n', '--normalize', action='store_true')
parser.add_argument('-y', '--year')
args = parser.parse_args()

if args.normalize:
    print("Normalizing Scores! Team Scores will have foul points deducted.\n")

if args.year:
    year = int(args.year)
    if year < 1992 or year > int(currentYear):
        sys.exit("Error: Year out of range: " + args.year)
    print("Finding high score from year " + args.year)
    mainTbaURL += args.year

# Get html page from the blue alliance events page
response = requests.get(mainTbaURL)
html_data = response.text
html_data = html_data.split('\n')

# Use regex to find event names and construct URLs
for line in html_data:
    r = re.search(r'<a href="/event/([^"]+)', line)
    if r:
        evntURLs.append(["https://www.thebluealliance.com/event/" + r.group(1) + '/feed', currWeek])
    
    s = re.search(r'<h2 id="[\w|-]+">([\w|\s]+)\s', line)
    if s:
        currWeek = s.group(1)
        
# call high score function for each event in parallel
results = Parallel(n_jobs=numThreads)(delayed(get_high_score)(event[0], event[1], args.normalize) for event in evntURLs)

for result in results:
    if result["HiScore"] > HighestScore:
        HighestScore = result["HiScore"]
        HighestScoreDict = result
    # Create dictionary subset that doesnt have events with no scores, and to only have event name, week, high score, and the match with that score
    if result["HiScore"] != 0:
        allScores.append({'Event': result['EventName'], 'Week': result['EventWeek'], 'Match': result['HiScoreMatchName'], 'High Score': result['HiScore']})
#

# # old single thread implementation
# for event in evntURLs:
    # currScoreDict = get_high_score(event[0], event[1], args.normalize)
    # if currScoreDict["HiScore"] > HighestScore:
        # HighestScore = currScoreDict["HiScore"]
        # HighestScoreDict = currScoreDict
    # allScores.append({'Event': currScoreDict['EventName'], 'Week': currScoreDict['EventWeek'], 'High Score': currScoreDict['HiScore']})
#

# Create and print table of high score from each event
allScores = sorted(allScores, key=lambda d: d['High Score'], reverse=True)

if allScores:
    header = allScores[0].keys()
else:
    print("No scores found!")
    sys.exit(0)
    
rows =  [x.values() for x in allScores]
print('')
print(tabulate(rows, header))

print('\n')
print("!"*75)

if args.normalize:
    print("The highest *normalized* score for this year is " + str(HighestScore) + " at " + HighestScoreDict["EventName"] + ":")
else:
    print("The highest score for this year is " + str(HighestScore) + " at " + HighestScoreDict["EventName"] + ":")
    
print('')

if HighestScoreDict["WinningTeam"] != "TIE":
    print(HighestScoreDict["WinningTeam"] + " won " + str(HighestScore) + " to " + str(HighestScoreDict["LosingTeamScore"]) + " in " + HighestScoreDict["HiScoreMatchName"] + ".")
else:
    print("There was a tie with a score of " + str(HighestScore) + " in " + HighestScoreDict["HiScoreMatchName"] + ".")

redTeamStr = "Red Team - "
blueTeamStr = "Blue Team - "
for team in HighestScoreDict["RedTeams"]:
    redTeamStr += str(team) + " "
for team in HighestScoreDict["BlueTeams"]:
    blueTeamStr += str(team) + " "

print(redTeamStr)
print(blueTeamStr)

print("!"*75)
print('')

print("--- Execution time: %s seconds ---" % (round(time.time() - start_time, 2)))
