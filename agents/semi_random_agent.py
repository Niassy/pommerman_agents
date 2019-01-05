

from collections import defaultdict
import queue
import random

import numpy as np

from . import SimpleAgent
from .. import constants
from .. import utility

import math

print("SemiRandomAgent Bonjour")

class SemiRandomAgent(SimpleAgent):


    # For more information about the algorithm implemented here,
    # this paper above
    # "Exploration Methods for Connectionist Q-Learning in Bomberman"
    # (Algorithm 1)
    def semi_random_opponent(self,obs, action_space):

        action_choosed = 0
        my_position = tuple(obs['position'])
        bombs = self.convert_bombs(np.array(obs['bomb_blast_strength']))

        life_bombs = self.get_Bomb_Life( np.array(obs['bomb_life']) )

        print("life bomb ",life_bombs)

        board = np.array(obs['board'])
        size_bombs  = len(bombs)

        possible_actions = self.getPossibleActions(my_position,board)

        print("My pos = ",my_position)
        print("possible actions ",possible_actions)

        possible_actions = np.array(possible_actions)

        list_bombs =  []
        utility_actions = []

        unsafe_flamme_pos = []
        print("Bombs size ",bombs)
        for a in possible_actions:

            agent_blocked = self.WillGetBlocked(pos_agent = my_position, board_map = board, future_action = a)

            if agent_blocked:
                continue

            ################### first try to void flammes ######################
            #newY, newX = self.simulate_action(pos_agent=my_position,action=a)

            unsafe_pos,isInDangerFlamme = self.avoid_Flamme(pos_agent = my_position,board_map = board,future_action = a)

            # The agent is in danger by taking this action so discard this action
            if isInDangerFlamme:

                unsafe_flamme_pos.append( { "unsafe_action":a,"flamme_pos":unsafe_pos })

                continue


            # The agent is not menaces by the flammes by taking this action so
            # it will try to avoid bomb

            self.avoid_Bomb(pos_agent = my_position,board_map = board,bombs = bombs,life_bombs = life_bombs,
                            utility_actions = utility_actions,future_action = a)

        ############# Choose the best action########################

        bestAction  = self.greedilyPickBestActions(utility_actions)

        # There exist an action that is more preffered than the other
        if bestAction != -1:
            action_choosed = bestAction

        else:
            action_choosed = self.getRandomSafeAction(unsafe_flamme_pos=unsafe_flamme_pos,possible_actions =possible_actions
                                                      ,pos_agent = my_position, board_map = board)

        return action_choosed
        # Check if there is bomn in the map

    # This function chooses randomly an action but ensure that this action
    # will not make him in danger (ie flammes or bomb area)
    def getRandomSafeAction(self,unsafe_flamme_pos,possible_actions,pos_agent,board_map):

        random_best_action = 0
        safe_actions =[]
        for a in possible_actions:

            isUnsafe = False

            agent_blocked = self.WillGetBlocked(pos_agent=pos_agent, board_map=board_map, future_action=a)

            if agent_blocked:
                continue

            # If this action is in the unsafe list , discar it
            for unsafe in unsafe_flamme_pos:

                unsafe_action = unsafe["unsafe_action"]

                if a == unsafe_action:
                    isUnsafe = True
                    break

            # No need to take this actions
            if isUnsafe :
                continue

            safe_actions.append(a)


        if len(safe_actions) > 0:
            random_best_action = np.random.choice(  np.array(safe_actions)  )

        return random_best_action


    # Take the best action given action desirability
    def greedilyPickBestActions(self,actions_desirability):


        # Choose the best action
        bestAction = -1
        bestValue = -10000

        for utility in actions_desirability:
            action = utility["action"]
            desire_action = utility["desire"]

            if desire_action > bestValue:
                bestValue = desire_action
                bestAction = action


        return bestAction

    # Avoid flammes in the map
    # Sometimes,the agent get stuck because there are no bombs
    # but flammes remaining. And when the agent move, he dies
    def avoid_Flamme(self,pos_agent,board_map,future_action):

        ok = 4 in (board_map)  # There is still flames remaining  if true

        if ok == False:

            return False,None

        # There is still flames so avoid to move in the direction of flammes

        flammes_pos = self.getFlammesPosition(board_map=board_map)

        # See if the future action can lead the agent to danger

        newPos = self.simulate_action(pos_agent=pos_agent,action=future_action)

        # If the position is in range the flammes the agent dies

        if self.isInRangeFlammes(pos_agent=newPos,flammes_pos=flammes_pos):
            return True,newPos

        return False,None

    def WillGetBlocked(self,pos_agent,board_map,future_action):

        newPos = self.simulate_action(pos_agent=pos_agent, action=future_action)

        if self.isBlockedByBomb(newPos, board_map):

            return True

        return False

    # Function that helps the agent to avoid bom
    def avoid_Bomb(self,pos_agent,board_map,bombs,life_bombs,utility_actions,future_action):

        # No bomb to avoid
        if len(bombs) == 0:
            return False


        desire_action = 0
        #utility_actions = []
        for bomb_dict in bombs:

            my_dict = {"action": future_action, "desire": 0}

            bomb = bomb_dict["position"]

            distY, distX, dist = self.getDistance(pos_agent=pos_agent, pos_object=bomb)

            if self.isObstacleBetweenBombAndAgent(pos_agent=pos_agent,pos_bomb=bomb,board_map =board_map):
                continue

            if dist > 3 or distX > 4 or distY > 4:
                continue

            newPos = self.simulate_action(pos_agent=pos_agent,action=future_action)

            desire = self.getDesirability_FleeBomb(pos_agent=newPos, bomb=bomb_dict, future_action=future_action,
                                                   board_map=board_map)

            if dist == 0:
                #print("dist ",dist)
                dist = 1

            bomb_proximity = 1 / dist ** 2

            desire_action += desire + bomb_proximity

            # the desirability of choosinf this action
            my_dict["desire"] = desire_action
            utility_actions.append(my_dict)

        return True


    # Function that push forward the agent to move to an item
    def moveToItem(self):

        pass

    # Function that lead the agen to put bomb
    def throw_bomb(self):

        pass


    # Simultate the fact of taking action
    # Useful for makimg prediction
    def simulate_action (self,pos_agent,action):

        y,x = pos_agent
        #xNew,yNew = pos_agent
        yNew,xNew = pos_agent
        if action == 1: # up

            yNew-=1

        elif action == 2 :# down

            yNew+=1

        elif action == 3: # left

            xNew-=1

        elif action == 4 : # right

            xNew+=1

        return yNew,xNew


    def isSurrounded(self,x,y,board_map):

        if board_map[y - 1, x] != 0 and \
                board_map[y + 1, x] != 0 and \
                board_map[y, x - 1] != 0 and board_map[y, x + 1] != 0:
            return True

        return False

    def isBlockedByBomb(self,pos_agent,board_map):

        y,x = pos_agent

        moves =  [ (0,1),(0,-1) ,(1,0),(-1,0) ]

        free_move = 0
        for move in moves:

            my,mx = move

            ny, nx = y + my, x + mx

            if nx < 0 or nx > 10 \
                or ny < 0 or ny > 10:
                continue

            if board_map[ny,nx] != 0:
                continue

            free_move+=1

        return free_move == 0


        # checking left
        #if board_map[y,x -1] != 0 and
        #if y == 0 or y == 10:  # map height

            # if there is wall to the right and left
            #if board_map[y,x - 1]



        pass


    def act(self, obs, action_space):

        a = self.semi_random_opponent(obs, action_space)

        text = constants.Action(a)
        return a

    def convert_bombs(self,bomb_map):
        '''Flatten outs the bomb array'''
        ret = []
        locations = np.where(bomb_map > 0)
        for r, c in zip(locations[0], locations[1]):
            ret.append({
                'position': (r, c),
                'blast_strength': int(bomb_map[(r, c)])
            })

        return ret

    def get_Bomb_Life(self,bombs_life):

        ret = []
        locations = np.where(bombs_life > 0)
        for r, c in zip(locations[0], locations[1]):
            ret.append({
                'position': (r, c),
                'life': int(bombs_life[(r, c)])
            })

        return ret

    def getPossibleActions(self,my_pos,board_map):

        actions = [0,1,2,3,4,5]
        possibles = []


        directions = [
            constants.Action.Stop, constants.Action.Left,
            constants.Action.Right, constants.Action.Up, constants.Action.Down
        ]

        y,x = my_pos
        action_chosen = []
        # iterate though the action list and see which action is feasible
        for action in actions:

            move = False
            # get the value of the action
            if action == 1:   # Moving up

                if y >0 and  board_map[y - 1 ,x] == 0:  # ok you can pass
                    move = True

            elif action == 2 : # Moving down

                if  y < 10 and  board_map[y + 1,x] == 0:

                    move = True

            elif action == 3:   # moving left

                if x>0 and board_map[y,x - 1] == 0:
                    move = True

            elif action == 4 :   # Moving right

                if  x<10 and board_map[y,x + 1] == 0:

                    move = True

            if move == True:
                action_chosen.append(action)

            if action == 0 or action == 5:
                action_chosen.append(action)

        return  action_chosen

    def getDesirability_FleeBomb(self,pos_agent,bomb,future_action,board_map):

        bomb_pos = bomb["position"]
        bomb_range = bomb["blast_strength"]

        y_bomb, x_bomb = bomb_pos
        y, x = pos_agent

        distY, distX, dist = self.getDistance(pos_agent=pos_agent, pos_object=bomb_pos)

        #left, right, up, down = x_bomb - bomb_range, x_bomb + bomb_range, y_bomb - bomb_range, y_bomb + bomb_range

        #  Get the maximum position the range bomb can reach imn each direction
        # this is useful because the distance is computed as the difference between
        # the position of action and these positions above
        #left_range_pos = (y,left)
        #right_range_pos = (y, right)
        #up_range_pos = (up, x)
        #down_range_pos = (down, x)

        left_range_pos, right_range_pos, up_range_pos, down_range_pos = self.getBombBlastPosition(bomb = bomb)
        #distY, distX, dist = self.getDistance(pos_agent=pos_agent,pos_object=bomb_pos)

        # No need to compute the other direction

        desirabilty = 0


        # The more the agent is close to the bomb the higher is this value
        score_far_bomb = dist


        isAtLeft = self.isAgentAtLeft(pos_agent=pos_agent, pos_object=bomb_pos)
        isAtRight = self.isAgentAtRight(pos_agent=pos_agent, pos_object=bomb_pos)
        isAtUp = self.isAgentAtUp(pos_agent=pos_agent, pos_object=bomb_pos)
        isAtDown = self.isAgentAtDown(pos_agent=pos_agent, pos_object=bomb_pos)

        if self.isAgentAtLeft(pos_agent=pos_agent,pos_object=bomb_pos) or \
            self.isAgentAtRight(pos_agent=pos_agent, pos_object=bomb_pos) :

            dir= 0
            if isAtLeft:
                dir = left_range_pos
            else:
                dir = right_range_pos

            distY, distX, dist = self.getDistance(pos_agent=pos_agent, pos_object=dir)
            #distY, distX, dist = self.getDistance(pos_agent=pos_agent, pos_object=dir)

            # No need to evaluate ar bomb

            #if math.fabs(distX-dir) > 4:
                #return 0

            desirabilty = math.fabs(distX) + score_far_bomb

        elif self.isAgentAtUp(pos_agent=pos_agent,pos_object=bomb_pos) or \
                self.isAgentAtDown(pos_agent=pos_agent, pos_object=bomb_pos):

            dir= 0
            if isAtUp:
                dir = up_range_pos
            else:
                dir = down_range_pos

            distY, distX, dist = self.getDistance(pos_agent=pos_agent, pos_object=dir)
            desirabilty =  math.fabs(distY) + score_far_bomb

            # No need to evaluate ar bomb


            #if math.fabs(distY-dir) > 4:
                #return 0

            up, left = left_range_pos

            #if math.fabs(distX, left) > 4:
                #return 0


        if self.isAgentInRangeBomb(pos_agent = pos_agent,bomb = bomb):
            desirabilty*=-1

        if self.isAgentInDiagonal(pos_agent = pos_agent,pos_object= bomb_pos):

            # desirability to be safe
            desir_safe = 10
            desirabilty = dist *desir_safe + score_far_bomb


        return desirabilty

    # comoute the distance from the bomb given a position
    # it is equal to -1 if the bomb blast can not reach the range even if it
    # has infinite blast (ie when the agent is in the diagonal or when the agent
    # when a wall is betwenn the agent and the bomb)

    ##################### Utility function ##########################

    # True if there is object between agent anf bomb
    def isObstacleBetweenBombAndAgent(self,pos_agent,pos_bomb,board_map):

        y1, x1 = pos_agent
        y2, x2 = pos_bomb

        range_search = 4

        for i in range(1,range_search +1):

            y,x = pos_agent
            if self.isAgentAtLeft(pos_agent,pos_bomb):

                x+=1

                if x > 10:
                    break

                if (y,x) == (y2,x2):
                    break

                if board_map[y,x] != 0 and board_map[y,x] != 4:
                    return True

            elif self.isAgentAtRight(pos_agent, pos_bomb):

                x -= 1

                if x <0:
                    break

                if (y, x) == (y2, x2):
                    break

                if board_map[y, x] != 0 and board_map[y, x] != 4:
                    return True


            elif self.isAgentAtUp(pos_agent, pos_bomb):

                y += 1

                if y > 10:
                    break

                if (y, x) == (y2, x2):
                    break

                if board_map[y, x] != 0 and board_map[y, x] != 4:
                    return True

            elif self.isAgentAtDown(pos_agent, pos_bomb):

                y -= 1

                if y <0:
                    break
                if (y, x) == (y2, x2):
                    break

                if board_map[y, x] != 0 and board_map[y, x] != 4:
                    return True

        return False

    def isSamePos(self,pos_agent,pos_object):

        y1, x1 = pos_agent
        y2, x2 = pos_object

        if x1 == x2 and y1 == y2:
            return True

        return False


    def isAgentAtRight(self,pos_agent,pos_object):

        y1,x1 = pos_agent
        y2,x2 = pos_object

        if  x1 > x2:
            return True

        return False

    def isAgentAtLeft(self,pos_agent,pos_object):

        return self.isAgentAtRight(pos_agent,pos_object) == False and self.isSamePos(pos_agent,pos_object) == False

    def isAgentAtUp(self,pos_agent,pos_object):

        y1,x1 = pos_agent
        y2,x2 = pos_object

        if  y1 < y2:
            return True

        return False

    def isAgentAtDown(self,pos_agent,pos_object):

        return self.isAgentAtUp(pos_agent,pos_object) == False and self.isSamePos(pos_agent,pos_object) == False

    def isAgentInDiagonal(self,pos_agent,pos_object):

        y1, x1 = pos_agent
        y2, x2 = pos_object

        if x1 != x2  and y1 != y2:
            return True

        return False

    def getDistance(self,pos_agent,pos_object):

        y1, x1 = pos_agent
        y2, x2 = pos_object

        distX = math.fabs(x1 -x2 )
        distY = math.fabs(y1 -y2)

        dist = math.sqrt(distX ** 2 + distY ** 2  )

        return distY,distX,dist


    # Get the range bomb position in all directions
    def getBombBlastPosition(self,bomb):

        bomb_pos = bomb["position"]
        bomb_range = bomb["blast_strength"]

        y_bomb, x_bomb = bomb_pos

        left, right, up, down = x_bomb - bomb_range, x_bomb + bomb_range, y_bomb - bomb_range, y_bomb + bomb_range

        #  Get the maximum position the range bomb can reach imn each direction
        # this is useful because the distance is computed as the difference between
        # the position of action and these positions above
        left_range_pos = (y_bomb, left)
        right_range_pos = (y_bomb, right)
        up_range_pos = (up, x_bomb)
        down_range_pos = (down, x_bomb)

        return left_range_pos,right_range_pos,up_range_pos,down_range_pos


    # Determine if aan agent is in the range of the blast of the bomb
    def isAgentInRangeBomb(self,pos_agent,bomb):

        bomb_pos = bomb["position"]
        bomb_range = bomb["blast_strength"]

        y_bomb, x_bomb = bomb_pos
        y, x = pos_agent

        left_range_pos, right_range_pos, up_range_pos, down_range_pos = self.getBombBlastPosition(bomb)

        unsafe_positions = []

        unsafe_positions.append(left_range_pos)
        unsafe_positions.append(right_range_pos)
        unsafe_positions.append(up_range_pos)
        unsafe_positions.append(down_range_pos)

        # The agent is in the diagonal so he is safe
        if self.isAgentInDiagonal(pos_agent=pos_agent,pos_object=bomb_pos) :
            return True

        for unsafe_pos in unsafe_positions:

            unsafeY,unsafeX = unsafe_pos

            if self.isAgentAtLeft(pos_agent = pos_agent,pos_object=bomb_pos):

                if x < unsafeX: return True

                return False

            if self.isAgentAtRight(pos_agent = pos_agent,pos_object=bomb_pos):

                if x > unsafeX : return True

                return False

            if self.isAgentAtDown(pos_agent = pos_agent,pos_object=bomb_pos):

                if y > unsafeY : return True

                return False

            if self.isAgentAtUp(pos_agent = pos_agent,pos_object=bomb_pos):

                if y < unsafeY: return True

                return False

        return  True

    # Return flase the position of the agent collids with a flamme
    def isInRangeFlammes(self,pos_agent,flammes_pos):

        for danger_pos in flammes_pos:

            # Retriewing the position
            h,w,_ = danger_pos

            if self.isSamePos(pos_agent=pos_agent,pos_object=(h,w)):
                return True

        # No flammes active for the action
        return False


    def getFlammesPosition(self,board_map):

        H, W = board_map.shape
        critical_pos = []
        for h in range(H):
            for w in range(W):

                val = board_map[h, w]

                if val == 4:
                    critical_pos.append((h, w, val))

        return critical_pos
