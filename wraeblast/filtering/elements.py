import enum
import typing

import pydantic
import structlog
from pydantic import dataclasses

from wraeblast import types


logger = structlog.get_logger()


OneOrMoreActionArgsType = typing.Union[
    types.FilterActionArgsType,
    list[types.FilterActionArgsType],
]
OneOrMoreConditionValueType = typing.Union[
    types.FilterConditionValueType,
    list[types.FilterConditionValueType],
]


def _merge_rule_and_style_actions(
    rule: "Rule",
    style: "Style",
    replace: bool = False,
) -> "Rule":
    rule_action_types = rule.actions.keys()
    for style_action_type, style_action_args in style.actions.items():
        if style_action_type in rule_action_types:
            if not replace:
                continue
            else:
                del rule.actions[style_action_type]
        if not isinstance(style_action_args, list):
            style_action_args = [style_action_args]
        rule.actions[style_action_type] = Action(
            action_type=style_action_type,
            args=style_action_args,
        )
    return rule


class Visibility(enum.Enum):
    """An enum representing loot filter visibility states."""

    SHOW = "Show"
    HIDE = "Hide"
    CONTINUE = "Continue"


class ConditionType(enum.Enum):
    """An enum representing supported loot filter conditions."""

    ALTERNATEQUALITY = "AlternateQuality"
    ANYENCHANTMENT = "AnyEnchantment"
    AREALEVEL = "AreaLevel"
    BASETYPE = "BaseType"
    BLIGHTEDMAP = "BlightedMap"
    CLASS = "Class"
    CORRUPTED = "Corrupted"
    CORRUPTEDMODS = "CorruptedMods"
    DROPLEVEL = "DropLevel"
    ELDERITEM = "ElderItem"
    ELDERMAP = "ElderMap"
    ENCHANTMENTPASSIVENODE = "EnchantmentPassiveNode"
    ENCHANTMENTPASSIVENUM = "EnchantmentPassiveNum"
    FRACTUREDITEM = "FracturedItem"
    GEMLEVEL = "GemLevel"
    GEMQUALITYTYPE = "GemQualityType"
    HASENCHANTMENT = "HasEnchantment"
    HASEXPLICITMOD = "HasExplicitMod"
    HASINFLUENCE = "HasInfluence"
    HEIGHT = "Height"
    IDENTIFIED = "Identified"
    ITEMLEVEL = "ItemLevel"
    LINKEDSOCKETS = "LinkedSockets"
    MAPTIER = "MapTier"
    MIRRORED = "Mirrored"
    PROPHECY = "Prophecy"
    QUALITY = "Quality"
    RARITY = "Rarity"
    REPLICA = "Replica"
    SCOURGED = "Scourged"
    SHAPEDMAP = "ShapedMap"
    SHAPERITEM = "ShaperItem"
    SOCKETGROUP = "SocketGroup"
    SOCKETS = "Sockets"
    STACKSIZE = "StackSize"
    SYNTHESISEDITEM = "SynthesisedItem"
    UBERBLIGHTEDMAP = "UberBlightedMap"
    WIDTH = "Width"


class ActionType(enum.Enum):
    """An enum representing supported loot filter actions."""

    CUSTOMALERTSOUND = "CustomAlertSound"
    DISABLEDROPSOUND = "DisableDropSound"
    ENABLEDROPSOUND = "EnableDropSound"
    MINIMAPICON = "MinimapIcon"
    PLAYALERTSOUND = "PlayAlertSound"
    PLAYALERTSOUNDPOSITIONAL = "PlayAlertSoundPositional"
    PLAYEFFECT = "PlayEffect"
    SETBACKGROUNDCOLOR = "SetBackgroundColor"
    SETBORDERCOLOR = "SetBorderColor"
    SETFONTSIZE = "SetFontSize"
    SETTEXTCOLOR = "SetTextColor"


class NamedColor(enum.Enum):
    """An enum representing supported loot filter named colors."""

    BLUE = "Blue"
    BROWN = "Brown"
    CYAN = "Cyan"
    GREEN = "Green"
    GRAY = GREY = "Grey"
    ORANGE = "Orange"
    PINK = "Pink"
    PURPLE = "Purple"
    RED = "Red"
    WHITE = "White"
    YELLOW = "Yellow"


class Shape(enum.Enum):
    """An enum representing supported loot filter shapes."""

    CIRCLE = "Circle"
    CROSS = "Cross"
    DIAMOND = "Diamond"
    HEXAGON = "Hexagon"
    KITE = "Kite"
    MOON = "Moon"
    PENTAGON = "Pentagon"
    RAINDROP = "Raindrop"
    SQUARE = "Square"
    STAR = "Star"
    TRIANGLE = "Triangle"
    UPSIDEDOWNHOUSE = "UpsideDownHouse"


class Operator(enum.Enum):
    """An enum representing comparison operators."""

    LTE = "<="
    LT = "<"
    EQ = "="
    NE = "!"
    ID = "=="
    GT = ">"
    GTE = ">="


class Condition(pydantic.BaseModel):
    """A loot filter condition."""

    condition_type: ConditionType
    value: typing.Optional[types.FilterConditionValueType]
    op: typing.Optional[Operator] = Operator.EQ

    @classmethod
    def from_args(
        cls,
        condition_type: ConditionType,
        args: typing.Any,
    ) -> "Condition":
        if isinstance(args, dict):
            op, value = list(args.items())[0]
        else:
            op = Operator.EQ
            value = args
        return cls(condition_type=condition_type, op=op, value=value)


class Action(pydantic.BaseModel):
    """A loot filter action."""

    action_type: ActionType
    args: OneOrMoreActionArgsType = dataclasses.Field(default_factory=list)

    @pydantic.validator("args", pre=True, always=True)
    def set_args(
        cls,
        v: OneOrMoreActionArgsType,
    ) -> list[types.FilterActionArgsType]:
        if not isinstance(v, list):
            return [v]
        return v


ActionsMapType = dict[ActionType, Action]
ConditionsMapType = dict[ConditionType, Condition]


class Style(pydantic.BaseModel):
    """Represents a loot filter style.

    Styles contain **actions** and (optionally) **tags**.

    """

    actions: dict[ActionType, OneOrMoreActionArgsType]
    tags: list[typing.Union[list[str], str]] = dataclasses.Field(
        default_factory=list
    )

    class Config:
        arbitrary_types_allowed = True


class Rule(pydantic.BaseModel):
    """Represents a loot filter rule."""

    visibility: Visibility = Visibility.SHOW
    conditions: ConditionsMapType = dataclasses.Field(default_factory=dict)
    actions: ActionsMapType = dataclasses.Field(default_factory=dict)
    tags: set[str] = dataclasses.Field(default_factory=set)
    priority: typing.Optional[int] = None
    style: typing.Optional[typing.Union[list, str]] = None
    name: typing.Optional[str] = "anonymous"

    class Config:
        arbitrary_types_allowed = True

    def apply_style(self, style: Style, replace: bool = True) -> "Rule":
        """Apply the given style to the rule.

        If **replace** is ``False``, returns a copy of the ``Rule``. Otherwise,
        the current instance is mutated.

        """
        return _merge_rule_and_style_actions(self, style, replace=replace)

    @pydantic.validator("conditions", pre=True, always=True)
    def set_conditions(
        cls,
        v: dict[
            ConditionType, typing.Union[OneOrMoreConditionValueType, Condition]
        ],
    ) -> ConditionsMapType:
        conditions = {}
        for condition_type in list(v.keys()):
            condition = v[condition_type]
            if not isinstance(condition, Condition):
                conditions[condition_type] = Condition.from_args(
                    condition_type=condition_type,
                    args=condition,
                )
            else:
                conditions[condition_type] = condition
        return conditions

    @pydantic.validator("actions", pre=True, always=True)
    def set_actions(
        cls,
        v: dict[ActionType, typing.Union[OneOrMoreActionArgsType, Action]],
    ) -> ActionsMapType:
        actions = {}
        for action_type in list(v.keys()):
            action_or_args = v[action_type]
            if not isinstance(action_or_args, Action):
                actions[action_type] = Action(
                    action_type=action_type,
                    args=action_or_args,
                )
            else:
                actions[action_type] = action_or_args
        return actions


class PresetTags(pydantic.BaseModel):
    """Stores lists of tags that control rule visibility.

    * **visible**: a single tag or a list of tags that are forced to be
      shown in the rendered loot filter.
    * **hidden**: a single tag or a list of tags that are forced to be
      hidden in the rendered loot filter.

    """

    replace: dict[str, typing.Optional[str]] = dataclasses.Field(
        default_factory=dict
    )
    visible: list[typing.Union[str, list[str]]] = dataclasses.Field(
        default_factory=list
    )
    hidden: list[typing.Union[str, list[str]]] = dataclasses.Field(
        default_factory=list
    )


class Preset(pydantic.BaseModel):
    """Template-level configuration for a loot filter.

    Presets allow a single item filter template to be used to generate
    many complementary filters. Currently, presets only control
    visibility of rules based on tag names.

    """

    tags: PresetTags = dataclasses.Field(default_factory=PresetTags)


class ItemFilter(pydantic.BaseModel):
    """Represents a loot filter."""

    presets: dict[str, Preset] = dataclasses.Field(default_factory=dict)
    styles: dict[str, Style] = dataclasses.Field(default_factory=dict)
    rules: list[Rule] = dataclasses.Field(default_factory=list)

    def __init__(self, **data: dict[str, typing.Any]) -> None:
        super().__init__(**data)
        self.apply_default_preset()
        logger.debug("filter.processed", rules=len(self.rules))

    def apply_default_preset(self) -> None:
        """Apply the default preset to all rules in the filter."""
        if "default" in self.presets:
            self.apply_preset(preset_name="default")

    def apply_preset(self, preset_name: str = "default") -> None:
        """Apply the given preset to all rules in the filter."""
        preset = self.presets[preset_name]
        log = logger.bind(preset=preset_name)
        log.debug("preset.apply")
        for rule in self.rules:
            # Replace tags
            for source_tag, target_tag in preset.tags.replace.items():
                source_tags = set(
                    source_tag
                    if isinstance(source_tag, list)
                    else [source_tag]
                )
                if source_tags.issubset(rule.tags):
                    target_tags = set(
                        target_tag
                        if isinstance(target_tag, list)
                        else [target_tag]
                    )
                    rule.tags -= {t for t in source_tags if t is not None}
                    rule.tags |= {t for t in target_tags if t is not None}

            # Disable visibility for hidden tags
            for hidden_tag in preset.tags.hidden:
                hidden_tags = set(
                    hidden_tag
                    if isinstance(hidden_tag, list)
                    else [hidden_tag]
                )
                if hidden_tags.issubset(rule.tags):
                    rule.visibility = Visibility.HIDE

            # Enable visibility for visible tags
            for visible_tag in preset.tags.visible:
                visible_tags = set(
                    visible_tag
                    if isinstance(visible_tag, list)
                    else [visible_tag]
                )
                if visible_tags.issubset(rule.tags):
                    rule.visibility = Visibility.SHOW
        self.resolve_styles()

    def get_styles_for_tags(
        self,
        tags: typing.Iterable[typing.Union[list[str], str]],
    ) -> list[Style]:
        """Get a list of styles that match the given tags."""
        tags = set(tags)
        styles = []
        for _, style in self.styles.items():
            for style_tags in style.tags:
                if not isinstance(style_tags, list):
                    style_tags = [style_tags]
                if set(style_tags).issubset(tags):
                    styles.append(style)
        return styles

    def resolve_styles(
        self,
        ignore_errors: bool = False,
        apply_default: bool = True,
    ) -> None:
        """Apply all styles to applicable rules across the filter."""
        logger.debug("styles.apply")
        default_style = None
        if apply_default and "default" in self.styles:
            default_style = self.styles["default"]
        for rule in self.rules:
            # Apply a style named "default", if it exists
            if default_style is not None:
                rule.apply_style(default_style, replace=True)
            # First apply styles with matching tag names...
            styles = self.get_styles_for_tags(rule.tags)
            # ...then apply any explicit style names from the given rule
            if rule.style:
                if isinstance(rule.style, list):
                    style_names = rule.style
                else:
                    style_names = [rule.style]
                try:
                    for style_name in style_names:
                        styles.append(self.styles[style_name])
                except KeyError:
                    if not ignore_errors:
                        raise
            for style in styles:
                rule.apply_style(style, replace=True)

    def remove_hidden_rules(self) -> None:
        """Remove all hidden rules."""
        self.rules = [
            rule for rule in self.rules if rule.visibility == Visibility.SHOW
        ]
