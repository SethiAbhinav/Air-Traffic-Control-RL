from enum import Enum
import numpy as np
import random as random
import pickle

# Creating the SARSA class
class Sarsa:
    d = 200
    rho = 36
    theta = 36
    na = 5
    ns = d * rho * theta
    explore = 0.1
    alpha = 0.5
    lamda = 0.9

    def __init__(self, qTableFile=None, alpha=alpha, lamda = lamda, explore=explore):
        # Initialize the q table as empty or with a file
        if qTableFile is None:
            self.Q = {}
        else:
            self.loadQ(qTableFile)
        self.alpha = alpha
        self.lamda = lamda
        self.explore = explore
        print("Initializing SARSA with these parameters: learning_rate: {}, lambda: {}, exploration_probability: {}.".format(self.alpha,self.lamda,self.explore))

    def setExplore(self,explore = explore):
        self.explore = explore
        print("Changing SARSA parameters to: learning_rate: {}, lambda: {}, exploration_probability: {}.".format(self.alpha,self.lamda,self.explore))


    def update(self, prevState, prevAction, state, reward):

        # If the state has never been seen before, initialize the state with 0 values for all actions
        if prevState not in self.Q:
            self.Q[prevState] = [0] * self.na
        if state not in self.Q:
            self.Q[state] = [0] * self.na

        action = self.chooseAction(state)
        self.updateQ(prevState, prevAction, reward, state, action)
        return action


    # Follow epsilon-greedy policy to choose action.
    def chooseAction(self, state):

        # Setting a random threshold
        rand = random.random()
        if rand < self.explore:
            action = random.randint(0,self.na-1)
        else:
            action = np.argmax(self.Q[state])
        return action

    def updateQ(self, prevState, prevAction, reward, state, action):
        if state not in self.Q:
            self.Q[state] = [0] * self.na
        Q_val = self.Q[prevState][prevAction]
        self.Q[prevState][prevAction] += self.alpha*(reward + self.lamda*self.Q[state][action] - Q_val)

    def saveQ(self, filename="q_tables/default.pickle"):

        # Saves the Q table in a file we can access later
        with open(filename, 'wb') as handle:
            pickle.dump(self.Q, handle, protocol=pickle.HIGHEST_PROTOCOL)
        print("Q Table saved at {}!".format(filename))

    def loadQ(self, filename="q_tables/default.pickle"):
        
        # Loads a previously trained Q table
        with open(filename, 'rb') as handle:
            self.Q = pickle.load(handle)
        print("Q Table {} loaded!".format(filename))



# Create the action enumeration
class Action(Enum):
    N = 0   # Nothing
    HL = 1  # Hard Left
    ML = 2  # Mid Left
    MR = 3  # Mid Right
    HR = 4  # Hard Right

# Create the state object 
class State:
    def __init__(self, d=0, rho=0, theta=0, distanceToGo=0):
        self.d = d
        self.rho = rho
        self.theta = theta
        self.distanceToGo = distanceToGo

