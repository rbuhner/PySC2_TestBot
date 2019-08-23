import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import NEXUS, PROBE, PYLON, ASSIMILATOR, GATEWAY, \
  CYBERNETICSCORE, FORGE, STALKER
from sc2.ids.upgrade_id import UpgradeId
import random

#roughly 165 iterations per minute?
class TestBot(sc2.BotAI):
  def __init__(self):
      self.CALL_ONCE=True

  async def call_once(self):
      self.MAIN_BASE=await self.get_next_expansion()

  async def on_step(self, iteration):
      if self.CALL_ONCE:
          self.CALL_ONCE=False
          await self.call_once()
      await self.distribute_workers()
      await self.build_workers()
      await self.build_pylons()
      await self.build_assimilators()
      await self.expand()
      await self.build_offense_buildings()
      await self.build_offense_units()
      await self.upgrade()
      await self.defend()
      await self.attack()

  async def build_workers(self):
      for nexus in self.units(NEXUS).ready.idle:
          if self.units(PROBE).amount<self.units(NEXUS).amount*22 and self.can_afford(PROBE):
              await self.do(nexus.train(PROBE))

  async def build_pylons(self):
      if self.supply_left < 5 and not self.already_pending(PYLON):
          nexus=self.units(NEXUS).ready
          if nexus.exists and self.can_afford(PYLON):
              await self.build(PYLON, near=self.MAIN_BASE)#was nexus.first

  async def build_assimilators(self):
      if self.can_afford(ASSIMILATOR) and self.units(ASSIMILATOR).amount+1<(self.time/30):
          for nexus in self.units(NEXUS).ready:
              geysers=self.state.vespene_geyser.closer_than(15.0, nexus)
              for geyser in geysers:
                  worker=self.select_build_worker(geyser.position)
                  if not worker is None:
                      if not self.units(ASSIMILATOR).closer_than(1.0, geyser).exists:
                          await self.do(worker.build(ASSIMILATOR, geyser))

  async def expand(self):
      if self.units(NEXUS).amount<(self.time/180) and self.can_afford(NEXUS):
          await self.expand_now()

  async def build_offense_buildings(self):
      if self.units(PYLON).ready.exists:
          pylon=self.units(PYLON).ready.random
          if self.units(GATEWAY).ready.exists:
              if not self.units(CYBERNETICSCORE):
                  if self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
                      await self.build(CYBERNETICSCORE, near=pylon)
              elif not self.units(FORGE):
                  if self.can_afford(FORGE) and not self.already_pending(FORGE):
                      await self.build(FORGE, near=pylon)
              elif self.units(GATEWAY).amount<(self.time/90):
                  if self.can_afford(GATEWAY) and not self.already_pending(GATEWAY):
                      await self.build(GATEWAY, near=pylon)
          else:
              if self.can_afford(GATEWAY) and not self.already_pending(GATEWAY):
                  await self.build(GATEWAY, near=pylon)

  async def upgrade(self):
      if self.units(FORGE).ready.exists and self.units(FORGE).ready.idle:
          forge=self.units(FORGE).ready.first
          if not self.already_pending_upgrade(UpgradeId.PROTOSSSHIELDSLEVEL1) and self.can_afford(UpgradeId.PROTOSSSHIELDSLEVEL1):
              await self.do(forge.research(UpgradeId.PROTOSSSHIELDSLEVEL1))
          elif not self.already_pending_upgrade(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1) and self.can_afford(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1):
              await self.do(forge.research(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1))
          elif not self.already_pending_upgrade(UpgradeId.PROTOSSGROUNDARMORSLEVEL1) and self.can_afford(UpgradeId.PROTOSSGROUNDARMORSLEVEL1):
              await self.do(forge.research(UpgradeId.PROTOSSGROUNDARMORSLEVEL1))
          elif not self.already_pending_upgrade(UpgradeId.PROTOSSSHIELDSLEVEL2) and self.can_afford(UpgradeId.PROTOSSSHIELDSLEVEL2):
              await self.do(forge.research(UpgradeId.PROTOSSSHIELDSLEVEL2))
          elif not self.already_pending_upgrade(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2) and self.can_afford(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2):
              await self.do(forge.research(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2))
          elif not self.already_pending_upgrade(UpgradeId.PROTOSSGROUNDARMORSLEVEL2) and self.can_afford(UpgradeId.PROTOSSGROUNDARMORSLEVEL2):
              await self.do(forge.research(UpgradeId.PROTOSSGROUNDARMORSLEVEL2))
          elif not self.already_pending_upgrade(UpgradeId.PROTOSSSHIELDSLEVEL3) and self.can_afford(UpgradeId.PROTOSSSHIELDSLEVEL3):
              await self.do(forge.research(UpgradeId.PROTOSSSHIELDSLEVEL3))
          elif not self.already_pending_upgrade(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3) and self.can_afford(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3):
              await self.do(forge.research(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3))
          elif not self.already_pending_upgrade(UpgradeId.PROTOSSGROUNDARMORSLEVEL3) and self.can_afford(UpgradeId.PROTOSSGROUNDARMORSLEVEL3):
              await self.do(forge.research(UpgradeId.PROTOSSGROUNDARMORSLEVEL3))

  async def build_offense_units(self):
      for gate in self.units(GATEWAY).ready.idle:
          if self.can_afford(STALKER) and self.supply_left>0:
              await self.do(gate.train(STALKER))

  async def defend(self):
      if self.units(STALKER).amount>3 and len(self.known_enemy_units)>0:
          target=random.choice(self.known_enemy_units)
          for u in self.units(STALKER).idle:
              await self.do(u.attack(target))

  def find_enemy(self, state):
      if len(self.known_enemy_units)>0:
          return random.choice(self.known_enemy_units)
      elif len(self.known_enemy_structures)>0:
          return random.choice(self.known_enemy_structures)
      else:
          return self.enemy_start_locations[0]

  async def attack(self):
      if self.units(STALKER).amount>5+(self.time/60):
          target=self.find_enemy(self.state)
          for u in self.units(STALKER).idle:
              await self.do(u.attack(target))

run_game(maps.get("Abyssal Reef LE"), [
    Bot(Race.Protoss, TestBot()),
    Computer(Race.Terran, Difficulty.Medium)
], realtime=True)
