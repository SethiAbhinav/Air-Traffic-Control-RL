# Air-Traffic-Control-RL

The 6th semester project for course on Reinforcement Learning.


## What did we do?
Simulated an aircraft Traffic Control agent which maneuvers around other planes to reach a common destination. Had to modify a PyGame based game to make it a Markov Decision Process (MDP) and formualted the state-space, action-space and reward setup. Next, we trained the agent using the SARSA algorithm.

## More details + Results?
A detailed report is present in the "RL_Project_report.pdf" file.

## Team:
Abhinav Sethi 

Hritik Bana

## Demonstration:
A demo run is shown below. The demo shows episodes that end either when all 50 planes reach the destination or any two planes collide. (A lot of parameters, such as number of planes, destinations, obstacles etc can be modified as per convenience):

To replicate run type ```python game2rl.py -p 50``` on the command line.


https://user-images.githubusercontent.com/84278440/168409735-6731280f-0131-4390-98c0-20db1c123732.mp4

