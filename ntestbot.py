import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer

from sc2.units import Units
from sc2.unit import Unit
from sc2.position import Point2, Point3

from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.buff_id import BuffId
from sc2.ids.ability_id import AbilityId

import random
import cv2
import numpy as np

class NTestBot(sc2.BotAI):
    class NUnit():
        #TODO: Create subclass to wrap any unit/building in a neural wrapper
        #   exposing the stats and actions to neural I/O
        def __init__():
            doSomething=False

        def input():
            #TODO: This should return a neural input of all unit's
            #   stats/position/abilities.
            doSomething=True

        def takeAction(n):
            #TODO: This should take a nerual action and map it to a unit action,
            #   like moving, move/attack, or using an ability.
            doSomething=True

    def __init__(self):
        self.CALL_ONCE=False

    async def intel(self):
        #print(dir(self))
        aieye=np.zeros((self.game_info.map_size[1],self.game_info.map_size[0],3), np.uint8)

    async def on_step(self, iteration):
        return None

class nNet():
    def __init__(self, x, y):
        self.input = x
        self.weights1 = np.random.rand(self.input.shape[1], 4)
        self.weights2 = np.random.rand(4, 1)
        self.y = y
        self.output = np.zeroes(y.shape)

    def sig(self, x):
        return 1/(1+np.exp(-x))
    def d_sig(self, x):
        return x*(1-x)

    def feedforward(self):
        self.layer1 = sigmoid(np.dot(self.input, self.weights1))
        self.output = sigmoid(np.dot(self.layer1, self.weights2))

    def backprop(self):
        #Application of the chain rule to find derivative of the loss function
        #   with respect to weights2 and weights1
        d_weights2 = np.dot(self.layer1.T, (2*(self.y-self.output)* \
        sigmoid_derivative(self.output)))
        d_weights1 = np.dot(self.input.T, (np.dot(2*(self.y-self.output)* \
        sigmoid_derivative(self.output), self.weights2.T)*sigmoid_derivative(self.layer1)))

        #Update the weights with the derivative(slope) of the loss function
        self.weights1 += d_weights1
        self.weights2 += d_weights2
