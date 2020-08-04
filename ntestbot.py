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
from coroutine_decorator import coroutine_decorator

class NTestBot(sc2.BotAI):
    class coroutine(object):
        """ Credit to https://stackoverflow.com/questions/21808113/is-there-anything-similar-to-self-inside-a-python-generator """
        def __new__(cls, func):
            @wraps(func)
            def decorated(*args, **kwargs):
                o = object.__new__(cls)
                o.__init__(func, args, kwargs)
                return o
            return decorated

        def __init__(self, generator, args, kw):
            self.generator = generator(self, *args, **kw)
            next(self.generator)

        def __iter__(self):
            return self

        def __next__(self):
            return next(self.generator)

        next = __next__

        def send(self, value):
            return self.generator.send(value)

    @coroutine
    def coroute_neuron(self, dict_in: dict, f_bias: float, l_out: list):
        """ Coroutine input is still linear, and too slow to keep up with mimo. """
        neuro_in = dict_in  #Neuron input pointers:weights
        bias = f_bias       #Neuron bias
        neuro_out = l_out   #Neuron output pointers
        act = 0.0           #Current activation level

        try:
            while True:
                d_node, d_in = yield
                if d_node in neuro_in:
                    act += d_in * neuro_in[d_node]
                #---Not working---#
                """
                More need an object that firing neurons can write into a float[] finputs area,
                 which is then pulled through the activation sumation and passed on to the output neurons
                 respective float finputs section, through the pointer on file from setup/creation of link.
                """

        except GeneratorExit:
            for n in neuro_out:
                n.close()

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
        self.nin = coroute_neuron

    async def intel(self):
        #print(dir(self))
        aieye=np.zeros((self.game_info.map_size[1],self.game_info.map_size[0],3), np.uint8)

    async def on_step(self, iteration):
