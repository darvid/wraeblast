import asyncio
import datetime
import json
import os
import pathlib
import tempfile

import boto3
import cleo
import pandas as pd
import pkg_resources
import structlog

from wraeblast import errors, insights, logging_
from wraeblast.filtering.parsers.extended import config, loads, render
from wraeblast.filtering.serializers.standard import dumps


log = structlog.get_logger()


def get_current_league() -> str:
    return open(".current_league").read().strip()


def check_league_option(league_name: str) -> str:
    if league_name == "TEMP":
        try:
            return get_current_league()
        except FileNotFoundError:
            raise errors.WraeblastError("no league specified")
    return league_name


class BaseCommand(cleo.Command):
    def initialize_logging(self):
        logging_.initialize_logging(
            default_level="DEBUG" if self.io.is_very_verbose() else "INFO"
        )


def main() -> int:
    app = cleo.Application(
        name=__package__,
        version=pkg_resources.get_distribution(__package__).version,
    )
    for command in (
        RenderFilterCommand,
        SyncInsightsCommand,
    ):
        app.add(command())
    return app.run()


class RenderFilterCommand(BaseCommand):
    """Render an item filter template

    render_filter
        {file : filter template file}
        {--O|options-file= : Options JSON file}
        {--d|output-directory=. : Output directory}
        {--i|keep-intermediate : Keep rendered intermediate template}
        {--o|output= : Output file}
        {--l|league=TEMP : Current league name}
        {--N|no-sync : Prevents automatic insights syncing}
        {--no-insights : Disables all economy data fetching}
        {--s|store-path= : Fetch HDF from the given path}
        {--p|preset=default : Preset name}

    """

    def format_filename(self, format_str: str) -> str:
        return datetime.datetime.now().strftime(
            format_str.format(
                league=str(self.option("league")),
                league_short=str(self.option("league"))[:3],
                preset=str(self.option("preset")),
            )
        )

    def handle(self) -> None:
        self.initialize_logging()
        self.line("<info>Rendering item filter from template</info>")

        league = check_league_option(str(self.option("league")))
        output_dir = pathlib.Path(str(self.option("output-directory")).strip())
        output_filename = self.format_filename(
            str(self.option("output")).strip()
        )
        output_path = output_dir / output_filename
        options_filename = str(self.option("options-file")).strip()
        tmpl_filename = str(self.argument("file")).strip()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        store_path = str(self.option("store-path"))
        store_is_s3 = store_path.startswith("s3://")

        if store_is_s3:
            bucket, key = store_path[5:].split("/", 1)
            key_basename = pathlib.Path(key).name
            self.line(f"<info>Downloading data from S3: {bucket}/{key}</info>")
            tempdir = tempfile.TemporaryDirectory()
            key_dest = str(pathlib.Path(tempdir.name) / key_basename)
            s3 = boto3.resource("s3")
            s3.Bucket(bucket).download_file(key, key_dest)
            store = insights._create_hdfstore(key_dest)
        else:
            store = insights._create_hdfstore(store_path)

        loop = asyncio.get_event_loop()
        filter_context = None
        if not self.option("no-insights"):
            filter_context = loop.run_until_complete(
                insights.initialize_filter_context(
                    league=league,
                    no_sync=bool(self.option("no-sync")),
                    store=store,
                ),
            )
        else:
            self.line("<info>Insights disabled</info>")
        if options_filename:
            with open(options_filename) as f:
                options = config.ItemFilterPrerenderOptions.with_defaults(
                    ctx=filter_context,
                    overrides=json.load(f),
                )
        else:
            options = None

        with open(tmpl_filename) as f:
            keep_intermediate = bool(self.option("keep-intermediate"))
            if keep_intermediate:
                intermediate_filename = tmpl_filename
                if intermediate_filename.endswith(".j2"):
                    intermediate_filename = intermediate_filename[:-3]
                intermediate_filename = pathlib.Path(
                    intermediate_filename
                ).name
                intermediate_filename = output_dir / intermediate_filename
                if intermediate_filename.suffix not in (".yml", ".yaml"):
                    intermediate_filename = intermediate_filename.with_suffix(
                        ".yaml"
                    )
                with open(intermediate_filename, "w") as f_:
                    self.line("<info>Rendering intermediate template</info>")
                    template = render(
                        f.read(),
                        ctx=filter_context,
                        options=options,
                    )
                    f_.write(template)
            else:
                template = f.read()
            item_filter = loads(
                template,
                ctx=filter_context,
                pre_rendered=keep_intermediate,
                options=options,
            )
            if self.option("preset") != "default":
                item_filter.apply_preset(
                    preset_name=str(self.option("preset"))
                )
            rendered = dumps(item_filter)
            if self.option("output") is None:
                self.write(rendered)
            else:
                self.line(f"<info>Writing filter to {output_filename}")
                with open(output_path, "w") as f:
                    f.write(rendered)


class SyncInsightsCommand(BaseCommand):
    """Fetch Path of Exile economy insights

    sync_insights
        {--s|store-path= : Store HDF at the given path}
        {--l|league=TEMP : Current league name}

    """

    def handle(self) -> None:
        self.initialize_logging()
        self.line("<info>Syncing economy data from poe.ninja</info>")
        league = check_league_option(str(self.option("league")))
        loop = asyncio.get_event_loop()
        store_path = str(self.option("store-path"))
        store_is_s3 = store_path.startswith("s3://")
        if store_is_s3:
            tempdir = tempfile.TemporaryDirectory()
            store = insights._create_hdfstore(
                str(pathlib.Path(tempdir.name) / f"wraeblast-{league}.h5")
            )
        else:
            store = insights._create_hdfstore(store_path)
        store = loop.run_until_complete(
            insights.initialize_insights_cache(
                league=league,
                store=store,
            ),
        )
        if store_is_s3:
            print(store_path)
            bucket, key = store_path[5:].split("/", 1)
            self.line(f"<info>Syncing to S3 bucket: {bucket}/{key}</info>")
            s3 = boto3.resource("s3")
            s3.Bucket(bucket).upload_file(store._path, key)
