import enum
import re
import typing

import pydantic
import pydantic.dataclasses


class AltQuality(enum.Enum):
    ANOMALOUS = "Anomalous"
    DIVERGENT = "Divergent"
    PHANTASMAL = "Phantasmal"


class ClusterJewelMinorPassive(enum.Enum):
    AREA_DAMAGE = "Area Damage"
    ARMOUR = "Armour"
    ATTACK_DAMAGE = "Attack Damage"
    ATTACK_DAMAGE_WHILE_DUAL_WIELDING = "Attack Damage while Dual Wielding"
    ATTACK_DAMAGE_WHILE_SHIELDING = "Attack Damage while holding a Shield"
    AURA_EFFECT = "Aura Effect"
    AXE_AND_SWORD_DAMAGE = "Axe and Sword Damage"
    BOW_DAMAGE = "Bow Damage"
    BRAND_DAMAGE = "Brand Damage"
    CHANCE_TO_BLOCK_ATTACK_DAMAGE = "Chance to Block Attack Damage"
    CHANCE_TO_BLOCK_SPELL_DAMAGE = "Chance to Block Spell Damage"
    CHANCE_TO_DODGE_ATTACKS = "Chance to Dodge Attacks"
    CHANNELLING_SKILL_DAMAGE = "Channelling Skill Damage"
    CHAOS_DAMAGE = "Chaos Damage"
    CHAOS_DOT = "Chaos Damage over Time"
    CHAOS_RESISTANCE = "Chaos Resistance"
    COLD_DAMAGE = "Cold Damage"
    COLD_DOT = "Cold Damage over Time"
    COLD_RESISTANCE = "Cold Resistance"
    CRITICAL_CHANCE = "Critical Chance"
    CURSE_EFFECT = "Curse Effect"
    DAGGER_AND_CLAW_DAMAGE = "Dagger and Claw Damage"
    DOT = "Damage over Time"
    HERALD_DAMAGE = "Damage while you have a Herald"
    TWO_HAND_DAMAGE = "Damage with Two Handed Melee Weapons"
    DEXTERITY = "Dexterity"
    AILMENT_EFFECT = "Effect of Non-Damaging Ailments"
    ELEMENTAL_DAMAGE = "Elemental Damage"
    ENERGY_SHIELD = "Energy Shield"
    EVASION = "Evasion"
    EXERTED_ATTACK_DAMAGE = "Exerted Attack Damage"
    FIRE_DAMAGE = "Fire Damage"
    FIRE_DOT = "Fire Damage over Time"
    FIRE_RESISTANCE = "Fire Resistance"
    FLASK_DURATION = "Flask Duration"
    INTELLIGENCE = "Intelligence"
    LIFE = "Life"
    FLASK_RECOVERY = "Life and Mana recovery from Flasks"
    LIGHTNING_DAMAGE = "Lightning Damage"
    LIGHTNING_RESISTANCE = "Lightning Resistance"
    MACE_STAFF_DAMAGE = "Mace and Staff Damage"
    MANA = "Mana"
    MINION_DAMAGE = "Minion Damage"
    MINION_HERALD_DAMAGE = "Minion Damage while you have a Herald"
    MINION_LIFE = "Minion Life"
    PHYSICAL_DAMAGE = "Physical Damage"
    PHYSICAL_DOT = "Physical Damage over Time"
    PROJECTILE_DAMAGE = "Projectile Damage"
    SPELL_DAMAGE = "Spell Damage"
    SPELL_SUPPRESSION = "Chance to Suppress Spell Damage"
    STRENGTH = "Strength"
    TOTEM_DAMAGE = "Totem Damage"
    TRAP_AND_MINE_DAMAGE = "Trap and Mine Damage"
    WAND_DAMAGE = "Wand Damage"


class FilterFormat(enum.Enum):
    STANDARD = enum.auto()
    EXTENDED = enum.auto()


class Influence(enum.Enum):
    SHAPER = "Shaper"
    ELDER = "Elder"
    CRUSADER = "Crusader"
    HUNTER = "Hunter"
    REDEEMER = "Redeemer"
    WARLORD = "Warlord"
    NONE = "None"


class SocketColor(enum.Enum):
    RED = "R"
    GREEN = "G"
    BLUE = "B"
    DELVE = "D"
    ABYSS = "A"
    WHITE = "W"


SocketGroupList = list[tuple[SocketColor, int]]

cluster_jewel_passives_to_names = {
    ClusterJewelMinorPassive.AREA_DAMAGE: r"\d+% increased Area Damage",
    ClusterJewelMinorPassive.ARMOUR: r"\d+% increased Armour",
    ClusterJewelMinorPassive.ATTACK_DAMAGE: r"\d+% increased Attack Damage",
    ClusterJewelMinorPassive.ATTACK_DAMAGE_WHILE_DUAL_WIELDING: (
        r"\d+% increased Attack Damage while Dual Wielding"
    ),
    ClusterJewelMinorPassive.ATTACK_DAMAGE_WHILE_SHIELDING: (
        r"\d+% increased Attack Damage while holding a Shield"
    ),
    ClusterJewelMinorPassive.AURA_EFFECT: (
        r"\d+% increased Mana Reservation Efficiency of Skills"
    ),
    ClusterJewelMinorPassive.AXE_AND_SWORD_DAMAGE: (
        r"Axe Attacks deal \d+% increased Damage with Hits and Ailments, "
        r"Sword Attacks deal \d+% increased Damage with Hits and Ailments"
    ),
    ClusterJewelMinorPassive.BOW_DAMAGE: (
        r"\d+% increased Damage with Bows, "
        r"\d+% increased Damage Over Time with Bow Skills"
    ),
    ClusterJewelMinorPassive.BRAND_DAMAGE: r"\d+% increased Brand Damage",
    ClusterJewelMinorPassive.CHANCE_TO_BLOCK_ATTACK_DAMAGE: (
        r"\+?\d+% Chance to Block Attack Damage"
    ),
    ClusterJewelMinorPassive.CHANCE_TO_BLOCK_SPELL_DAMAGE: (
        r"\d+% Chance to Block Spell Damage"
    ),
    ClusterJewelMinorPassive.CHANCE_TO_DODGE_ATTACKS: (
        r"\d+% chance to Dodge Attack Hits"
    ),
    ClusterJewelMinorPassive.CHANNELLING_SKILL_DAMAGE: (
        r"Channelling Skills deal \d+% increased Damage"
    ),
    ClusterJewelMinorPassive.CHAOS_DAMAGE: r"\d+% increased Chaos Damage",
    ClusterJewelMinorPassive.CHAOS_DOT: (r"\+\d+% to Chaos Damage over Time"),
    ClusterJewelMinorPassive.CHAOS_RESISTANCE: r"\+\d+% to Chaos Resistance",
    ClusterJewelMinorPassive.COLD_DAMAGE: r"\d+% increased Cold Damage",
    ClusterJewelMinorPassive.COLD_DOT: (r"\+\d+% to Cold Damage over Time"),
    ClusterJewelMinorPassive.COLD_RESISTANCE: r"\+\d+% to Cold Resistance",
    ClusterJewelMinorPassive.CRITICAL_CHANCE: (
        r"\d+% increased Critical Strike Chance"
    ),
    ClusterJewelMinorPassive.CURSE_EFFECT: (
        r"\d+% increased Effect of your Curses"
    ),
    ClusterJewelMinorPassive.DAGGER_AND_CLAW_DAMAGE: (
        r"Claw Attacks deal \d+% increased Damage with Hits and Ailments, "
        r"Dagger Attacks deal \d+% increased Damage with Hits and Ailments"
    ),
    ClusterJewelMinorPassive.DOT: r"\d+% increased Damage over Time",
    ClusterJewelMinorPassive.HERALD_DAMAGE: (
        r"\d+% increased Damage while affected by a Herald"
    ),
    ClusterJewelMinorPassive.TWO_HAND_DAMAGE: (
        r"\d+% increased Damage with Two Handed Weapons"
    ),
    ClusterJewelMinorPassive.DEXTERITY: r"\+\d+ to Dexterity",
    ClusterJewelMinorPassive.AILMENT_EFFECT: (
        r"\d+% increased Effect of Non-Damaging Ailments"
    ),
    ClusterJewelMinorPassive.ELEMENTAL_DAMAGE: (
        r"\d+% increased Elemental Damage"
    ),
    ClusterJewelMinorPassive.ENERGY_SHIELD: (
        r"\d+% increased maximum Energy Shield"
    ),
    ClusterJewelMinorPassive.EVASION: r"\d+% increased Evasion Rating",
    ClusterJewelMinorPassive.EXERTED_ATTACK_DAMAGE: (
        r"Exerted Attacks deal 20% increased Damage"
    ),
    ClusterJewelMinorPassive.FIRE_DAMAGE: r"\d+% increased Fire Damage",
    ClusterJewelMinorPassive.FIRE_DOT: (
        r"(\+\d+% to Fire Damage over Time" r"|\d+% increased Burning Damage)"
    ),
    ClusterJewelMinorPassive.FIRE_RESISTANCE: r"\+\d+% to Fire Resistance",
    ClusterJewelMinorPassive.FLASK_DURATION: (
        r"\d+% increased Flask Effect Duration"
    ),
    ClusterJewelMinorPassive.INTELLIGENCE: r"\+\d+ to Intelligence",
    ClusterJewelMinorPassive.LIFE: r"\d+% increased maximum Life",
    ClusterJewelMinorPassive.FLASK_RECOVERY: (
        r"\d+% increased Life Recovery from Flasks, "
        r"\d+% increased Mana Recovery from Flasks"
    ),
    ClusterJewelMinorPassive.LIGHTNING_DAMAGE: r"\d+% increased Lightning Damage",
    ClusterJewelMinorPassive.LIGHTNING_RESISTANCE: r"\+\d+% to Lightning Resistance",
    ClusterJewelMinorPassive.MACE_STAFF_DAMAGE: (
        r"Staff Attacks deal \d+% increased Damage with Hits and Ailments, "
        r"Mace or Sceptre Attacks deal \d+% increased Damage with Hits "
        r"and Ailments"
    ),
    ClusterJewelMinorPassive.MANA: r"\d+% increased maximum Mana",
    ClusterJewelMinorPassive.MINION_DAMAGE: (
        r"Minions deal \d+% increased Damage"
    ),
    ClusterJewelMinorPassive.MINION_HERALD_DAMAGE: (
        r"Minions deal \d+% increased Damage while you are "
        r"affected by a Herald"
    ),
    ClusterJewelMinorPassive.MINION_LIFE: (
        r"Minions have \d+% increased maximum Life"
    ),
    ClusterJewelMinorPassive.PHYSICAL_DAMAGE: r"\d+% increased Physical Damage",
    ClusterJewelMinorPassive.PHYSICAL_DOT: (
        r"\+\d+% to Physical Damage over Time"
    ),
    ClusterJewelMinorPassive.PROJECTILE_DAMAGE: (
        r"\d+% increased Projectile Damage"
    ),
    ClusterJewelMinorPassive.SPELL_DAMAGE: r"\d+% increased Spell Damage",
    ClusterJewelMinorPassive.SPELL_SUPPRESSION: (
        r"\+\d+% chance to Suppress Spell Damage"
    ),
    ClusterJewelMinorPassive.STRENGTH: r"\+\d+ to Strength",
    ClusterJewelMinorPassive.TOTEM_DAMAGE: r"\d+% increased Totem Damage",
    ClusterJewelMinorPassive.TRAP_AND_MINE_DAMAGE: (
        r"\d+% increased Trap Damage, \d+% increased Mine Damage"
    ),
    ClusterJewelMinorPassive.WAND_DAMAGE: (
        r"Wand Attacks deal \d+% increased Damage with Hits and Ailments"
    ),
}
cluster_jewel_names_to_passives = {
    v: k for k, v in cluster_jewel_passives_to_names.items()
}


def get_cluster_jewel_passive(name: str) -> ClusterJewelMinorPassive:
    for passive, pattern in cluster_jewel_passives_to_names.items():
        if re.match(pattern, name):
            return passive
    raise KeyError(name)


class SocketGroup(pydantic.BaseModel):
    sockets: SocketGroupList
    links: typing.Optional[int] = None

    @pydantic.validator("sockets", pre=True, always=True)
    def set_sockets(cls, v: SocketGroupList) -> SocketGroupList:
        total_count = 0
        for _, count in v:
            assert count <= 6, "socket count cannot be greater than six"
            total_count += count
        assert (
            total_count <= 6
        ), "total socket count cannot be greater than six"
        return v

    @classmethod
    def from_string(cls, s: str) -> "SocketGroup":
        sockets = {c: 0 for c in SocketColor}
        links: typing.Optional[int] = None
        if ord(s[0]) in range(ord("0"), ord("7")):
            links = int(s[0])
            s = s[1:]
        for char in s:
            sockets[SocketColor(char.upper())] += 1
        return SocketGroup(sockets=list(sockets.items()), links=links)

    def __str__(self) -> str:
        s = ""
        if self.links:
            s += str(self.links)
        for color, count in self.sockets:
            s += color.value * count
        return s
