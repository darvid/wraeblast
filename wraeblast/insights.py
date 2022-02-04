import collections.abc
import enum
import os
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    AsyncGenerator,
    Optional,
    Union,
)

import aiohttp
import inflection
import numpy as np
import pandas as pd
import pydantic
import structlog
import uplink
import uplink.converters
from pandera.decorators import check_io, check_output
from pandera.errors import SchemaError
from pandera.model import SchemaModel
from pandera.model_components import Field
from pandera.typing import Series, String

from wraeblast import constants, errors
from wraeblast.filtering.elements import ItemFilter
from wraeblast.filtering.parsers.extended import env


if TYPE_CHECKING:
    import uplink.commands

    from wraeblast.filtering.parsers.extended import config


logger = structlog.get_logger()


QcutItemsType = list[tuple[pd.Interval, pd.DataFrame]]
SingleInfluencedQcutItemsType = list[
    tuple[tuple[tuple[str, ...], pd.Interval], pd.DataFrame]
]
InsightsResultType = tuple[
    Union["CurrencyType", "ItemType"],
    pd.DataFrame,
]
InsightsType = Union["CurrencyType", "ItemType"]

quantiles = {
    "quartile": 4,
    "quintile": 5,
    "decile": 10,
    "percentile": 100,
}
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


def _create_hdfstore(path: Optional[str] = None) -> pd.HDFStore:
    if not path:
        path = os.getenv("WRAEBLAST_CACHE", "./.wbinsights.h5")
    return pd.HDFStore(path)


class InflectedEnumMixin(enum.Enum):
    @property
    def underscored_value(self) -> str:
        return inflection.underscore(self.value)

    @property
    def pluralized_underscored_value(self) -> str:
        return inflection.pluralize(self.underscored_value)


class CurrencyType(InflectedEnumMixin, enum.Enum):
    CURRENCY = "Currency"
    FRAGMENT = "Fragment"


class ItemType(InflectedEnumMixin, enum.Enum):
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

    @property
    def key_name(self) -> str:
        return inflection.pluralize(inflection.underscore(self.value))


@uplink.response_handler
def raise_for_status(response):
    """Checks whether or not the response was successful."""
    if 200 <= response.status_code < 300:
        return response

    raise errors.UnsuccessfulInsightsRequest(
        f"error {response.status_code}: {response.url}"
    )


def get_all_insights_types() -> list[InsightsType]:
    return [*CurrencyType, *ItemType]


def get_display_value(
    chaos_value: float,
    exalted_exchange_value: int,
    round_down_by: int = 1,
    precision: int = 0,
) -> str:
    if chaos_value < exalted_exchange_value:
        if round_down_by:
            chaos_value = env.round_down(chaos_value, round_down_by)
        return f"{chaos_value}c"
    else:
        return f"{chaos_value / exalted_exchange_value:.{precision}f}ex"


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


async def get_economy_overview(
    league: str,
    client: "NinjaConsumer",
    type_: InsightsType,
) -> pd.DataFrame:
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


async def get_dataframes(
    league: str,
    types: list[InsightsType],
) -> AsyncGenerator[InsightsResultType, None]:
    """Request all economy overviews from poe.ninja."""
    logger.info("all_insights.get", league=league)
    session = aiohttp.ClientSession()
    client = uplink.AiohttpClient(session=session)
    ninja = NinjaConsumer(
        base_url=NinjaConsumer.default_base_url,
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
    store: Optional[pd.HDFStore] = None,
    no_sync: bool = False,
) -> pd.HDFStore:
    """Fetch and cache economy insights as needed."""
    if store is None:
        store = _create_hdfstore()
    log = logger.bind(league=league)
    log.info("cache.initialize", league=league)
    missing_dataframes = []
    for t in get_all_insights_types():
        try:
            df = store.get(f"i_{t.value}")
            log.debug("cache.hit", type=t.value)
        except KeyError:
            log.debug("cache.miss", type=t.value)
            missing_dataframes.append(t)
    if missing_dataframes and no_sync:
        raise errors.WraeblastError("insights cache is incomplete")
    async for t, df in get_dataframes(
        league=league,
        types=missing_dataframes,
    ):
        log.info(
            "overview.response",
            lines=df.shape[0],
            type=t.value,
        )
        store.put(f"i_{t.value}", df, format="table")
    return store


async def initialize_filter_context(
    initialize_cache: bool = True,
    league: Optional[str] = None,
    store: Optional[pd.HDFStore] = None,
    no_sync: bool = False,
) -> "ItemFilterContext":
    """Create an ``ItemFilterContext`` from cached economy data."""
    if initialize_cache:
        if league is None:
            raise RuntimeError("league must be provided if initializing cache")
        if store is None:
            store = _create_hdfstore()
        cache = await initialize_insights_cache(
            league=league,
            store=store,
            no_sync=no_sync,
        )
    else:
        raise RuntimeError("cache not provided")
    economy_data = {}
    for t in get_all_insights_types():
        overview = cache.get(f"i_{t.value}")
        economy_data[t.pluralized_underscored_value] = overview
    return ItemFilterContext(data=economy_data)


def _parse_name_and_details_id(
    name: str, details_id: str
) -> tuple[Optional[int], tuple[constants.Influence, ...]]:
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


def get_quantile_thresholds(df: pd.DataFrame) -> list[dict[str, float]]:
    groups = df.groupby(list(quantiles.keys()), as_index=False)
    return groups.agg({"chaos_value": "min"}).to_dict(  # type: ignore
        "records"
    )


class NinjaCurrencyOverviewSchema(SchemaModel):
    currency_type_name: Series[String]
    chaos_equivalent: Series[float]
    details_id: Series[String]
    pay_id: Series[float] = Field(alias="pay.id", nullable=True)
    pay_league_id: Series[float] = Field(alias="pay.league_id", nullable=True)
    pay_pay_currency_id: Series[float] = Field(
        alias="pay.pay_currency_id", nullable=True
    )
    pay_get_currency_id: Series[float] = Field(
        alias="pay.get_currency_id", nullable=True
    )
    pay_sample_time_utc: Series[
        Annotated[pd.DatetimeTZDtype, "ns", "utc"]
    ] = Field(alias="pay.sample_time_utc", coerce=True, nullable=True)
    pay_count: Series[float] = Field(alias="pay.count", nullable=True)
    pay_value: Series[float] = Field(alias="pay.value", nullable=True)
    pay_data_point_count: Series[float] = Field(
        alias="pay.data_point_count", ge=0, coerce=True, nullable=True
    )
    pay_includes_secondary: Series[bool] = Field(
        alias="pay.includes_secondary", coerce=True, nullable=True
    )
    pay_listing_count: Series[float] = Field(
        alias="pay.listing_count", coerce=True, nullable=True
    )


class NinjaItemOverviewSchema(SchemaModel):
    id: Series[int]
    name: Series[String]
    item_class: Series[int]
    flavour_text: Optional[Series[String]]
    chaos_value: Series[float]
    exalted_value: Series[float]
    count: Series[int]
    details_id: Series[String]
    # listing_count: Series[int]
    icon: Optional[Series[String]] = Field(nullable=True)
    base_type: Optional[Series[String]] = Field(nullable=True)
    gem_level: Optional[Series[float]] = Field(nullable=True)
    gem_quality: Optional[Series[float]] = Field(nullable=True)
    item_level: Optional[Series[float]] = Field(nullable=True)
    level_required: Optional[Series[float]] = Field(nullable=True)
    links: Optional[Series[float]] = Field(nullable=True)
    map_tier: Optional[Series[float]] = Field(nullable=True)
    stack_size: Optional[Series[float]] = Field(nullable=True)
    variant: Optional[Series[String]] = Field(nullable=True)

    class Config:
        coerce = True


class ExtendedNinjaOverviewSchema(SchemaModel):
    item_name: Series[String]
    chaos_value: Series[float]
    alt_quality: Series[String]
    is_alt_quality: Series[bool]
    chaos_value: Series[float]
    chaos_value_log: Series[float]
    quartile: Series[int]
    quintile: Series[int]
    decile: Series[int]
    percentile: Series[int]
    base_type: Optional[Series[String]] = Field(nullable=True)
    gem_level: Optional[Series[float]] = Field(nullable=True)
    gem_quality: Optional[Series[float]] = Field(nullable=True)
    influences: Optional[Series[String]] = Field(nullable=True)
    level_required: Optional[Series[float]] = Field(nullable=True)
    links: Optional[Series[float]] = Field(nullable=True)
    map_tier: Optional[Series[float]] = Field(nullable=True)
    num_influences: Optional[Series[int]] = Field(nullable=True)
    orb_name: Optional[Series[String]] = Field(nullable=True)
    stack_size: Optional[Series[float]] = Field(nullable=True)
    uber_blight: Optional[Series[bool]] = Field(nullable=True)
    variant: Optional[Series[String]] = Field(nullable=True)


class PostProcessedNinjaOverviewSchema(ExtendedNinjaOverviewSchema):
    exalted_value: Series[float]
    display_value: Series[String]


@check_output(ExtendedNinjaOverviewSchema)
def transform_ninja_df(df: pd.DataFrame) -> pd.DataFrame:
    currency_overview_schema = NinjaCurrencyOverviewSchema.to_schema()
    item_overview_schema = NinjaItemOverviewSchema.to_schema()
    is_currency_overview = False

    df = df.fillna(0)

    try:
        df = currency_overview_schema.validate(df)
        is_currency_overview = True
    except SchemaError as e:
        df = item_overview_schema.validate(df)

    if is_currency_overview:
        try:
            shards = []
            for shard_name, orb_name in shard_names_to_orb_names.items():
                if not df[df["currency_type_name"] == shard_name].empty:
                    continue
                orb_value = (
                    df[df["currency_type_name"] == orb_name][
                        "chaos_equivalent"
                    ].iloc[0]
                    if orb_name != "Chaos Orb"
                    else 1
                )
                shards.append(
                    {
                        "currency_type_name": shard_name,
                        "chaos_equivalent": orb_value / 20,
                    }
                )
            df = df.append(
                shards,
                verify_integrity=True,
                sort=True,
                ignore_index=True,
            )
        except IndexError:
            pass

    if "sparkline.data" in df.columns:
        df = df.loc[df["sparkline.data"].str.len() != 0]

    output = pd.DataFrame()
    output["item_name"] = (
        df["currency_type_name"]
        if "currency_type_name" in df.columns
        else df["name"]
    )
    if not is_currency_overview:
        output["scourged"] = output["item_name"].map(
            lambda name: name.startswith("Scourged")
        )
    for label in ("currency_type_name", "skill_gem_name"):
        if label in df.columns:
            output["item_name"] = df[label]

    if "map_tier" in df.columns:
        output["uber_blight"] = df["name"].map(
            lambda name: name.startswith("Blight-ravaged")
        )

    if (
        "base_type" in df.columns
        and not df[
            df["base_type"].str.contains("Cluster Jewel", na=False)
        ].empty
    ):
        try:
            output["cluster_jewel_enchantment"] = df["name"].map(
                lambda name: constants.get_cluster_jewel_passive(name).value
            )
            output["cluster_jewel_passives_min"] = df["trade_info"].apply(
                lambda trade_info: [
                    ti
                    for ti in trade_info
                    if ti["mod"] == "enchant.stat_3086156145"
                ][0]["min"]
            )
            output["cluster_jewel_passives_max"] = df["trade_info"].apply(
                lambda trade_info: [
                    ti
                    for ti in trade_info
                    if ti["mod"] == "enchant.stat_3086156145"
                ][0]["max"]
            )
            output["cluster_jewel_passives"] = output[
                "cluster_jewel_passives_min"
            ]
        except (KeyError, IndexError) as e:
            # TODO: Find a way to filter out unique cluster jewels better
            pass

    output["alt_quality"] = ""
    output["is_alt_quality"] = False
    alt_filter = (
        output["item_name"].str.startswith("Anomalous")
        | output["item_name"].str.startswith("Divergent")
        | output["item_name"].str.startswith("Phantasmal")
    )
    if not output[alt_filter].empty:
        output.loc[alt_filter, "is_alt_quality"] = True
        output.loc[alt_filter, "alt_quality"] = output["item_name"].apply(
            lambda s: s[: s.find(" ")],
        )
        output.loc[alt_filter, "item_name"] = output["item_name"].apply(
            lambda s: s[s.find(" ") + 1 :],
        )

    if "name" in df.columns and "details_id" in df.columns:
        output["influences"] = df.apply(
            lambda r: "/".join(
                i.value
                for i in _parse_name_and_details_id(
                    str(r["name"]),
                    str(r["details_id"]),
                )[1]
            ),
            axis=1,
        )
        output["num_influences"] = (
            df["variant"].str.count("/").fillna(0).astype(int)
            if "variant" in df.columns
            else 0
        )

    for column in (
        "base_type",
        "level_required",
        "links",
        "gem_level",
        "gem_quality",
        "map_tier",
        "stack_size",
    ):
        if column in df.columns:
            output[column] = df[column]
            if column == "links":
                output[column] = output[column].fillna(0)

    output["chaos_value"] = (
        df["chaos_equivalent"]
        if "chaos_equivalent" in df.columns
        else df["chaos_value"]
    )
    # Normalized chaos values
    # XXX: since log(0) is -inf, the min chaos value of the dataframe replaces
    # rows with a chaos value of 0
    min_chaos_value = output.loc[
        output["chaos_value"] != 0, "chaos_value"
    ].min()
    output["chaos_value"].replace(0, min_chaos_value, inplace=True)  # type: ignore
    output["chaos_value_log"] = np.log(output["chaos_value"])

    # Pre-defined quantiles (quartiles, quintiles, percentiles)
    for label, q in quantiles.items():
        labels = None
        if isinstance(q, (list, tuple)):
            q, labels = q
        output[label] = pd.qcut(
            output["chaos_value"].rank(method="first", numeric_only=True),
            q=q,
            labels=False if labels is None else None,
            precision=0,
            duplicates="drop",
        )
        if labels is not None:
            output[label] = output[label].map(dict(enumerate(labels)))
    return output


def json_normalize(data: dict[Any, Any]) -> pd.DataFrame:
    df = pd.json_normalize(data)
    df.columns = [inflection.underscore(c) for c in df.columns]
    return df


@uplink.install
class NinjaDataFrameFactory(uplink.converters.Factory):
    def create_response_body_converter(self, cls, request_definition):
        return lambda response: transform_ninja_df(
            df=json_normalize(response.json()["lines"]),
        )


uplink_retry = uplink.retry(
    when=uplink.retry.when.status(503) | uplink.retry.when.raises(Exception),
    stop=uplink.retry.stop.after_attempt(5)
    | uplink.retry.stop.after_delay(10),
    backoff=uplink.retry.backoff.jittered(multiplier=0.5),
)


@raise_for_status
@uplink_retry
@uplink.returns.json
@uplink.json
@uplink.get
def get_json():
    """Template for GET requests with JSON as both request and response."""


@raise_for_status
@uplink_retry
@uplink.get
def get_dataframe():
    ...


class NinjaConsumer(uplink.Consumer):
    default_base_url = "https://poe.ninja/api/data/"

    @uplink.ratelimit(calls=2, period=150)
    @get_dataframe("CurrencyOverview")  # type: ignore
    def get_currency_overview(
        self,
        league: uplink.Query(type=str),  # type: ignore
        type: uplink.Query(type=CurrencyType),  # type: ignore
    ) -> pd.DataFrame:
        ...

    @uplink.ratelimit(calls=2, period=150)
    @get_dataframe("CurrencyHistory")  # type: ignore
    def get_currency_history(
        self,
        league: uplink.Query(type=str),  # type: ignore
        type: uplink.Query(type=CurrencyType),  # type: ignore
        currency_id: uplink.Query("currencyId", type=int),  # type: ignore
    ) -> pd.DataFrame:
        ...

    @uplink.ratelimit(calls=30, period=150)
    @get_dataframe("ItemOverview")  # type: ignore
    def get_item_overview(
        self,
        league: uplink.Query(type=str),  # type: ignore
        type: uplink.Query(type=ItemType),  # type: ignore
    ) -> pd.DataFrame:
        ...


class ItemFilterContext(pydantic.BaseModel):
    """Entrypoint for accessing economy data from poe.ninja."""

    data: dict[str, pd.DataFrame]
    _exalted_value: int = pydantic.PrivateAttr(default=0)
    _quantile_thresholds: dict[
        str, list[dict[str, float]]
    ] = pydantic.PrivateAttr(default_factory=list)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self._exalted_value = self.data["currencies"][
            self.data["currencies"].item_name == "Exalted Orb"
        ].iloc[0]["chaos_value"]
        self._quantile_thresholds = {
            k: get_quantile_thresholds(df) for k, df in self.data.items()
        }
        self.data = {
            k: self._post_process(k, df) for k, df in self.data.items()
        }

    def get_display_value(
        self,
        chaos_value: float,
        round_down_by: int = 1,
        precision: int = 0,
    ):
        return get_display_value(
            chaos_value=chaos_value,
            exalted_exchange_value=self._exalted_value,
            round_down_by=round_down_by,
            precision=precision,
        )

    def get_quantiles_for_threshold(
        self,
        key: str,
        min_chaos_value: float,
    ) -> Optional[dict[str, float]]:
        for threshold in self._quantile_thresholds[key]:
            if threshold["chaos_value"] >= min_chaos_value:
                return threshold
        return self._quantile_thresholds[key][-1]

    @pydantic.validator("data")
    def data_must_contain_all_types(
        cls, v: dict[str, pd.DataFrame]
    ) -> dict[str, pd.DataFrame]:
        for type_ in [*CurrencyType, *ItemType]:
            if type_.pluralized_underscored_value not in v:
                raise ValueError(f"{type_} missing from filter context")
        return v

    @check_io(
        df=ExtendedNinjaOverviewSchema.to_schema(),
        out=PostProcessedNinjaOverviewSchema.to_schema(),
    )
    def _post_process(self, key: str, df: pd.DataFrame) -> pd.DataFrame:
        df["exalted_value"] = df["chaos_value"].apply(
            lambda x: x / self._exalted_value
        )
        df["display_value"] = df["chaos_value"].apply(
            lambda x: get_display_value(
                chaos_value=x,
                exalted_exchange_value=self._exalted_value,
                precision=2,
            )
        )
        return df
