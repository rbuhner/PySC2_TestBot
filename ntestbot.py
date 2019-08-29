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
    def __init__(self}):
        self.CALL_ONCE=False

    async def intel(self):
        #print(dir(self))
        aieye=np.zeros((self.game_info.map_size[1],self.game_info.map_size[0],3), np.uint8)

    async def on_step(self, iteration):
