import enum
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
    CHAOS_DOT_MULTIPLIER = "Chaos Damage over Time Multiplier"
    CHAOS_RESISTANCE = "Chaos Resistance"
    COLD_DAMAGE = "Cold Damage"
    COLD_DOT_MULTIPLIER = "Cold Damage over Time Multiplier"
    COLD_RESISTANCE = "Cold Resistance"
    CRITICAL_CHANCE = "Critical Chance"
    CURSE_EFFECT = "Curse Effect"
    DAGGER_AND_CLAW_DAMAGE = "Dagger and Claw Damage"
    DOT_MULTIPLIER = "Damage over Time Multiplier"
    HERALD_DAMAGE = "Damage while you have a Herald"
    TWO_HAND_DAMAGE = "Damage with Two Handed Melee Weapons"
    DEXTERITY = "Dexterity"
    AILMENT_EFFECT = "Effect of Non-Damaging Ailments"
    ELEMENTAL_DAMAGE = "Elemental Damage"
    ENERGY_SHIELD = "Energy Shield"
    EVASION = "Evasion"
    EXERTED_ATTACK_DAMAGE = "Exerted Attack Damage"
    FIRE_DAMAGE = "Fire Damage"
    FIRE_DOT_MULTIPLIER = "Fire Damage over Time Multiplier"
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
    PHYSICAL_DOT_MULTIPLIER = "Physical Damage over Time Multiplier"
    PROJECTILE_DAMAGE = "Projectile Damage"
    SPELL_DAMAGE = "Spell Damage"
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
    ClusterJewelMinorPassive.AREA_DAMAGE: "10% increased Area Damage",
    ClusterJewelMinorPassive.ARMOUR: "15% increased Armour",
    ClusterJewelMinorPassive.ATTACK_DAMAGE: "10% increased Attack Damage",
    ClusterJewelMinorPassive.ATTACK_DAMAGE_WHILE_DUAL_WIELDING: (
        "12% increased Attack Damage while Dual Wielding"
    ),
    ClusterJewelMinorPassive.ATTACK_DAMAGE_WHILE_SHIELDING: (
        "12% increased Attack Damage while holding a Shield"
    ),
    ClusterJewelMinorPassive.AURA_EFFECT: (
        "6% increased effect of Non-Curse Auras from your Skills"
    ),
    ClusterJewelMinorPassive.AXE_AND_SWORD_DAMAGE: (
        "Axe Attacks deal 12% increased Damage with Hits and Ailments, "
        "Sword Attacks deal 12% increased Damage with Hits and Ailments"
    ),
    ClusterJewelMinorPassive.BOW_DAMAGE: (
        "12% increased Damage with Bows, "
        "12% increased Damage Over Time with Bow Skills"
    ),
    ClusterJewelMinorPassive.BRAND_DAMAGE: "12% increased Brand Damage",
    ClusterJewelMinorPassive.CHANCE_TO_BLOCK_ATTACK_DAMAGE: (
        "1% Chance to Block Attack Damage"
    ),
    ClusterJewelMinorPassive.CHANCE_TO_BLOCK_SPELL_DAMAGE: (
        "1% Chance to Block Spell Damage"
    ),
    ClusterJewelMinorPassive.CHANCE_TO_DODGE_ATTACKS: (
        "1% chance to Dodge Attack Hits"
    ),
    ClusterJewelMinorPassive.CHANNELLING_SKILL_DAMAGE: (
        "Channelling Skills deal 12% increased Damage"
    ),
    ClusterJewelMinorPassive.CHAOS_DAMAGE: "12% increased Chaos Damage",
    ClusterJewelMinorPassive.CHAOS_DOT_MULTIPLIER: (
        "+4% to Chaos Damage over Time Multiplier"
    ),
    ClusterJewelMinorPassive.CHAOS_RESISTANCE: "+12% to Chaos Resistance",
    ClusterJewelMinorPassive.COLD_DAMAGE: "12% increased Cold Damage",
    ClusterJewelMinorPassive.COLD_DOT_MULTIPLIER: (
        "+4% to Cold Damage over Time Multiplier"
    ),
    ClusterJewelMinorPassive.COLD_RESISTANCE: "+15% to Cold Resistance",
    ClusterJewelMinorPassive.CRITICAL_CHANCE: (
        "15% increased Critical Strike Chance"
    ),
    ClusterJewelMinorPassive.CURSE_EFFECT: (
        "5% increased Effect of your Curses"
    ),
    ClusterJewelMinorPassive.DAGGER_AND_CLAW_DAMAGE: (
        "Claw Attacks deal 12% increased Damage with Hits and Ailments, "
        "Dagger Attacks deal 12% increased Damage with Hits and Ailments"
    ),
    ClusterJewelMinorPassive.DOT_MULTIPLIER: (
        "+4% to Damage over Time Multiplier"
    ),
    ClusterJewelMinorPassive.HERALD_DAMAGE: (
        "10% increased Damage while affected by a Herald"
    ),
    ClusterJewelMinorPassive.TWO_HAND_DAMAGE: (
        "12% increased Damage with Two Handed Weapons"
    ),
    ClusterJewelMinorPassive.DEXTERITY: "+10 to Dexterity",
    ClusterJewelMinorPassive.AILMENT_EFFECT: (
        "10% increased Effect of Non-Damaging Ailments"
    ),
    ClusterJewelMinorPassive.ELEMENTAL_DAMAGE: (
        "10% increased Elemental Damage"
    ),
    ClusterJewelMinorPassive.ENERGY_SHIELD: (
        "6% increased maximum Energy Shield"
    ),
    ClusterJewelMinorPassive.EVASION: "15% increased Evasion Rating",
    ClusterJewelMinorPassive.EXERTED_ATTACK_DAMAGE: (
        "Exerted Attacks deal 20% increased Damage"
    ),
    ClusterJewelMinorPassive.FIRE_DAMAGE: "12% increased Fire Damage",
    ClusterJewelMinorPassive.FIRE_DOT_MULTIPLIER: (
        "+4% to Fire Damage over Time Multiplier"
    ),
    ClusterJewelMinorPassive.FIRE_RESISTANCE: "+15% to Fire Resistance",
    ClusterJewelMinorPassive.FLASK_DURATION: (
        "6% increased Flask Effect Duration"
    ),
    ClusterJewelMinorPassive.INTELLIGENCE: "+10 to Intelligence",
    ClusterJewelMinorPassive.LIFE: "4% increased maximum Life",
    ClusterJewelMinorPassive.FLASK_RECOVERY: (
        "10% increased Life Recovery from Flasks, "
        "10% increased Mana Recovery from Flasks"
    ),
    ClusterJewelMinorPassive.LIGHTNING_DAMAGE: "12% increased Lightning Damage",
    ClusterJewelMinorPassive.LIGHTNING_RESISTANCE: "+15% to Lightning Resistance",
    ClusterJewelMinorPassive.MACE_STAFF_DAMAGE: (
        "Staff Attacks deal 12% increased Damage with Hits and Ailments, "
        "Mace or Sceptre Attacks deal 12% increased Damage with Hits "
        "and Ailments"
    ),
    ClusterJewelMinorPassive.MANA: "6% increased maximum Mana",
    ClusterJewelMinorPassive.MINION_DAMAGE: (
        "Minions deal 10% increased Damage"
    ),
    ClusterJewelMinorPassive.MINION_HERALD_DAMAGE: (
        "Minions deal 10% increased Damage while you are "
        "affected by a Herald"
    ),
    ClusterJewelMinorPassive.MINION_LIFE: (
        "Minions have 12% increased maximum Life"
    ),
    ClusterJewelMinorPassive.PHYSICAL_DAMAGE: "12% increased Physical Damage",
    ClusterJewelMinorPassive.PHYSICAL_DOT_MULTIPLIER: (
        "+4% to Physical Damage over Time Multiplier"
    ),
    ClusterJewelMinorPassive.PROJECTILE_DAMAGE: (
        "10% increased Projectile Damage"
    ),
    ClusterJewelMinorPassive.SPELL_DAMAGE: "10% increased Spell Damage",
    ClusterJewelMinorPassive.STRENGTH: "+10 to Strength",
    ClusterJewelMinorPassive.TOTEM_DAMAGE: "12% increased Totem Damage",
    ClusterJewelMinorPassive.TRAP_AND_MINE_DAMAGE: (
        "12% increased Trap Damage, 12% increased Mine Damage"
    ),
    ClusterJewelMinorPassive.WAND_DAMAGE: (
        "Wand Attacks deal 12% increased Damage with Hits and Ailments"
    ),
}
cluster_jewel_names_to_passives = {
    v: k for k, v in cluster_jewel_passives_to_names.items()
}


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
