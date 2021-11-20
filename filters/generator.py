#!/usr/bin/env python
import asyncio
import functools
import json
import pathlib
import sys
from typing import Any, Optional

import cleo
import mergedeep
import pandas as pd

from wraeblast import cmd, insights
from wraeblast.filtering.parsers.extended import config


default_threshold_overrides = {
    "base_types": {"quantile": "D9"},
    "blighted_maps": {"quantile": "QU1"},
    "delirium_orbs": {"quantile": "QU1"},
    "divination_cards": {"quantile": "QU4"},
    "essences": {"quantile": "QU2"},
    "incubators": {"quantile": "QU2"},
    "prophecies": {"quantile": "QU4"},
    "scarabs": {"quantile": "QU1"},
    "skill_gems": {"quantile": "QU4"},
    "uniques": {"quantile": "QU4"},
    "vials": {"quantile": "QU2"},
}
secondary_colormap_categories = (
    "base_types",
    "uniques",
    "fragments",
    "artifacts",
    "prophecies",
    "vials",
    "fossils",
    "resonators",
)
sequential_colormaps = [
    "BluGrn_7",
    "BluYl_7",
    "BrwnYl_7",
    "Burg_7",
    "BurgYl_7",
    "DarkMint_7",
    "Emrld_7",
    "Magenta_7",
    "Mint_7",
    "OrYel_7",
    "Peach_7",
    "PinkYl_7",
    "Purp_7",
    "PurpOr_7",
    "RedOr_7",
    "Sunset_7",
    "SunsetDark_7",
    "Teal_7",
    "TealGrn_7",
    "agGrnYl_7",
    "agSunset_7",
    "Algae_20",
    "Amp_20",
    "Deep_20",
    "Dense_20",
    "Gray_20",
    "Haline_20",
    "Ice_20",
    "Matter_20",
    "Oxy_20",
    "Phase_20",
    "Solar_20",
    "Speed_20",
    "Tempo_20",
    "Thermal_20",
    "Turbid_20",
    "Blues_9",
    "BuGn_9",
    "BuPu_9",
    "GnBu_9",
    "Greens_9",
    "Greys_9",
    "OrRd_9",
    "Oranges_9",
    "PuBu_9",
    "PuBuGn_9",
    "PuRd_9",
    "Purples_9",
    "RdPu_9",
    "Reds_9",
    "YlGn_9",
    "YlGnBu_9",
    "YlOrBr_9",
    "YlOrRd_9",
]
for cm in sequential_colormaps[:]:
    sequential_colormaps.append(cm + "_r")
sequential_colormaps.sort()


def get_thresholds(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby(list(insights.quantiles.keys()))
    return grouped.agg({"chaos_value": ["min"]})


def write_config(
    name: str,
    colormap: str,
    tag: Optional[str] = None,
    quantile: Optional[list[str]] = None,
    secondary_colormap: Optional[str] = None,
    output_directory: str = ".",
    overrides: dict[str, Any] = None,
    json_indent: int = 4,
):
    if tag is not None:
        tag = tag.lstrip("-")
        tag = (
            f"-{quantile}"
            if tag == "QUANTILE" and quantile is not None
            else (f"-{tag}" if tag != "QUANTILE" else "")
        )
    else:
        tag = ""
    template_config = config.default_options.copy()
    colormap_name = colormap.rstrip("_r").rsplit("_", maxsplit=1)[0]
    if colormap.endswith("_r"):
        colormap_name += "_r"
    filename = f"{name}{tag}-{colormap_name}.config.json"

    for category in template_config["thresholds"]:
        if quantile is not None:
            template_config["thresholds"][category]["quantile"] = quantile
        elif "quantile" in template_config["thresholds"][category]:
            template_config["thresholds"][category].pop("quantile")

    if overrides is not None:
        mergedeep.merge(template_config["thresholds"], overrides)

    for key in template_config["colormaps"]:
        if key in ("life_flasks", "mana_flasks"):
            continue
        template_config["colormaps"][key]["name"] = (
            secondary_colormap
            if key in secondary_colormap_categories
            else colormap
        )
    parent_dir = pathlib.Path(output_directory)
    parent_dir.mkdir(exist_ok=True)
    with open(parent_dir / filename, "w") as f:
        f.write(json.dumps(template_config, indent=json_indent))
    return filename


class BuildCommand(cmd.BaseCommand):
    """Generate filter options from a matrix of colormaps and thresholds.

    build_configs
        {filter-name : Filter name}
        {thresholds=ALL : Comma-separated quantile thresholds (defaults
            to all quintiles: QU0..QU4)}
        {colormaps=ALL : Comma-separated colormap names (defaults to
            all sequential colormaps)}
        {--C|secondary-colormap=Turbid_20_r : Complimentary colormap
            used for base items, uniques, etc.}
        {--t|tag=QUANTILE : Tag filter filename (defaults to each quantile)}
        {--l|league=TEMP : Current league name}
        {--O|override-thresholds=OVERRIDES : JSON formatted overrides}
        {--o|output-directory=filters : Output directory}

    """

    def handle(self) -> None:
        filter_name = str(self.argument("filter-name"))
        thresholds = str(self.argument("thresholds"))
        if thresholds.upper() == "NONE":
            quantiles = None
        elif thresholds.upper() == "ALL":
            quantiles = [f"QU{i}" for i in range(1, 6)]
        else:
            quantiles = [q.strip() for q in thresholds.split(",")]
        tag = str(self.option("tag"))
        overrides = str(self.option("override-thresholds"))
        if overrides == "OVERRIDES":
            overrides = default_threshold_overrides.copy()
        else:
            overrides = json.loads(overrides)
        colormaps = str(self.argument("colormaps"))
        if colormaps.upper() != "ALL":
            colormaps = [c.strip() for c in colormaps]
        else:
            colormaps = sequential_colormaps.copy()
        secondary_colormap = str(self.option("secondary-colormap"))
        output_directory = pathlib.Path(str(self.option("output-directory")))
        # league = str(self.option("league"))
        for colormap in colormaps:
            config_writer = functools.partial(
                write_config,
                name=filter_name,
                colormap=colormap,
                secondary_colormap=secondary_colormap,
                tag=tag,
                output_directory=output_directory,
                overrides=overrides,
            )
            if quantiles is not None:
                for quantile in quantiles:
                    filename = config_writer(quantile=quantile)
                    self.line(f"<info>Wrote {filename}</info>")
            else:
                filename = config_writer(quantile=None)
                self.line(f"<info>Wrote {filename}</info>")


class RankingsCommand(cmd.BaseCommand):
    """Print rankings of economy segments.

    rankings
        {category : Economy category (e.g. currency, fragments, etc.)}
        {--l|league=TEMP : Current league name}
        {--t|thresholds : Return quantile thresholds}
    """

    def handle(self) -> None:
        league = cmd.check_league_option(str(self.option("league")))
        loop = asyncio.get_event_loop()
        filter_context = loop.run_until_complete(
            insights.initialize_filter_context(league=league),
        )
        category = str(self.argument("category"))

        df = filter_context.data[category]
        quantile_labels = insights.quantiles.keys()
        table = self.table()
        table.set_header_row(
            [
                "Index",
                "Name",
                "Chaos Value",
                *[ql.capitalize() for ql in quantile_labels],
            ]
        )
        for index, row in df.iterrows():
            quantiles = [
                str(row[label]) for label in quantile_labels
            ]  # type: ignore
            table.add_row(
                [
                    str(index),
                    str(row["item_name"]),
                    str(row["chaos_value"]),
                    *quantiles,
                ]
            )
        self.line(f"<info>Rankings ({category})")
        table.render(self.io)

        if self.option("thresholds"):
            table = self.table()
            table.set_header_row(
                [
                    "Quartile",
                    "Quintile",
                    "Decile",
                    "Percentile",
                    "Threshold (chaos value)",
                ]
            )
            self.line("")
            self.line("<info>Thresholds:</info>")
            thresholds = get_thresholds(df)
            for group, threshold in thresholds.iterrows():
                table.add_row(
                    [str(c) for c in group]  # type: ignore
                    + [str(threshold.chaos_value["min"])]
                )
            table.render(self.io)


def main() -> int:
    app = cleo.Application(
        name=__name__,
        version="0.1.0",
    )
    app.add(BuildCommand())
    app.add(RankingsCommand())
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
