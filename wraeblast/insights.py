import collections
import collections.abc
import datetime
import enum
import functools
import os
import typing

import aiohttp
import diskcache
import numpy as np
import pandas as pd
import pydantic
import structlog
import uplink

from wraeblast import constants, errors
from wraeblast.filtering.parsers.extended import env


logger = structlog.get_logger()


QcutItemsType = list[tuple[pd.Interval, pd.DataFrame]]
SingleInfluencedQcutItemsType = list[
    tuple[tuple[tuple[str, ...], pd.Interval], pd.DataFrame]
]
InsightsResultType = tuple[
    typing.Union["CurrencyType", "ItemType"],
    "EconomyOverview",
]
InsightsType = typing.Union["CurrencyType", "ItemType"]

quantiles = {
    "quartile": 4,
    "quintile": 5,
    "decile": 10,
    "percentile": 100,
}

_cache = diskcache.Cache(
    directory=os.getenv("WRAEBLAST_CACHE_DIR", "./.insights_cache")
)


def to_camel(string: str) -> str:
    first, *rest = string.split("_")
    return first + "".join(word.capitalize() for word in rest)


def raise_for_status(response):
    """Checks whether or not the response was successful."""
    if 200 <= response.status_code < 300:
        return response

    raise errors.UnsuccessfulInsightsRequest(
        f"error {response.status_code}: {response.url}"
    )


def get_all_insights_types() -> list[InsightsType]:
    return [*CurrencyType, *ItemType]


def get_insights_type_by_value(s: str) -> InsightsType:
    for t in get_all_insights_types():
        if t.value == s:
            return t
    raise KeyError(s)


def get_quantile_tuple(q: str) -> tuple[str, int]:
    if q.startswith("D"):
        return ("decile", int(q[1:]))
    elif q.startswith("P"):
        return ("percentile", int(q[1:]))
    elif q.startswith("QU"):
        return ("quintile", int(q[2:]))
    elif q.startswith("Q"):
        return ("quartile", int(q[1:]))
    else:
        raise RuntimeError(f"invalid quantile: {q}")


def group_items_by_quantile(
    df: pd.DataFrame,
    groups: list[str],
    query: str = None,
    thresholds: "config.ThresholdOptions" = None,
) -> list[tuple[typing.Any, ...]]:
    """Group an item overview dataframe by chaos value quantiles."""
    if thresholds is not None:
        if query:
            query += " and "
        query += thresholds.get_dataframe_query()
    df_filtered = df.query(query) if query else df
    gb = df_filtered.groupby(groups)
    return list(gb)


def group_items_by_influence_and_quantile(
    df: pd.DataFrame,
    max_influences: int = 1,
    thresholds: "config.ThresholdOptions" = None,
) -> SingleInfluencedQcutItemsType:
    """Group an item overview dataframe by value quantile and influence."""
    return group_items_by_quantile(
        df=df,
        query=f"influences.str.len() <= {max_influences}",
        thresholds=thresholds,
    )  # type: ignore


async def get_economy_overview(
    league: str,
    client: "PoENinja",
    type_: InsightsType,
) -> "EconomyOverview":
    """Request an economy overview from poe.ninja."""
    if type_ in CurrencyType:
        meth = client.get_currency_overview
    elif type_ in ItemType:
        meth = client.get_item_overview
    else:
        raise RuntimeError()
    logger.info(
        "overview.get",
        client=".".join([client.__module__, client.__class__.__name__]),
        type=type_.value,
    )
    return await meth(league=league, type=type_.value)  # type: ignore


async def get_overviews(
    league: str,
    types: list[InsightsType],
) -> typing.AsyncGenerator[InsightsResultType, None]:
    """Request all economy overviews from poe.ninja."""
    logger.info("all_insights.get", league=league)
    session = aiohttp.ClientSession()
    client = uplink.AiohttpClient(session=session)
    ninja = PoENinja(
        base_url=PoENinja.default_base_url,
        client=client,
    )
    for t in types:
        overview = await get_economy_overview(
            league=league,
            client=ninja,
            type_=t,
        )
        yield (t, overview)
    await session.close()


async def initialize_insights_cache(
    league: str,
    cache: typing.Optional[diskcache.Cache] = None,
    cache_expire: int = 60 * 60,
) -> diskcache.Cache:
    """Fetch and cache economy insights as needed."""
    if cache is None:
        cache = _cache
    # log = logger.bind(league=league, cache_dir=cache.directory)
    log = logger.bind(league=league)
    log.info("cache.initialize", league=league, dir=cache.directory)
    stale_types = []
    for t in get_all_insights_types():
        overview = cache.get(f"insights:{t.value}")
        if overview is None:
            log.debug("cache.miss", type=t.value)
            stale_types.append(t)
        else:
            log.debug("cache.hit", type=t.value)
    async for t, overview in get_overviews(
        league=league,
        types=stale_types,
    ):
        log.info(
            "overview.response",
            lines=len(overview.lines),
            type=t.value,
        )
        cache.add(
            key=f"insights:{t.value}",
            value=overview.dict(by_alias=True),
            expire=cache_expire,
        )
    return cache


async def initialize_filter_context(
    initialize_cache: bool = True,
    league: typing.Optional[str] = None,
    cache: typing.Optional[diskcache.Cache] = None,
    cache_expire: int = 60 * 60,
) -> "ItemFilterContext":
    """Create an ``ItemFilterContext`` from cached economy data."""
    if initialize_cache:
        if league is None:
            raise RuntimeError("league must be provided if initializing cache")
        cache = await initialize_insights_cache(
            league=league,
            cache=cache,
            cache_expire=cache_expire,
        )
    elif cache is None:
        cache = _cache
    else:
        raise RuntimeError("cache not provided")
    ctx = {}
    for t in get_all_insights_types():
        overview = cache.get(f"insights:{t.value}")
        ctx[ItemFilterContext.ctx_name_for_insights_type(t)] = overview
    return ItemFilterContext(**ctx)


def discretize(
    models: list[pydantic.BaseModel],
    key: typing.Callable[[pydantic.BaseModel], float],
    bins: list[float],
    ignore_out_of_bounds: bool = True,
) -> dict[float, list[pydantic.BaseModel]]:
    arr = np.asarray([key(m) for m in models])
    d = collections.defaultdict(list)
    for i, bin_i in enumerate(np.digitize(arr, bins)):
        try:
            d[bins[bin_i]].append(models[i])
        except IndexError:
            if not ignore_out_of_bounds:
                raise
            d[bins[-1]].append(models[i])
    return d


@uplink.retry(
    when=uplink.retry.when.status(503) | uplink.retry.when.raises(Exception),
    stop=uplink.retry.stop.after_attempt(5)
    | uplink.retry.stop.after_delay(10),
    backoff=uplink.retry.backoff.jittered(multiplier=0.5),
)
@uplink.returns.json
@uplink.json
@uplink.get
def get_json():
    """Template for GET requests with JSON as both request and response."""


class CurrencyType(enum.Enum):
    CURRENCY = "Currency"
    FRAGMENT = "Fragment"


class ItemType(enum.Enum):
    ARTIFACT = "Artifact"
    BASE_TYPE = "BaseType"
    BEAST = "Beast"
    BLIGHTED_MAP = "BlightedMap"
    CLUSTER_JEWEL = "ClusterJewel"
    DELIRIUM_ORB = "DeliriumOrb"
    DIVINATION_CARD = "DivinationCard"
    ESSENCE = "Essence"
    FOSSIL = "Fossil"
    HELMET_ENCHANT = "HelmetEnchant"
    INCUBATOR = "Incubator"
    INVITATION = "Invitation"
    MAP = "Map"
    OIL = "Oil"
    PROPHECY = "Prophecy"
    RESONATOR = "Resonator"
    SCARAB = "Scarab"
    SKILL_GEM = "SkillGem"
    UNIQUE_ACCESSORY = "UniqueAccessory"
    UNIQUE_ARMOUR = "UniqueArmour"
    UNIQUE_FLASK = "UniqueFlask"
    UNIQUE_JEWEL = "UniqueJewel"
    UNIQUE_MAP = "UniqueMap"
    UNIQUE_WEAPON = "UniqueWeapon"
    VIAL = "Vial"
    WATCHSTONE = "Watchstone"


class BidAsk(pydantic.BaseModel):
    id: int
    league_id: int
    pay_currency_id: int
    get_currency_id: int
    sample_time_utc: datetime.datetime
    count: int
    value: float
    data_point_count: int
    includes_secondary: int
    listing_count: int


class Modifier(pydantic.BaseModel):
    text: str
    optional: bool


class BaseLine(pydantic.BaseModel):
    chaos_value: float = 0


class CurrencyLine(BaseLine):
    currency_type_name: str
    chaos_equivalent: float
    details_id: str
    # chaos_value: float = 0
    pay: typing.Optional[BidAsk]
    receive: typing.Optional[BidAsk]

    @pydantic.root_validator
    def set_chaos_value(cls, values) -> None:
        values["chaos_value"] = values["chaos_equivalent"]
        return values

    @property
    def name(self) -> str:
        return self.currency_type_name

    class Config:
        alias_generator = to_camel


def _parse_name_and_details_id(
    name: str, details_id: str
) -> tuple[typing.Optional[int], tuple[constants.Influence, ...]]:
    tokens = details_id.split("-")
    ilvl_and_influences = tokens[name.count(" ") + name.count("-") + 1 :]
    try:
        return (
            int(ilvl_and_influences[0]),
            tuple(
                constants.Influence(i.capitalize())
                for i in ilvl_and_influences[1:]
            ),
        )
    except (IndexError, ValueError):
        return (None, tuple())


class TradeInfo(pydantic.BaseModel):
    mod: str
    min: int
    max: int


class ItemLine(BaseLine):
    id: str
    name: str
    item_class: int
    implicit_modifiers: list[Modifier]
    explicit_modifiers: list[Modifier]
    exalted_value: float
    count: int
    details_id: str

    base_type: typing.Optional[str]
    flavour_text: typing.Optional[str]
    gem_quality: typing.Optional[int]
    gem_level: typing.Optional[int]
    icon: typing.Optional[str]
    influences: typing.Optional[tuple[constants.Influence, ...]]
    item_level: typing.Optional[int]
    level_required: typing.Optional[int]
    links: typing.Optional[int]
    listing_count: typing.Optional[int]
    map_tier: typing.Optional[int]
    stack_size: typing.Optional[int]
    trade_info: typing.Optional[list[TradeInfo]] = pydantic.Field(
        default_factory=list
    )
    variant: typing.Optional[str]

    class Config:
        alias_generator = to_camel
        use_enum_values = True

    def __init__(self, **data) -> None:
        super().__init__(**data)
        if self.item_class == 2:
            self.item_level, self.influences = _parse_name_and_details_id(
                self.name, self.details_id
            )

    @property
    def cluster_jewel_enchantment(self) -> str:
        try:
            return constants.cluster_jewel_names_to_passives[self.name].value
        except KeyError:
            return ""

    @property
    def cluster_jewel_passives(self) -> int:
        if self.trade_info:
            for ti in self.trade_info:
                if ti.mod == "enchant.stat_3086156145":
                    return ti.min
        return 0

    @property
    def alt_quality(self) -> typing.Optional[str]:
        for alt_quality in constants.AltQuality:
            if self.name.startswith(alt_quality.value):
                return alt_quality.value
        return None

    @property
    def is_alt_quality_skill_gem(self) -> bool:
        return self.skill_gem_name != self.name

    @property
    def skill_gem_name(self) -> str:
        for alt_quality in constants.AltQuality:
            if self.name.startswith(alt_quality.value):
                return self.name[len(alt_quality.value) + 1 :]
        return self.name


class CurrencyDetail(pydantic.BaseModel):
    id: int
    icon: str
    name: str
    trade_id: typing.Optional[str] = None

    class Config:
        alias_generator = to_camel


def build_economy_overview_dataframe(
    *args,
    chaos_value_bins: int = 10,
    chaos_value_labels: typing.Optional[typing.Union[list[str], bool]] = None,
) -> pd.DataFrame:
    df = pd.DataFrame(*args)
    # if "variant" in df:
    #     df.drop(
    #         index=df[df.variant.isin(("Pre 2.0", "Pre 2.4"))].index,  # type: ignore
    #         inplace=True,
    #     )
    for name_key in ("currency_type_name", "skill_gem_name"):
        if name_key in df:
            df["name"] = df[name_key]

    # Allow dot-notation access to item names, since name is reserved
    df["item_name"] = df["name"]

    # Normalized chaos values
    # XXX: since log(0) is -inf, the min chaos value of the dataframe replaces
    # rows with a chaos value of 0
    min_chaos_value = df.loc[df["chaos_value"] != 0, "chaos_value"].min()
    df["chaos_value"].replace(0, min_chaos_value, inplace=True)  # type: ignore
    df["chaos_value_norm"] = np.log(df["chaos_value"])
    # min_norm = df.loc[
    #     df["chaos_value_norm"] != -np.inf, "chaos_value_norm"
    # ].min()
    # df["chaos_value_norm"].replace(
    #     -np.inf,
    #     min_norm,  # type: ignore
    #     inplace=True,
    # )
    # XXX: massage incorrect/out-of-date poe.ninja data to avoid skewing
    # ...but keep the original dataframe intact for posterity

    # Custom quantiles
    df["value_bin"] = pd.cut(
        df["chaos_value_norm"],
        bins=chaos_value_bins,
        duplicates="drop",
        labels=chaos_value_labels,
    )
    df["value_quantile"] = pd.qcut(
        df["chaos_value"],
        q=chaos_value_bins,
        duplicates="drop",
        labels=chaos_value_labels,
    )

    # Pre-defined quantiles (quartiles, quintiles, percentiles)
    for key, q in quantiles.items():
        labels = None
        if isinstance(q, (list, tuple)):
            q, labels = q
        df[key] = pd.qcut(
            df.rank(method="first", numeric_only=True)["chaos_value"],
            q=q,
            labels=False if labels is None else None,
            precision=0,
            duplicates="drop",
        )
        df[key] += 1
        if labels is not None:
            df[key] = df[key].map(dict(enumerate(labels)))
    return df


class EconomyOverview(pydantic.BaseModel, collections.abc.Iterator):
    lines: typing.List[BaseLine]
    chaos_value_bins: int = 10
    chaos_value_labels: typing.Optional[typing.Union[list[str], bool]]
    _dataframe: pd.DataFrame = pydantic.PrivateAttr()
    _dataframe_rows_it: typing.Iterator[
        tuple[typing.Any, ...]
    ] = pydantic.PrivateAttr()
    _quantile_thresholds: list[dict[str, float]] = pydantic.PrivateAttr(
        default_factory=list
    )

    class Config:
        alias_generator = to_camel

    @property
    def df(self) -> pd.DataFrame:
        return self._dataframe

    @pydantic.root_validator
    def set_chaos_value_labels(
        cls, values: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        labels = values["chaos_value_labels"]
        bins = values["chaos_value_bins"]
        if isinstance(labels, list) and len(labels) == 0:
            values["chaos_value_labels"] = None
        return values

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self._dataframe = build_economy_overview_dataframe(
            [line.dict() for line in self.lines],
            chaos_value_bins=self.chaos_value_bins,
            chaos_value_labels=self.chaos_value_labels,
        )
        self._dataframe_rows_it = self._dataframe.iterrows().__iter__()

    def max_chaos_value(self) -> float:
        return self._dataframe.value_quantile.max().right

    def get_quantiles_for_threshold(
        self, min_chaos_value: float
    ) -> typing.Optional[dict[str, float]]:
        for threshold in self.quantile_thresholds():
            if threshold["chaos_value"] >= min_chaos_value:
                return threshold
        return self.quantile_thresholds()[-1]

    def quantile_thresholds(self) -> list[dict[str, float]]:
        if self._quantile_thresholds:
            return self._quantile_thresholds
        groups = self.df.groupby(list(quantiles.keys()), as_index=False)
        self._quantile_thresholds = groups.agg(  # type: ignore
            {"chaos_value": "min"}
        ).to_dict("records")
        return self._quantile_thresholds

    def __iter__(self):
        return self._dataframe_rows_it

    def __next__(self):
        return self._dataframe_rows_it.__next__()


class CurrencyOverview(EconomyOverview):
    lines: typing.List[CurrencyLine]
    currency_details: typing.List[CurrencyDetail]

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self.lines.sort(key=lambda line: line.chaos_value, reverse=True)

    def details_by_id(self) -> dict[int, CurrencyDetail]:
        return {cd.id: cd for cd in self.currency_details}

    def dict_by_name(self) -> dict[str, typing.Any]:
        return {line.currency_type_name: line for line in self.lines}

    def get_human_readable_value(
        self,
        chaos_value: float,
        round_down_by: int = 1,
        precision: int = 0,
    ) -> str:
        ex_price = self.exalted_price()
        if chaos_value < ex_price:
            if round_down_by:
                chaos_value = env.round_down(chaos_value, round_down_by)
            return f"{chaos_value}c"
        else:
            return f"{chaos_value / ex_price:.{precision}f}ex"

    def get_orb_for_shard_name(self, shard_name: str) -> pd.Series:
        shard_names_to_orb_names = {
            "Transmutation Shard": "Orb of Transmutation",
            "Alteration Shard": "Orb of Alteration",
            "Alchemy Shard": "Orb of Alteration",
            "Annulment Shard": "Orb of Annulment",
            "Binding Shard": "Orb of Binding",
            "Horizon Shard": "Orb of Horizons",
            "Harbinger's Shard": "Harbinger's Orb",
            "Engineer's Shard": "Engineer's Orb",
            "Ancient Shard": "Ancient Orb",
            "Chaos Shard": "Chaos Orb",
            "Mirror Shard": "Mirror of Kalandra",
            "Exalted Shard": "Exalted Orb",
            "Regal Shard": "Regal Orb",
        }
        orb_name = shard_names_to_orb_names[shard_name]
        return self.df[self.df.item_name == orb_name].iloc[0]  # type: ignore

    def exalted_price(self) -> float:
        for line in self.lines:
            if line.name == "Exalted Orb":
                return line.chaos_value
        return -1

    def __getitem__(self, key) -> CurrencyLine:
        for line in self.lines:
            if line.name == key:
                return line
        raise KeyError(key)


class ItemOverview(EconomyOverview):
    lines: typing.List[ItemLine]

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self.lines.sort(key=lambda line: line.chaos_value, reverse=True)

    def dict_by_name(self) -> dict[str, typing.Any]:
        return {line.name: line for line in self.lines}

    # def grouped_by_quantile(
    #     self,
    #     groups: list[str],
    #     query: str = "",
    # ) -> QcutItemsType:
    #     return group_items_by_quantile(
    #         self._dataframe,
    #         groups=groups,
    #         query=query,
    #     )

    # def grouped_by_single_influence_quantile(
    #     self,
    #     min_chaos_value: typing.Optional[float] = None,
    # ) -> SingleInfluencedQcutItemsType:
    #     return group_items_by_influence_and_quantile(
    #         self._dataframe,
    #         max_influences=1,
    #         filter_value_min=min_chaos_value,
    #     )


class ItemFilterContext(pydantic.BaseModel):
    """Entrypoint for accessing economy data from poe.ninja."""

    artifacts: ItemOverview
    base_types: ItemOverview
    beasts: ItemOverview
    blighted_maps: ItemOverview
    cluster_jewels: ItemOverview
    currency: CurrencyOverview
    delirium_orbs: ItemOverview
    divination_cards: ItemOverview
    essences: ItemOverview
    fossils: ItemOverview
    fragments: CurrencyOverview
    helmet_enchants: ItemOverview
    incubators: ItemOverview
    invitations: ItemOverview
    maps: ItemOverview
    oils: ItemOverview
    prophecies: ItemOverview
    resonators: ItemOverview
    scarabs: ItemOverview
    skill_gems: ItemOverview
    unique_accessories: ItemOverview
    unique_armours: ItemOverview
    unique_flasks: ItemOverview
    unique_jewels: ItemOverview
    unique_maps: ItemOverview
    unique_weapons: ItemOverview
    vials: ItemOverview
    watchstones: ItemOverview

    @classmethod
    def ctx_name_for_insights_type(cls, insights_type: InsightsType) -> str:
        return {
            CurrencyType.CURRENCY: "currency",
            CurrencyType.FRAGMENT: "fragments",
            ItemType.ARTIFACT: "artifacts",
            ItemType.BASE_TYPE: "base_types",
            ItemType.BEAST: "beasts",
            ItemType.BLIGHTED_MAP: "blighted_maps",
            ItemType.CLUSTER_JEWEL: "cluster_jewels",
            ItemType.DELIRIUM_ORB: "delirium_orbs",
            ItemType.DIVINATION_CARD: "divination_cards",
            ItemType.ESSENCE: "essences",
            ItemType.FOSSIL: "fossils",
            ItemType.HELMET_ENCHANT: "helmet_enchants",
            ItemType.INCUBATOR: "incubators",
            ItemType.INVITATION: "invitations",
            ItemType.MAP: "maps",
            ItemType.OIL: "oils",
            ItemType.PROPHECY: "prophecies",
            ItemType.RESONATOR: "resonators",
            ItemType.SCARAB: "scarabs",
            ItemType.SKILL_GEM: "skill_gems",
            ItemType.UNIQUE_ACCESSORY: "unique_accessories",
            ItemType.UNIQUE_ARMOUR: "unique_armours",
            ItemType.UNIQUE_FLASK: "unique_flasks",
            ItemType.UNIQUE_JEWEL: "unique_jewels",
            ItemType.UNIQUE_MAP: "unique_maps",
            ItemType.UNIQUE_WEAPON: "unique_weapons",
            ItemType.VIAL: "vials",
            ItemType.WATCHSTONE: "watchstones",
        }[insights_type]

    def dict_by_name(self) -> dict[str, dict[str, typing.Any]]:
        d = {}
        for key, overview in self.__dict__.items():
            if key.startswith("_"):
                continue
            if isinstance(overview, (CurrencyOverview, ItemOverview)):
                d[key] = overview.dict_by_name()
        return d


class PoEOfficial(uplink.Consumer):
    default_base_url = "https://api.pathofexile.com/"

    @uplink.response_handler(raise_for_status)
    @get_json("league")  # type: ignore
    def get_leagues(self):
        """List leagues."""


class PoENinja(uplink.Consumer):
    default_base_url = "https://poe.ninja/api/data/"

    @uplink.response_handler(raise_for_status)
    @uplink.ratelimit(calls=2, period=150)
    @get_json("CurrencyOverview")  # type: ignore
    def get_currency_overview(
        self,
        league: uplink.Query(type=str),  # type: ignore
        type: uplink.Query(type=CurrencyType),  # type: ignore
    ) -> CurrencyOverview:
        ...

    @uplink.response_handler(raise_for_status)
    @uplink.ratelimit(calls=30, period=150)
    @get_json("ItemOverview")  # type: ignore
    def get_item_overview(
        self,
        league: uplink.Query(type=str),  # type: ignore
        type: uplink.Query(type=ItemType),  # type: ignore
    ) -> ItemOverview:
        ...
