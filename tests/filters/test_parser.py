import asyncio
import collections
import json

import pytest

from wraeblast import insights
from wraeblast.filtering import elements
from wraeblast.filtering.parsers import extended, standard
from wraeblast.filtering.parsers.extended import config
from wraeblast.filtering.serializers.standard import dumps


@pytest.fixture
def current_league() -> str:
    # TODO: API call
    return open(".current_league").read().strip()


@pytest.fixture
def filter_context(current_league: str) -> insights.ItemFilterContext:
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(
        insights.initialize_filter_context(league=current_league),
    )


@pytest.fixture
def neversink_uberstrict() -> elements.ItemFilter:
    with open("./tests/filters/Neversink_5_UBERSTRICT.filter") as f:
        return standard.loads(f.read())


@pytest.fixture
def filter_options(
    filter_context: insights.ItemFilterContext,
) -> config.ItemFilterPrerenderOptions:
    with open("./filters/trade/trade-QU4-agGrnYl_r.config.json") as f:
        return config.ItemFilterPrerenderOptions.with_defaults(
            ctx=filter_context,
            overrides=json.load(f),
        )


@pytest.fixture
def extended_filter(
    filter_context: insights.ItemFilterContext,
    filter_options: config.ItemFilterPrerenderOptions,
) -> elements.ItemFilter:
    with open("./filters/trade/trade.yaml.j2") as f:
        return extended.loads(
            f.read(), ctx=filter_context, options=filter_options
        )


def test_loads_standard_filter(neversink_uberstrict):
    assert len(neversink_uberstrict.rules) == 434
    # assert len(neversink_uberstrict.styles) == 0

    # action_hashes = collections.defaultdict(int)

    # for rule in neversink_uberstrict.rules:
    #     action_hash = ""
    #     for action in rule.actions:
    #         if action.action_type is elements.ActionType.SETFONTSIZE:
    #             action_hash += f"{action.args[0]}:"
    #         elif action.action_type in (
    #             elements.ActionType.SETTEXTCOLOR,
    #             elements.ActionType.SETBORDERCOLOR,
    #             elements.ActionType.SETBACKGROUNDCOLOR,
    #         ):
    #             action_hash += f'{",".join([str(i) for i in action.args[0]])}:'
    #         # else:
    #         #     print(action.action_type)
    #     action_hashes[action_hash] += 1
    # for action_hash, count in action_hashes.items():
    #     if count > 1:
    #         print((action_hash, count))
    # assert False


def test_dumps_standard_filter(neversink_uberstrict):
    s = dumps(neversink_uberstrict)
    assert len(s.split("\n")) == 4638


@pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
@pytest.mark.filterwarnings("ignore:.*was never awaited.*:RuntimeWarning")
def test_loads_extended_filter(extended_filter: elements.ItemFilter):
    assert len(extended_filter.rules)


def test_dumps_extended_filter(extended_filter):
    s = dumps(extended_filter)
    ...
