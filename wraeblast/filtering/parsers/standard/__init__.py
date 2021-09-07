import enum
import typing

import lark

from wraeblast.filtering import elements
from wraeblast.filtering.parsers.standard import transformers


_LARK_PARSER = lark.Lark.open_from_package(
    __name__,
    "poe_filter_grammar.lark",
    start="start",
    parser="lalr",
)


def loads(s: typing.Union[str, bytes]) -> elements.ItemFilter:
    tree = _LARK_PARSER.parse(str(s))
    transformer = transformers.FilterTransformer()
    transformer.transform(tree)
    if transformer.filter_obj is None:
        raise RuntimeError("failed to parse item filter")
    return transformer.filter_obj
