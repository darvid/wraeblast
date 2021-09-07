"""Extended filter parsing."""
import math
import typing

import glom
import jinja2
import jinja2.filters
import jinja2.sandbox
import ruamel.yaml


if typing.TYPE_CHECKING:
    from wraeblast import insights

from wraeblast.filtering import colors, elements
from wraeblast.filtering.parsers.extended import config, env


@jinja2.filters.environmentfilter
def glom_query(
    environment: jinja2.Environment,
    value: typing.Any,
    spec: str,
    default: typing.Any,
) -> typing.Any:
    return glom.glom(value, spec, default=default)


def iter_stacks(
    start: int,
    end: int,
    op: elements.Operator = elements.Operator.ID,
    end_op: elements.Operator = elements.Operator.GTE,
) -> list[tuple[str, int]]:
    return [
        (op.value if i < end else end_op.value, i)
        for i in range(start, end + 1)
    ]


jinja2.filters.FILTERS["q"] = glom_query


def update_template_globals(
    ctx: "insights.ItemFilterContext",
    globals: typing.Optional[dict[str, typing.Any]] = None,
    options: typing.Optional[config.ItemFilterPrerenderOptions] = None,
) -> dict[str, typing.Any]:
    if globals is None:
        globals = {}
    if options is None:
        options = config.ItemFilterPrerenderOptions.with_defaults(ctx=ctx)
    globals.update(
        {
            "change_brightness": env.change_brightness,
            "colormap_pick": env.colormap_pick,
            "colormap": colors.linear_colormap_from_color_list,
            "ctx": ctx,
            "e": math.e,
            "get_item_tags": env.get_item_tags,
            "get_quantile_threshold_tags": env.get_quantile_threshold_tags,
            "get_stack_tags": env.get_stack_tags,
            "iter_stacks": iter_stacks,
            "nearest_named_color": env.nearest_named_color,
            "normalize_skill_gem_name": env.normalize_skill_gem_name,
            "options": options,
            "round_down": env.round_down,
            "text_color": env.text_color,
            "tts": env.tts,
        },
    )
    return globals


def loads(
    s: typing.Union[str, bytes],
    ctx: "insights.ItemFilterContext",
    globals: typing.Optional[dict[str, typing.Any]] = None,
    options: typing.Optional[config.ItemFilterPrerenderOptions] = None,
    pre_rendered: bool = False,
) -> elements.ItemFilter:
    """Load a Jinja2 + YAML formatted extended filter from a string."""
    if not pre_rendered:
        rendered_template = render(
            s=s,
            ctx=ctx,
            globals=globals,
            options=options,
        )
    else:
        rendered_template = s
    yaml = ruamel.yaml.YAML(typ="safe")
    document = yaml.load(rendered_template)
    item_filter = elements.ItemFilter(**document)
    return item_filter


def render(
    s: typing.Union[str, bytes],
    ctx: "insights.ItemFilterContext",
    globals: typing.Optional[dict[str, typing.Any]] = None,
    options: typing.Optional[config.ItemFilterPrerenderOptions] = None,
) -> str:
    """Render a Jinja2 + YAML filter template to YAML."""
    globals = update_template_globals(
        ctx=ctx,
        globals=globals,
        options=options,
    )
    jinja_env = jinja2.sandbox.SandboxedEnvironment()
    template = jinja_env.from_string(str(s), globals=globals)
    return template.render()
