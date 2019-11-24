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
