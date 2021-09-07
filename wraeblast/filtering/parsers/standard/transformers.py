import typing

import lark
import lark.visitors

from wraeblast import constants
from wraeblast.filtering import colors, elements


def _override_tree_children(tree: lark.Tree, obj: typing.Any) -> typing.Any:
    tree.children = [obj]
    return obj


@lark.v_args(tree=True)
class FilterTransformer(lark.visitors.Transformer_InPlace):
    def __init__(self) -> None:
        super().__init__()
        self.filter_obj: typing.Optional[elements.ItemFilter] = None

    def rule(self, tree: lark.Tree) -> elements.Rule:
        rule: typing.Optional[elements.Rule] = None
        for child in tree.children:
            if isinstance(child, elements.Visibility):
                rule = elements.Rule(visibility=child)
            elif isinstance(child, elements.Condition):
                rule.conditions[child.condition_type] = child
            elif isinstance(child, elements.Action):
                rule.actions[child.action_type] = child
        if rule is None:
            raise lark.visitors.Discard
        return _override_tree_children(tree=tree, obj=rule)

    def condition(self, tree: lark.Tree) -> lark.Tree:
        condition_type: typing.Optional[elements.ConditionType] = None
        operator: typing.Optional[elements.Operator] = None
        value: typing.Optional[typing.Union[str, int, list[str]]] = None
        for child in tree.children:
            if isinstance(child, lark.Token):
                if child.type.startswith("COND_"):
                    condition_type = elements.ConditionType(child.value)
                else:
                    raise RuntimeError(f"unexpected token {child.type}")
            elif isinstance(child, elements.Operator):
                operator = child
            else:
                if isinstance(child, str):
                    value = str(child)
                elif isinstance(child, int) and not isinstance(child, bool):
                    value = int(child)
                else:
                    value = child  # type: ignore
        if condition_type is None:
            raise lark.visitors.Discard
        return _override_tree_children(
            tree=tree,
            obj=elements.Condition(
                condition_type=condition_type,
                value=value,
                op=operator,
            ),
        )

    def action(self, tree: lark.Tree) -> elements.Action:
        action_type = elements.ActionType(str(tree.children[0]))
        args = tree.children[1:]
        action = elements.Action(action_type=action_type, args=args)
        return _override_tree_children(
            tree=tree,
            obj=action,
        )

    def named_color(self, tree: lark.Tree) -> elements.NamedColor:
        return _override_tree_children(
            tree=tree,
            obj=elements.NamedColor(str(tree.children[0])),
        )

    def influence(self, tree: lark.Tree) -> constants.Influence:
        return _override_tree_children(
            tree=tree,
            obj=constants.Influence(str(tree.children[0])),
        )

    def rarity(self, tree: lark.Tree) -> str:
        return _override_tree_children(tree=tree, obj=str(tree.children[0]))

    def shape(self, tree: lark.Tree) -> elements.Shape:
        return _override_tree_children(
            tree=tree,
            obj=elements.Shape(str(tree.children[0])),
        )

    def socket_group(self, tree: lark.Tree) -> str:
        return _override_tree_children(
            tree=tree,
            obj=constants.SocketGroup.from_string(
                "".join([str(c) for c in tree.children])
            ),
        )

    def multi_string(self, tree: lark.Tree) -> list[str]:
        return _override_tree_children(
            tree=tree, obj=[str(c).strip('"') for c in tree.children]
        )

    def op(self, tree: lark.Tree) -> elements.Operator:
        symbol = str(tree.children[0])
        if symbol == "<":
            op = elements.Operator.LT
        elif symbol == "<=":
            op = elements.Operator.LTE
        elif symbol == "=":
            op = elements.Operator.EQ
        elif symbol == ">":
            op = elements.Operator.GT
        elif symbol == ">=":
            op = elements.Operator.GTE
        elif symbol == "==":
            op = elements.Operator.ID
        else:
            raise lark.visitors.Discard
        return _override_tree_children(tree=tree, obj=op)

    def start(self, tree: lark.Tree) -> elements.ItemFilter:
        self.filter_obj = elements.ItemFilter(rules=tree.children)  # type: ignore
        self.children = [self.filter_obj]
        return self.filter_obj

    def true(self, tree: lark.Tree) -> bool:
        return _override_tree_children(tree=tree, obj=True)

    def false(self, tree: lark.Tree) -> bool:
        return _override_tree_children(tree=tree, obj=False)

    def NEWLINE(self, token: lark.Token) -> lark.Token:
        raise lark.visitors.Discard

    def NUMBER(self, token: lark.Token) -> int:
        token.value = int(token.value)
        return token.value

    def RGBA(self, token: lark.Token) -> colors.Color:
        rgba = tuple(int(i) for i in token.value.split(" "))
        token.value = colors.Color.from_rgba_bytes(colors.ColorType_RGBA(rgba))
        return token.value

    def STRING(self, token: lark.Token) -> str:
        token.value = token.value[1:-1]
        return token.value

    def VISIBILITY(self, token: lark.Token) -> elements.Visibility:
        token.value = elements.Visibility[str(token).upper()]
        return token.value
