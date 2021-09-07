import enum
import typing

from wraeblast import constants


FilterConditionValueType = typing.Union[
    bool,
    int,
    str,
    list[str],
    enum.Enum,
    constants.SocketGroup,
]
FilterActionArgsType = typing.Union[
    int,
    str,
    tuple,
    enum.Enum,
]
AnyFilterValueType = typing.Union[
    FilterActionArgsType,
    FilterConditionValueType,
    None,
]
