import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer, Human
from sc2.constants import COMMANDCENTER, SUPPLYDEPOT, REFINERY, BARRACKS, \
    ENGINEERINGBAY, BUNKER, SENSORTOWER, FACTORY, STARPORT, ARMORY, FUSIONCORE, \
    SIEGETANKSIEGED, SIEGETANK, COMMANDCENTERFLYING, BARRACKSTECHLAB, BARRACKSREACTOR, \
    FACTORYTECHLAB, FACTORYREACTOR, STARPORTTECHLAB, STARPORTREACTOR, FACTORYFLYING, \
    STARPORTFLYING, SCV, BARRACKSFLYING, SUPPLYDEPOTLOWERED, MARINE, REAPER, MARAUDER, \
    MEDIVAC, BATTLECRUISER, PLANETARYFORTRESS, ORBITALCOMMAND, ORBITALCOMMANDFLYING, MULE
from sc2.ids.upgrade_id import UpgradeId
import random

class TestBot2(sc2.BotAI):
    def __init__(self):
        self.CALL_ONCE = True

    async def call_once(self):
        self.MAIN_BASE = await self.get_next_expansion()

    async def on_step(self, iteration):
        if self.CALL_ONCE:
            self.CALL_ONCE = False
            await self.call_once()

        #Step Cycle
        await self.distribute_workers() # OPTIMIZE: Imported function
        await self.build_workers()
        await self.build_supply()

        # TODO: Incorporate ramp logic in ground attacks, to prevent bottlenecking.
        """
        Snip of main_base_ramp code for comparison

        # Returns the Ramp instance of the closest main-ramp to start location. Look in game_info.py for more information
        if hasattr(self, "cached_main_base_ramp"):
            return self.cached_main_base_ramp
        self.cached_main_base_ramp = min(
            {ramp for ramp in self.game_info.map_ramps if len(ramp.upper2_for_ramp_wall) == 2},
            key=(lambda r: self.start_location.distance_to(r.top_center)),
        )
        return self.cached_main_base_ramp
        """

    async def build_workers(self):
        """ Builds units iff townhall has resources to utilize. """
        # OPTIMIZE: Break assigned/ideal_harvesters from can_afford, and search for nearby townhalls that need workers.
        for townhall in self.units(COMMANDCENTER).ready.idle:
            if townhall.assigned_harvesters<townhall.ideal_harvesters and self.can_afford(SCV):
                await self.do(townhall.train(SCV))

    async def build_supply(self):
        """ Builds supply building if low (5) on supply.
            Focusing on Terran due to A) already having a Protoss bot, and B) haven't learned zerg egg finding yet. """
        """
        Relev snippets

        if mf.position._distance_squared(
                    cluster[0].position
                ) < RESOURCE_SPREAD_THRESHOLD and mf_height == self.get_terrain_height(cluster[0].position):

        # distance offsets from a gas geysir
        offsets = [(x, y) for x in range(-9, 10) for y in range(-9, 10) if 75 >= x ** 2 + y ** 2 >= 49]
        centers = {}
        # for every resource group:
        for resources in resource_groups:
            # possible expansion points
            # resources[-1] is a gas geysir which always has (x.5, y.5) coordinates, just like an expansion
            possible_points = (
                Point2((offset[0] + resources[-1].position.x, offset[1] + resources[-1].position.y))
                for offset in offsets
            )
            # filter out points that are too near
            possible_points = [
                point
                for point in possible_points
                if all(point.distance_to(resource) >= (7 if resource in geysers else 6) for resource in resources)
            ]
            # choose best fitting point
            result = min(possible_points, key=lambda p: sum(p.distance_to(resource) for resource in resources))
            centers[result] = resources
        # Returns dict with center of resources as key, resources (mineral field, vespene geyser) as value
        return centers
        """
        # OPTIMIZE: Organify supply_left, likely through neural-like behavior.
        # OPTIMIZE: 1stL: Since terran, queue supply to lower upon completion.
        if self.supply_left<5 and not self.already_pending(SUPPLYDEPOT):
            if self.units(COMMANDCENTER).exists and self.can_afford(SUPPLYDEPOT):
                await self.build(SUPPLYDEPOT, near=self.MAIN_BASE)

#--- Run Game ---#
run_game(maps.get("Abyssal Reef LE"), [
    #Human(Race.Terran,fullscreen=True), #If one wants to play against the bot.
    Bot(Race.Terran, TestBot2(), fullscreen=False),
    Computer(Race.Zerg, Difficulty.Easy) #Lets get min functionality against Easy before testing against Medium
], realtime=True)
