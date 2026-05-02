# FIRSTHighScoreReport
## Parses scores for the current year on www.thebluealliance.com and creates a high score text report.

### Requirements
Python must be installed, version 3.13 or higher is recommended.

### Config
| Value | Description |
| :---- | :---------- |
| numThreads | Set on line 12 of TbaScores.py. Configures how many threads are invoked when the script is ran. Default value is 56.|

### Usage
#### Run the following command before first run to ensure all required python packages are installed:
```
pip install -r requirements.txt
```

To create a report, run GetFIRSThiScores.bat -> this will output hiscores.txt with the following formatting:

...  
\***************************************************************************  
NE District WPI Event  
  
The high score was Quals 60 with Blue Team winning 669 to 165.  
Blue Team - 4628 1768 3467  
Red Team - 1474 3205 2168  
\***************************************************************************  
  
  
Event                                            Week       Match               High Score  
\-----------------------------------------------------------------------------------------------  
CA District Central Valley Event                 Week 4     Playoff Match 1            825  
Avrasya Regional                                 Week 5     Playoff Match 7            769  
...  
  
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!  
The highest score for this year is 825 at CA District Central Valley Event:  
  
Red won 825 to 169 in Playoff Match 1.  
Red Team - 1323 2367 254  
Blue Team - 11296 1351 1671  
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!  
  
\--- Execution time: 13.69 seconds ---  
<br>
<br>
  
#### Ignore penalty points awarded to teams
To create a **standardized** high score report, run GetFIRSThiScores_normalized.bat, this subtracts any penalty points awarded to each team.
This is useful for games in which a high amount of penalty points can be awarded to teams, which can skew perceived actual performance.
This creates hiscores_normalized.txt which has the same format shown above.
<br>
<br>
  
### GetFIRSThiScores.bat
1. Deletes previous high score text file.
2. Calls the python script using the following command:
```
powershell "python TbaScores.py | tee hiscores.txt"
```
powershell is used in order to utilize the built-in 'tee' command. Output can be shown to console and written to file.

### TbaScores.py
1. Looks for '-n' option to normalize scores.
2. Uses request library to retrieve html data from https://www.thebluealliance.com/events.
3. Creates an array of Event URLs (e.g. https://www.thebluealliance.com/event/2026midtr/feed).
4. For each entry in the Event URL array, a thread is invoked via the Parallel function from the joblib library to call get_high_score from highscoretba.py.
The event url, week number, and normalize score argument are passed in. By default, number of jobs is set to 56 for 56 threads.
The number of threads can be customized by changing the variable 'numThreads'.
5. Results are returned as a dictionary and appended to the array 'results'.
6. The results are iterated through to find the highest score, and sorted.
7. The sorted dictionaries are printed to console with a summary of the highest score.
<br>

### highscoretba.py
#### get_foul_points
1. Retrieves html data from the supplied URL (e.g. https://www.thebluealliance.com/match/2026midtr_qm1).
2. Parses html data to find foul points awarded to red and blue teams, and returns them.

#### get_high_score
1. Retrieves RSS feed data from the supplied URL (e.g. https://www.thebluealliance.com/event/2026midtr/feed).
2. Parses RSS feed data to retrieve information such as event name, and scores for current match.
3. When a score is found for that event, it is compared to the current highest score found. If a new high score is found, more information is obtained from RSS feed data.
4. RSS tags are used to find that match's URL, match name, and teams playing in that match.
5. If scores are being normalized, calls get_foul_points with the match URL to retrieve foul points.
6. Results for this event are printed to console and returned to parent function.