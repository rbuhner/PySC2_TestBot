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
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.data import Alert
import random, time

class TestBot2(sc2.BotAI):
    def __init__(self):
        self.CALL_ONCE = True

        global defense, offense
        defense = []
        offense = []

        global lAddon, halltech, hallreac
        lAddon = []
        halltech = []
        hallreac = []

    async def call_once(self):
        self.next_node = await self.get_next_expansion()

    async def on_step(self, iteration):
        if self.CALL_ONCE:
            self.CALL_ONCE = False
            await self.call_once()

        #Step Cycle
        await self.distribute_workers() # OPTIMIZE: Imported function, apparently not the best?
        await self.build_workers()
        await self.build_supply()
        await self.build_gas()
        await self.expand()

        await self.build_offense()
        await self.train_offense()
        await self.upgrade()
        await self.defend()
        await self.attack()

        time.sleep(0.1)

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

        # TODO: self.upgrade function/ality

    # OPTIMIZE: Need to account for a total pool of workers,
    #               so we're not building extra when surplus workers are incoming.
    async def build_workers(self):
        """ Builds units iff townhall has resources to utilize. """
        # OPTIMIZE: Break assigned/ideal_harvesters from can_afford, and search for nearby townhalls that need workers.
        for townhall in self.units(COMMANDCENTER).ready.idle:
            if self.can_afford(SCV):
                if townhall.assigned_harvesters < townhall.ideal_harvesters:
                    await self.do(townhall.train(SCV))
                else:
                    for ref in self.units(REFINERY).closer_than(15.0, townhall):
                        if ref.assigned_harvesters < ref.ideal_harvesters:
                            await self.do(townhall.train(SCV))
                            break

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
        global depots
        depots = self.units(SUPPLYDEPOT).ready | self.units(SUPPLYDEPOTLOWERED).ready

        if self.supply_left<6 and not self.already_pending(SUPPLYDEPOT):
            townhall = self.units(COMMANDCENTER).ready
            if townhall and self.can_afford(SUPPLYDEPOT):
                await self.build(SUPPLYDEPOT, near=townhall.first)

        for unit in self.units(SUPPLYDEPOT).ready:
            await self.do(unit(AbilityId.MORPH_SUPPLYDEPOT_LOWER))

    # OPTIMIZE: Tends to build WAY too many REFINERYs on a single geyser...
    async def build_gas(self):
        if self.can_afford(REFINERY) and self.units(REFINERY).amount+1<(self.time/30):
            for townhall in self.units(COMMANDCENTER).ready:
                for geyser in self.state.vespene_geyser.closer_than(15.0, townhall):
                    worker = self.select_build_worker(geyser.position)
                    if worker and not self.units(REFINERY).closer_than(1.0, geyser).exists and \
                    self.already_pending(REFINERY)<2:
                        await self.do(worker.build(REFINERY, geyser))

    # OPTIMIZE: For some reason waited until it had enough for two comms,
    #               then put both down on the same point?
    async def expand(self):
        if self.units(COMMANDCENTER).amount<(self.time/180) and self.can_afford(COMMANDCENTER) and \
        not self.already_pending(COMMANDCENTER):
            await self.expand_now()
            self.next_node = await self.get_next_expansion()

    async def better_placement(self, building: UnitTypeId, near: Union[Unit, Point2, Point3], \
    max_distance: int=20, random_alternative: bool=True, placement_step: int=2, add_on: bool=False) \
    -> Optional[Point2]:
        """An attempt at a placement finder that keeps space for addons."""
        assert isinstance(building, (AbilityId, UnitTypeId))
        assert isinstance(near, Point2)
        if isinstance(building, UnitTypeId):
            building = self._game_data.units[building.value].creation_ability
        else: #AbilityId
            building = self._game_data.abilties[building.value]

        if await self._client.query_building_placement(building, near)[0] == ActionResult.Success:
            if add_on and await self._client.query_building_placement(BARRACKSTECHLAB, )
                return near #Normal, need to change
        if max_distance == 0:
            return None

        for distance in range(placement_step, max_distance, placement_step):
            possible_positions = [Point2(p).offset(near).to2 for p in (
                [(dx, -distance) for dx in range(-distance, distance+1, placement_step)] +
                [(dx, distance) for dx in range(-distance, distance+1, placement_step)] +
                [(-distance, dy) for dy in range(-distance, distance+1, placement_step)] +
                [(distance, dy) for dy in range(-distance, distance+1, placement_step)]
            )]
            res = await self._client.query_building_placement(building, possible_positions)
            possible = [p for r, p in zip(res, possible_positions) if r == ActionResult.Success]
            if not possible:
                continue

            if random_alternative:
                return random.choice(possible)
            else:
                return min(possible, key=lambda p: p.distance_to(near))
        return None

    async def build_offense(self):
        if depots:
            if not self.units(BARRACKS).ready:
                if not self.already_pending(BARRACKS) and self.can_afford(BARRACKS):
                    await self.build(BARRACKS, self.main_base_ramp.barracks_correct_placement)
            elif not self.units(ENGINEERINGBAY).ready and not self.already_pending(ENGINEERINGBAY) and \
            self.can_afford(ENGINEERINGBAY):
                await self.build(ENGINEERINGBAY, \
                near=self.start_location.towards(self.game_info.map_center, distance=5), placement_step=1)
            elif self.units(BARRACKS).ready.amount<2:
                if not self.already_pending(BARRACKS) and self.can_afford(BARRACKS):
                    build_loc = await self.find_placement(UnitTypeId.BARRACKS, \
                    near=self.main_base_ramp.barracks_correct_placement)
                    if build_loc:
                        await self.build(BARRACKS, build_loc)

    async def build_defense(self):
        return None

    async def train_offense(self):
        global lAddon
        global halltech, hallreac

        if self.alert(Alert.AddOnComplete):
            lAddon.pop(0)

        if self.units(MARINE).amount<4:
            for hall in self.units(BARRACKS).ready.idle:
                if self.can_afford(MARINE):
                    await self.do(hall.train(MARINE))
        else:
            for hall in self.units(BARRACKS).ready:
                if hall.add_on_tag == 0 and hall in self.units(BARRACKS).ready.idle:
                    if len(halltech)<1:
                        await self.do(hall.build(BARRACKSTECHLAB))
                        halltech.append(hall)
                    else:
                        await self.do(hall.build(BARRACKSREACTOR))
                        hallreac.append(hall)
                    lAddon.append(hall)
                elif hall in hallreac:
                    if len(hall.orders)<2 and not hall in lAddon:
                        await self.do(hall.train(MARINE))
                elif hall in halltech:
                    if len(hall.orders)<1 and not hall in lAddon:
                        await self.do(hall.train(MARAUDER))

    async def upgrade(self):
        #ENGINEERINGBAY Research queuing
        for tech in self.units(ENGINEERINGBAY).ready.idle:
            if not self.already_pending_upgrade(UpgradeId.TERRANINFANTRYARMORSLEVEL1) and \
            self.can_afford(UpgradeId.TERRANINFANTRYARMORSLEVEL1):
                await self.do(tech.research(UpgradeId.TERRANINFANTRYARMORSLEVEL1))
            elif not self.already_pending_upgrade(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1) and \
            self.can_afford(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1):
                await self.do(tech.research(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1))

        #BARRACKSTECHLAB Research queuing
        for htech in self.units(BARRACKSTECHLAB).ready.idle:
            if not self.already_pending_upgrade(UpgradeId.COMBATSHIELD) and \
            self.can_afford(UpgradeId.UpgradeId.COMBATSHIELD):
                await self.do(htech.research(UpgradeId.COMBATSHIELD))
            elif not self.already_pending_upgrade(UpgradeId.CONCUSSIVESHELLS) and \
            self.can_afford(UpgradeId.CONCUSSIVESHELLS):
                await self.do(htech.research(UpgradeId.CONCUSSIVESHELLS))

    async def defend(self):
        global defense

        if defense and len(self.known_enemy_units)>0:
            target = random.choice(self.known_enemy_units).position
            for unit in (units for units in defense if len(units.orders)<1):
                await self.do(unit.attack(target))

    def find_enemy(self, state):
        if len(self.known_enemy_units)>0:
            return random.choice(self.known_enemy_units).position
        elif len(self.known_enemy_structures)>0:
            return random.choice(self.known_enemy_structures).position
        else:
            return self.enemy_start_locations[0]

    # OPTIMIZE: Would rather marines kept at top of map_ramps, need further research...
    # OPTIMIZE: Need rally points and the army to gather at them, current code is flaky at best.
    # OPTIMIZE: Doing some really janky things with the marines picked to go etc...
    async def attack(self):
        global defense, offense

        #Add all new units to defense force first
        for unit in (units for units in self.units(MARINE)|self.units(MARAUDER) if \
        not units in defense and not units in offense):
            defense.append(unit)
            await self.do(unit.move(self.next_node))

        #If defense force is big enough to attack, attack
        if len(defense)>6+(self.time/45):
            target=self.find_enemy(self.state)
            for unit in defense:
                defense.remove(unit)
                offense.append(unit)
                await self.do(unit.attack(target))
            for unit in (units for units in offense if len(units.orders)<1):
                await self.do(unit.attack(target))

        #Retreat if offense too weak
        if len(offense)<(6+(self.time/45))/3:
            for unit in offense:
                offense.remove(unit)
                defense.append(unit)
                await self.do(unit.move(self.next_node))

#--- Run Game ---#
run_game(maps.get("Abyssal Reef LE"), [
    #Human(Race.Terran,fullscreen=True), #If one wants to play against the bot.
    Bot(Race.Terran, TestBot2(), fullscreen=False),
    Computer(Race.Zerg, Difficulty.Easy) #Lets get min functionality against Easy before testing against Medium
], realtime=True)
