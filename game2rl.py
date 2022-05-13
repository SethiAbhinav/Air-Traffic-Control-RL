from pygame import *
from game_ai import *
from highs import *
from waypoint import *
import info_logger
import menu_base
import conf
import argparse
import numpy as np
from aircraft import Aircraft
from mdp import *

STATE_MENU = 1
STATE_GAME = 2
STATE_DEMO = 3
STATE_HIGH = 4
STATE_KILL = 5
STATE_AGES = 6

# Define the distance a plane should be re-routed to when given an action
REROUTE_DISTANCE = 50

# Define the distance away from the airport where planes cannot reroute
MIN_AIRPORT_DISTANCE = 50


class Main:

    BG_COLOR = (0, 0, 0)

    def __init__(self, qTableFile=None, alpha = 0.5, lamda = 0.9, explore = 0.1 ):

        display.init()
        pygame.mixer.init()
        font.init()

        if(conf.get()['game']['fullscreen'] == True):
            self.screen = display.set_mode((1024, 768), pygame.FULLSCREEN)
        else:
            self.screen = display.set_mode((1024, 768))

        display.set_caption('ATC Version 2')

        self.menu = menu_base.menu_base(self.screen,150,25)
        self.menu.from_file('main_menu')
        self.ages = menu_base.menu_base(self.screen,150,25)
        self.ages.from_file('ages_menu')
        self.high = HighScore(self.screen)
        self.infologger = info_logger.info_logger()
        #Current visitor number
        self.id = int(self.infologger.get_id())


        # Initializing a default Sarsa object or with a pre-initialized Q-table
        if qTableFile is None:
            self.sarsa = Sarsa(alpha=alpha,lamda=lamda,explore=explore)
        else:
            self.sarsa = Sarsa(qTableFile,alpha=alpha,lamda=lamda,explore=explore)
        # Keep track of the running planes and their previous state and action
        # Key is the plane ID and the value is the tuple (state, action)
        self.planeHistory = {}

    def run(self):
        state = STATE_GAME
        exit = 0
        score = 0
        episodes = 0
        scores = []

        while (exit == 0):
            if (state == STATE_MENU):
                menuEndCode = None
                menuEndCode = self.menu.main_loop()
                self.infologger.writeout()
                if (menuEndCode == conf.get()['codes']['start']):
                    state = STATE_AGES
                    self.id += 1
                    self.infologger.add_value(self.id,'id',self.id)
                elif (menuEndCode == conf.get()['codes']['demo']):
                    state = STATE_DEMO
                elif (menuEndCode == conf.get()['codes']['high_score']):
                    state = STATE_HIGH
                elif (menuEndCode == conf.get()['codes']['kill']):
                    state = STATE_KILL
            elif (state == STATE_GAME):

                game = AIGame(self.screen, False)
                gameEndCode = 0
                game.start()
                while (gameEndCode == 0):
                    aircraft, rewards, collidingAircraft, gameEndCode, score = game.step()
                    self.trainSarsa(aircraft, collidingAircraft, rewards)

                self.infologger.add_value(self.id,'score',score)
                scores.append(score)
                s = np.array(scores)
                print("Episode {} over. \t Avg Score:{}".format(episodes, np.mean(s)))

                # Save the Q table every 25 episodes to save progress
                if episodes != 0 and episodes % 25 == 0:
                    self.sarsa.saveQ("q_tables/"+str(episodes)+"model.pickle")
                    scoresArray = np.array(scores)
                    np.save("episode_"+str(episodes)+'score.npy', scoresArray)

                # Update explore probability every 10 episodes
                if episodes != 0 and episodes % 10 == 0:
                    self.sarsa.setExplore(self.sarsa.explore*0.9)

                # Clear the plane history at the restart of every game
                self.planeHistory.clear()
                score = 0
                episodes += 1

                if (gameEndCode == conf.get()['codes']['kill']):
                    state = STATE_KILL
                elif (gameEndCode == conf.get()['codes']['user_end']):
                    state = STATE_MENU
                elif (gameEndCode == conf.get()['codes']['ac_collide']):
                    state = STATE_GAME
            elif (state == STATE_KILL):
                exit = 1
            game = None

    def trainSarsa(self, aircraft, collidingAircraft, rewards):
        # Handle all of the planes that are in collision radius of each other and keep track of the planes
        handledPlanes = []
        for (plane1, plane2) in collidingAircraft:

            if plane1 not in handledPlanes:
                handledPlanes.append(plane1)
            if plane2 not in handledPlanes:
                handledPlanes.append(plane2)

            state1 = self.getState(aircraft[plane1], aircraft[plane2])
            state2 = self.getState(aircraft[plane2], aircraft[plane1])


            # Getting distance to destination for the two planes
            dest1 = aircraft[plane1].destination.getLocation()
            dest2 = aircraft[plane2].destination.getLocation()
            # get locations & headings of planes
            loc1 = np.array(aircraft[plane1].getLocation())
            loc2 = np.array(aircraft[plane2].getLocation())
            d1_vec = loc1 - dest1
            d2_vec = loc2 - dest2
            # calculate distance between planes
            d1 = abs(np.linalg.norm(d1_vec))
            d2 = abs(np.linalg.norm(d2_vec))

            if plane1 not in self.planeHistory:
                self.planeHistory[plane1] = (state1, Action.N.value)
            else:
                history = self.planeHistory[plane1]
                p1_action = self.sarsa.update(history[0], history[1], state1, rewards[plane1])
                self.planeHistory[plane1] = (state1, p1_action)
                if (d1 > MIN_AIRPORT_DISTANCE and state1.d > REROUTE_DISTANCE):
                    self.queueAction(aircraft[plane1], Action(p1_action))

            if plane2 not in self.planeHistory:
                self.planeHistory[plane2] = (state2, Action.N.value)
            else:
                history = self.planeHistory[plane2]
                p2_action = self.sarsa.update(history[0], history[1], state2, rewards[plane2])
                self.planeHistory[plane2] = (state2, p2_action)
                if (d2 > MIN_AIRPORT_DISTANCE and state2.d > REROUTE_DISTANCE):
                    self.queueAction(aircraft[plane2], Action(p2_action))
        

        # For all the planes that are cruising on their own, make sure the table has their entry.
        for planeName in aircraft.keys():
            if planeName not in handledPlanes:
                plane = aircraft[planeName]
                state = State(0, 0, 0, plane.getDistanceToGo())
                if plane not in self.planeHistory:
                    self.planeHistory[planeName] = (state, Action.N.value)
                history = self.planeHistory[planeName]
                self.sarsa.updateQ(history[0], history[1], rewards[planeName], state, Action.N.value)


        # Take into account the planes that have reached their destination and propagate their reward
        activePlanes = np.array(list(aircraft.keys()))
        rewardKeys = np.array(list(rewards.keys()))
        destinationPlanes = np.setdiff1d(rewardKeys, activePlanes)
        if len(destinationPlanes) > 0:
            for plane in destinationPlanes:
                # Create a new terminal state
                state = State(0, 0, 0, 0)
                history = self.planeHistory[plane]
                self.sarsa.updateQ(history[0], history[1], rewards[plane], state, Action.N.value)



    def getState(self, plane1, plane2):
        # Handle exception where you pass in the wrong type
        if not isinstance(plane1, Aircraft):
            raise Exception("Arg plane1 is type {}, must be type Aircraft".format(type(plane1)))
        if not isinstance(plane2, Aircraft):
            raise Exception("Arg plane2 is type {}, must be type Aircraft".format(type(plane2)))

        # Handle exception where you pass in the same plane
        if plane1.getIdent() == plane2.getIdent():
            raise Exception("Args plane1 and plane2 have the same identity: {}".format(plane1.getIdent()))

        # Helper function to calculate angles
        def wrapToPi(a):
            if isinstance(a, list):
                return [(x + np.pi) % (2*np.pi) - np.pi for x in a]
            return (a + np.pi) % (2*np.pi) - np.pi


        # get locations & headings of planes
        loc1 = np.array(plane1.getLocation())
        loc2 = np.array(plane2.getLocation())
        d_vec = loc2 - loc1

        head1 = plane1.getHeading()
        head2 = plane2.getHeading()

        # calculate distance between planes
        d = abs(np.linalg.norm(d_vec))

        # calculate the rho
        # absolute angle to other plane location
        dirHeading = abs(np.arctan(d_vec[1]/d_vec[0]) * 180/np.pi)
        rho_accurate = abs(dirHeading - head1)

        # put in the bucket 0 to 35
        rho = int(np.around(rho_accurate/10))

        # calculate theta
        theta_accurate = abs(head2 - head1)

        # put in the bucket 0 to 35
        theta = int(np.around(theta_accurate/10))
        d = int(d)

        return State(d, rho, theta, plane1.getDistanceToGo())

    def queueAction(self, plane, action):
        def wrapToPi(a):
            if isinstance(a, list):
                return [(x + np.pi) % (2*np.pi) - np.pi for x in a]
            return (a + np.pi) % (2*np.pi) - np.pi

        location = plane.getLocation()

        # Initialize the Waypoint with the plane's current location as a placeholder
        newWaypoint = Waypoint(location)

        # Heading is returned as degrees to convert to radians
        heading = wrapToPi(plane.getHeading()*np.pi/180.0 - np.pi/2)

        # Calculate the new heading that the plane must go to inact the desired action
        if action == Action.HL:
            newHeading = wrapToPi(heading-np.pi/2)
        elif action == Action.ML:
            newHeading = wrapToPi(heading-np.pi/8)
        elif action == Action.HR:
            newHeading = wrapToPi(heading+np.pi/2)
        elif action == Action.MR:
            newHeading = wrapToPi(heading+np.pi/8)
        else:
            newWaypoint = None

        if (newWaypoint):

            # Using the new heading and the reroute distance, calculate a point along that heading
            reroutePoint = REROUTE_DISTANCE*np.array([np.cos(newHeading), np.sin(newHeading)])
            
            # Set the waypoint object
            newWaypoint.setLocation(location + reroutePoint)
            
            # Add the waypoint to the plane trajectory
            plane.addWaypoint(newWaypoint)



def getArgs(parser):
    parser.add_argument("-g", "--gametime", type=int, help="Gametime in seconds")
    parser.add_argument("-p", "--planes", type=int, help="Number of planes to spawn")
    parser.add_argument("-s", "--spawnpoints", type=int, help="Number of spawnpoints for planes")
    parser.add_argument("-d", "--destinations", type=int, help="Number of airport destinations")
    parser.add_argument("-o", "--obstacles", type=int, help="Number of obstacles")
    parser.add_argument("-f", "--fullscreen", action="store_true", help="Toggle fullscreen mode")
    parser.add_argument("-fr", "--framerate", type=int, help="Framerate of the game")
    parser.add_argument("-q", "--q_table", type=str, help="Filepath of a precalculated q table.")
    parser.add_argument("-lr", "--learning_rate", type=float, help="Learning rate for SARSA.")
    parser.add_argument("-e", "--exploration_probability", type=float, help="Exploration probability for SARSA.")
    parser.add_argument("-l", "--lamda", type=float, help="Discount factor for SARSA.")
    return parser.parse_args()


def override_config(args):
    if (args.gametime is not None):
        conf.get()['game']['gametime'] = args.gametime * 1000
    if (args.planes is not None):
        conf.get()['game']['n_aircraft'] = args.planes
    if (args.spawnpoints is not None):
        conf.get()['game']['n_spawnpoints'] = args.spawnpoints
    if (args.destinations is not None):
        conf.get()['game']['n_destinations'] = args.destinations
    if (args.obstacles is not None):
        conf.get()['game']['n_obstacles'] = args.obstacles
    if (args.fullscreen):
        conf.get()['game']['fullscreen'] = True
    if (args.framerate is not None):
        conf.get()['game']['n_framerate'] = args.framerate


if __name__ == '__main__':

    # Initialize the command line parser
    parser = argparse.ArgumentParser("Testing command line arguments.")
    # Get the arguments
    args = getArgs(parser)
    # Make the necessary changes to the game configuration
    override_config(args)


    if args.learning_rate is None:
        args.learning_rate = 0.5
    if args.lamda is None:
        args.lamda = 0.9
    if args.exploration_probability is None:
        args.exploration_probability = 0.1 

    if args.q_table is None:
        game_main = Main(alpha = args.learning_rate, lamda = args.lamda, explore=args.exploration_probability)
    else:
        game_main = Main(args.q_table,alpha = args.learning_rate, lamda = args.lamda, explore=args.exploration_probability)
    game_main.run()
