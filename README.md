# FIRSTHighScoreReport
## Parses scores for the current year on www.thebluealliance.com and creates a high score text report.

### Requirements
Python must be installed, version 3.13 or higher is recommended.

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
  
### TbaScores.py

### highscoretba.py