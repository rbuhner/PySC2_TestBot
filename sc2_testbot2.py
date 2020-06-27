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
from sc2.data import ActionResult, Alert
from sc2.position import Point2, Point3
from sc2.unit import Unit

import random, time
from typing import Optional, Union # mypy type checking

class TestBot2(sc2.BotAI):
    def __init__(self):
        self.CALL_ONCE = True

        global defense, offense, staging, retreat
        defense = []
        offense = []
        staging = []
        retreat = []

        global lAddon, halltech, hallreac
        lAddon = []
        halltech = []
        hallreac = []

    async def call_once(self):
        global staging_loc, rallyPoint

        self.next_node = await self.get_next_expansion()
        self.current_node = self.start_location

        rallyPoint = await self.find_placement(SUPPLYDEPOT, near=self.next_node)
        staging_loc = await self.find_placement(SUPPLYDEPOT, near=self.game_info.map_center)

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
        await self.build_defense()
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

    async def build_workers(self):
        """ Builds units iff townhall has resources to utilize. """
        aharvest=0
        iharvest=0
        townhalls = self.units(COMMANDCENTER).ready|self.units(ORBITALCOMMAND).ready

        for townhall in townhalls:
            aharvest+=townhall.assigned_harvesters
            iharvest+=townhall.ideal_harvesters
        for ref in self.units(REFINERY).ready:
            aharvest+=ref.assigned_harvesters
            iharvest+=ref.ideal_harvesters

        for townhall in self.units(COMMANDCENTER).ready.idle:
            if self.units(BARRACKS).ready:
                if aharvest+8<iharvest and self.can_afford(SCV):
                    aharvest+=1
                    await self.do(townhall.train(SCV))
            else:
                if aharvest<iharvest and self.can_afford(SCV):
                    aharvest+=1
                    await self.do(townhall.train(SCV))
        for townhall in self.units(ORBITALCOMMAND).ready.idle:
            if aharvest<iharvest and self.can_afford(SCV):
                aharvest+=1
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
        global depots
        depots = self.units(SUPPLYDEPOT).ready | self.units(SUPPLYDEPOTLOWERED).ready
        townhall = self.units(COMMANDCENTER).ready | self.units(ORBITALCOMMAND).ready

        if townhall and self.supply_left<2+2*(self.time/60) and not self.already_pending(SUPPLYDEPOT) and \
        (self.supply_used+self.supply_left)<200 and self.can_afford(SUPPLYDEPOT):
            await self.build(SUPPLYDEPOT, near=townhall.first)

        for unit in self.units(SUPPLYDEPOT).ready:
            await self.do(unit(AbilityId.MORPH_SUPPLYDEPOT_LOWER))

    # OPTIMIZE: Limited to just overbuilding on a geyer by one now...
    async def build_gas(self):
        if self.units(REFINERY).amount+1<(self.time/30):
            for townhall in self.units(COMMANDCENTER).ready:
                for geyser in self.state.vespene_geyser.closer_than(15.0, townhall):
                    worker = self.select_build_worker(geyser.position)
                    if worker and not self.units(REFINERY).closer_than(1.0, geyser).exists and \
                    self.already_pending(REFINERY)<2 and self.can_afford(REFINERY):
                        await self.do(worker.build(REFINERY, geyser))

    async def expand(self):
        """ Every 3 minutes, waits until it can afford a Command Center, then expands to the next site. """
        global rallyPoint

        if self.units(COMMANDCENTER).amount<(self.time/180) and self.can_afford(COMMANDCENTER) and \
        not self.already_pending(COMMANDCENTER):
            self.current_node = self.next_node
            await self.expand_now()
            self.next_node = await self.get_next_expansion()
            if self.current_node == self.next_node:
                print("Current node and Next node returned same point/object.")
            rallyPoint = await self.find_placement(SUPPLYDEPOT, near=self.next_node)

    async def better_placement(self, building: UnitTypeId, near: Union[Unit, Point2, Point3], \
    max_distance: int=20, random_alternative: bool=True, placement_step: int=2, add_on: bool=True) \
    -> Optional[Point2]:
        """ An attempt at a placement finder that keeps space for addons. """
        assert isinstance(building, (AbilityId, UnitTypeId))
        assert isinstance(near, Point2)
        if isinstance(building, UnitTypeId):
            building = self._game_data.units[building.value].creation_ability
        else: #AbilityId
            building = self._game_data.abilties[building.value]
        ao = self._game_data.units[UnitTypeId.SUPPLYDEPOT.value].creation_ability
        b_r = 1.5
        ao_r = 1
        ao_p = [b_r+ao_r,ao_r-b_r]
        lls_p = [-(b_r+ao_r),ao_r-b_r]
        lus_p = [-(b_r+ao_r),b_r-ao_r]

        ns = await self.can_place(building, near)
        if ns:
            if add_on:
                #All coords from bottomleft x/y
                nsao = await self.can_place(SUPPLYDEPOT,Point2(ao_p).offset(near).to2)
                nslls = await self.can_place(SUPPLYDEPOT,Point2(lls_p).offset(near).to2)
                nslus = await self.can_place(SUPPLYDEPOT,Point2(lus_p).offset(near).to2)
                if nsao and nslls and nslus:
                    print("Near:", near)
                    return near
            else:
                return near
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

            if add_on:
                #All coords from bottomleft x/y
                possible_ao = [Point2(p).offset(ao_p).to2 for p in possible]
                rao = await self._client.query_building_placement(ao, possible_ao)
                aoPossible = [p for r, p in zip(rao, possible) if r == ActionResult.Success]

                possible_lls = [Point2(p).offset(lls_p).to2 for p in aoPossible]
                rlls = await self._client.query_building_placement(ao, possible_lls)
                llsPossible = [p for r, p in zip(rlls, aoPossible) if r == ActionResult.Success]

                possible_lus = [Point2(p).offset(lus_p).to2 for p in llsPossible]
                rlus = await self._client.query_building_placement(ao, possible_lus)
                adjPossible = [p for r, p in zip(rlus, llsPossible) if r == ActionResult.Success]
                if not adjPossible:
                    continue
                else:
                    possible=adjPossible

            if random_alternative:
                pos = random.choice(possible)
                pao = Point2(pos).offset(ao_p).to2
                rao = await self.can_place(SUPPLYDEPOT, pao)
                plls = Point2(pos).offset(lls_p).to2
                rlls = await self.can_place(SUPPLYDEPOT, plls)
                plus = Point2(pos).offset(lus_p).to2
                rlus = await self.can_place(SUPPLYDEPOT, plus)
                print("RPos:",pos,"|",pao,"-",rao,"|",plls,"-",rlls,"|",plus,"-",rlus)
                return pos
            else:
                pos = min(possible, key=lambda p: p.distance_to(near))
                print("MPos:", pos)
                return pos
        return None

    async def build_offense(self):
        if depots:
            if not self.units(BARRACKS).ready:
                if not self.already_pending(BARRACKS) and self.can_afford(BARRACKS):
                    build_loc = await self.better_placement(BARRACKS, \
                    near=self.main_base_ramp.barracks_correct_placement)
                    if build_loc:
                        await self.build(BARRACKS, build_loc)
            elif not self.units(ENGINEERINGBAY).ready and not self.already_pending(ENGINEERINGBAY) and \
            self.can_afford(ENGINEERINGBAY):
                await self.build(ENGINEERINGBAY, near=self.start_location.towards(
                    self.game_info.map_center, distance=5
                ), placement_step=1)
            elif self.units(BARRACKS).ready.amount<self.time/150:
                if not self.already_pending(BARRACKS) and self.can_afford(BARRACKS):
                    if self.current_node == self.start_location:
                        build_loc = await self.better_placement(BARRACKS, \
                        near=self.main_base_ramp.barracks_correct_placement)
                    else:
                        build_loc = await self.better_placement(BARRACKS, \
                        near=self.current_node.towards(
                            self.game_info.map_center, distance=5
                        ), add_on=True)
                    if build_loc:
                        await self.build(BARRACKS, build_loc)
            elif not self.units(FACTORY).ready:
                if not self.already_pending(FACTORY) and self.can_afford(FACTORY):
                    build_loc = await self.better_placement(FACTORY, \
                    near=self.main_base_ramp.barracks_correct_placement)
                    if build_loc:
                        await self.build(FACTORY, build_loc)
            elif not self.units(ARMORY).ready and not self.already_pending(ARMORY) and \
            self.can_afford(ARMORY):
                await self.build(ARMORY, near=self.start_location.towards(
                    self.game_info.map_center, distance=5
                ), placement_step=1)
            elif not self.units(STARPORT).ready and not self.already_pending(STARPORT) and \
            self.can_afford(STARPORT):
                build_loc = await self.better_placement(STARPORT, \
                near=self.main_base_ramp.barracks_correct_placement)
                if build_loc:
                    await self.build(STARPORT, build_loc)

    async def build_defense(self):
        if self.units(BARRACKS).ready:
            for townhall in self.units(COMMANDCENTER).ready.idle:
                if self.can_afford(ORBITALCOMMAND):
                    await self.do(townhall(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND))
            for townhall in self.units(ORBITALCOMMAND).ready:
                abilities = await self.get_available_abilities(townhall)
                # OPTIMIZE: Should have MULE per ORBITALCOMMAND for increased mineral gain...
                if not self.units(UnitTypeId.MULE):
                    if AbilityId.CALLDOWNMULE_CALLDOWNMULE in abilities:
                        await self.do(townhall(
                            AbilityId.CALLDOWNMULE_CALLDOWNMULE,
                            self.state.mineral_field.closest_to(townhall)
                        ))
                # OPTIMIZE: Should scan not just base but around enemy base to find
                #           expansions, enemy army/composition, etc...
                elif not self.is_visible(self.enemy_start_locations[0]):
                    if AbilityId.SCANNERSWEEP_SCAN in abilities:
                        await self.do(townhall(
                            AbilityId.SCANNERSWEEP_SCAN,
                            self.enemy_start_locations[0]
                        ))

    async def train_offense(self):
        global lAddon
        global halltech, hallreac
        forceMin = 4+(self.time/30)

        if self.alert(Alert.AddOnComplete):
            lAddon.pop(0)

        if self.units(MARINE).amount<4:
            for hall in self.units(BARRACKS).ready.idle:
                if self.can_afford(MARINE):
                    await self.do(hall.train(MARINE))
        else:
            for hall in self.units(BARRACKS).ready:
                if hall.add_on_tag == 0 and hall in self.units(BARRACKS).ready.idle \
                and self.can_afford(BARRACKSTECHLAB):
                    if len(halltech)<1:
                        lAddon.append(hall)
                        await self.do(hall.build(BARRACKSTECHLAB))
                        halltech.append(hall)
                    elif self.can_afford(BARRACKSREACTOR):
                        lAddon.append(hall)
                        await self.do(hall.build(BARRACKSREACTOR))
                        hallreac.append(hall)
                elif hall in hallreac:
                    if len(hall.orders)<2 and not hall in lAddon and self.can_afford(MARINE):
                        await self.do(hall.train(MARINE))
                elif hall in halltech:
                    if len(hall.orders)<1 and not hall in lAddon and self.can_afford(MARAUDER):
                        await self.do(hall.train(MARAUDER))

            for port in self.units(STARPORT).ready.idle:
                if self.units(MEDIVAC).amount<forceMin/5 and self.can_afford(MEDIVAC):
                    await self.do(port.train(MEDIVAC))

    async def upgrade(self):
        #ENGINEERINGBAY Research queuing
        for tech in self.units(ENGINEERINGBAY).ready.idle:
            if not self.already_pending_upgrade(UpgradeId.TERRANINFANTRYARMORSLEVEL1) and \
            self.can_afford(UpgradeId.TERRANINFANTRYARMORSLEVEL1):
                await self.do(tech.research(UpgradeId.TERRANINFANTRYARMORSLEVEL1))
            elif not self.already_pending_upgrade(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1) and \
            self.can_afford(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1):
                await self.do(tech.research(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1))
            elif self.units(ARMORY).ready:
                if not self.already_pending_upgrade(UpgradeId.TERRANINFANTRYARMORSLEVEL2) and \
                self.can_afford(UpgradeId.TERRANINFANTRYARMORSLEVEL2):
                    await self.do(tech.research(UpgradeId.TERRANINFANTRYARMORSLEVEL2))
                elif not self.already_pending_upgrade(UpgradeId.TERRANINFANTRYWEAPONSLEVEL2) and \
                self.can_afford(UpgradeId.TERRANINFANTRYWEAPONSLEVEL2):
                    await self.do(tech.research(UpgradeId.TERRANINFANTRYWEAPONSLEVEL2))
                elif not self.already_pending_upgrade(UpgradeId.TERRANINFANTRYARMORSLEVEL3) and \
                self.can_afford(UpgradeId.TERRANINFANTRYARMORSLEVEL3):
                    await self.do(tech.research(UpgradeId.TERRANINFANTRYARMORSLEVEL3))
                elif not self.already_pending_upgrade(UpgradeId.TERRANINFANTRYWEAPONSLEVEL3) and \
                self.can_afford(UpgradeId.TERRANINFANTRYWEAPONSLEVEL3):
                    await self.do(tech.research(UpgradeId.TERRANINFANTRYWEAPONSLEVEL3))

        #BARRACKSTECHLAB Research queuing
        for htech in self.units(BARRACKSTECHLAB).ready.idle:
            abilities = await self.get_available_abilities(htech)
            if AbilityId.RESEARCH_COMBATSHIELD in abilities and \
            self.can_afford(AbilityId.RESEARCH_COMBATSHIELD):
                await self.do(htech(AbilityId.RESEARCH_COMBATSHIELD))
            elif AbilityId.RESEARCH_CONCUSSIVESHELLS in abilities and \
            self.can_afford(AbilityId.RESEARCH_CONCUSSIVESHELLS):
                await self.do(htech(AbilityId.RESEARCH_CONCUSSIVESHELLS))

        #ARMORY Research queuing
        for advtech in self.units(ARMORY).ready.idle:
            if not self.already_pending_upgrade(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL1) and \
            self.can_afford(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL1):
                await self.do(advtech.research(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL1))
            elif not self.already_pending_upgrade(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL2) and \
            self.can_afford(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL2):
                await self.do(advtech.research(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL2))
            elif not self.already_pending_upgrade(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL2) and \
            self.can_afford(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL2):
                await self.do(advtech.research(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL2))

    async def defend(self):
        global defense

        if defense and len(self.known_enemy_units)>0 and \
        not self.game_info.map_center.is_closer_than(
            self.current_node.distance_to_closest(self.known_enemy_units),
            self.current_node
        ):
            target = self.current_node.closest(self.known_enemy_units).position
            for unit in (units for units in self.getAllUnits() if units in defense and units.is_idle):
                await self.do(unit.attack(target))

    def find_enemy(self, state):
        if len(self.known_enemy_units)>0:
            return random.choice(self.known_enemy_units).position
        elif len(self.known_enemy_structures)>0:
            return random.choice(self.known_enemy_structures).position
        else:
            return self.enemy_start_locations[0]

    def getAllUnits(self):
        return self.units(MARINE) + self.units(MARAUDER) + self.units(MEDIVAC)

    # OPTIMIZE: Would rather marines kept at top of map_ramps, need further research...
    # OPTIMIZE: Need rally points and the army to gather at them.
    async def attack(self):
        """ Covers military AI, from the moment unit is recruited into defense,
         into staging to offense and retreat, and cycle. """
        global defense, offense, staging, retreat
        global staging_loc, isStaging
        forceMin = 4+(self.time/30)

        #Add all new units to defense force first
        for unit in (units for units in self.getAllUnits() if not units in defense and \
        not units in offense and not units in staging and not units in retreat):
            defense.append(unit)
            await self.do(unit.move(self.next_node))

        if defense: defense = list(units for units in self.getAllUnits() if units in defense)
        if staging: staging = list(units for units in self.getAllUnits() if units in staging)
        if offense: offense = list(units for units in self.getAllUnits() if units in offense)

        #If defense force is big enough to attack, attack
        if len(defense)>forceMin:
            staging += defense
            defense = []
            for unit in staging:
                await self.do(unit.attack(staging_loc))
            print("D>S Defense:", len(defense), "|Staging:", len(staging),
            "|Offense:", len(offense), "|ForceMin:", forceMin)
        elif defense:
            for unit in defense:
                if staging and len(staging)<forceMin:
                    staging += defense
                    defense = []
                    await self.do(unit.attack(staging_loc))
                elif unit.is_idle and unit.position.distance_to(self.next_node)>5:
                    await self.do(unit.attack(self.next_node))

        #Staging force until units are grouped together
        # OPTIMIZE: Need to organify the max radius of staging->offense
        if len(staging)>=forceMin:
            #p=[]
            #for unit in (units for units in self.getAllUnits() if units in staging):
                #p.append(unit.position)
            p = list(units.position for units in staging)
            if Point2.center(p).distance_to_furthest(p)<8:
                target=self.find_enemy(self.state)
                offense += staging
                staging = []
                for unit in offense:
                    if unit in self.units(MEDIVAC) and unit.is_idle:
                        await self.do(unit.attack(random.choice(offense)))
                    elif unit.is_idle:
                        await self.do(unit.attack(target))
                print("S>O Defense:", len(defense), "|Staging:", len(staging),
                "|Offense:", len(offense), "|ForceMin:", forceMin)
            else:
                for unit in staging:
                    if unit.is_idle and unit.position.distance_to(staging_loc)>5:
                        await self.do(unit.attack(staging_loc))

        if offense:
            #Retreat if offense too weak
            if len(offense)<forceMin/4:
                retreat = offense
                offense = []
                for unit in retreat:
                    await self.do(unit.move(self.next_node))

                defense += retreat
                retreat = []
                print("O>D Defense:", len(defense), "|Staging:", len(staging),
                "|Offense:", len(offense), "|ForceMin:", forceMin)
            #If part of/offense loses/kills target, retarget
            else:
                target = self.find_enemy(self.state)
                for unit in offense:
                    if unit.is_idle:
                        await self.do(unit.attack(target))

#--- Run Game ---#
run_game(maps.get("Abyssal Reef LE"), [
    #Human(Race.Terran,fullscreen=True), #If one wants to play against the bot.
    Bot(Race.Terran, TestBot2(), fullscreen=False),
    Computer(Race.Zerg, Difficulty.Hard) #Lets get min functionality against Easy before testing against Medium
], realtime=True)
