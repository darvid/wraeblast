import enum

from wraeblast import types
from wraeblast.filtering import colors, elements


use_default_opacity = True


def serialize_value(v: types.AnyFilterValueType, quoted: bool = True) -> str:
    if isinstance(v, str):
        return f'"{v}"' if quoted else v
    elif isinstance(v, enum.Enum):
        return v.value
    elif isinstance(v, (list, tuple)):
        return " ".join([serialize_value(v_, quoted=quoted) for v_ in v])
    elif v is None:
        return "None"
    return str(v)


def serialize_action(action: elements.Action) -> str:
    s = action.action_type.value
    args = action.args
    if action.action_type in (
        elements.ActionType.DISABLEDROPSOUND,
        elements.ActionType.ENABLEDROPSOUND,
    ):
        return s
    if not isinstance(args, list):
        args = [args]
    for arg in args:
        s += " "
        if action.action_type in (
            elements.ActionType.SETBACKGROUNDCOLOR,
            elements.ActionType.SETBORDERCOLOR,
            elements.ActionType.SETTEXTCOLOR,
        ):
            if isinstance(arg, (list, tuple)):
                if len(arg) == 1:
                    arg = str(arg[0])
                    color = colors.Color(arg)
                elif len(arg) in (3, 4):
                    rgb = tuple(c / 255 for c in arg)
                    if rgb[3] == 1:
                        rgb = rgb[:3]
                    color = colors.Color(rgb)  # type: ignore
                else:
                    raise ValueError("color values must be RGB(A)")
                rgb = color.rgba_as_bytes
            elif isinstance(arg, (str, colors.Color)):
                color = colors.Color(arg)
                rgb = color.rgba_as_bytes
            else:
                raise ValueError("invalid color type")
            s += serialize_value(
                rgb[:3] if rgb[3] == 1 and use_default_opacity else rgb
            )
        elif isinstance(arg, tuple):
            quoted = action.action_type not in (
                elements.ActionType.MINIMAPICON,
                elements.ActionType.PLAYEFFECT,
            )
            s += " ".join([serialize_value(a, quoted=quoted) for a in arg])
        elif isinstance(arg, enum.Enum):
            s += arg.value
        elif isinstance(arg, (int, str, list)) or arg is None:
            s += serialize_value(arg)
        else:
            raise RuntimeError("invalid action args type")
    return s


def serialize_condition(condition: elements.Condition) -> str:
    s = condition.condition_type.value
    if condition.op and condition.op != elements.Operator.EQ:
        s += f" {condition.op.value}"
    value = condition.value
    if (
        condition.condition_type
        in (
            elements.ConditionType.AREALEVEL,
            elements.ConditionType.GEMLEVEL,
            elements.ConditionType.ITEMLEVEL,
            elements.ConditionType.MAPTIER,
            elements.ConditionType.STACKSIZE,
        )
        and condition.value is True
    ):
        value = 1
    s += f" {serialize_value(value)}"
    return s


def serialize_rule(
    rule: elements.Rule,
    indent: int = 4,
    soft_tabs: bool = True,
) -> str:
    s = rule.visibility.name.capitalize()
    s += "\n"
    i = " " * indent if indent and soft_tabs else "\t"
    for _, condition in rule.conditions.items():
        s += i + serialize_condition(condition)
        s += "\n"
    for _, action in rule.actions.items():
        s += i + serialize_action(action)
        s += "\n"
    return s


def dumps(
    item_filter: elements.ItemFilter,
    indent: int = 4,
    soft_tabs: bool = True,
) -> str:
    s = ""
    for rule in item_filter.rules:
        s += serialize_rule(rule, indent=indent, soft_tabs=soft_tabs)
        s += "\n"
    return s
