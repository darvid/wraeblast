import asyncio
import datetime
import json
import pathlib

import cleo
import pkg_resources
import structlog

from wraeblast import errors, insights, logging
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


class CommandMixin:
    def initialize_logging(self):
        logging.initialize_logging(
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


class RenderFilterCommand(CommandMixin, cleo.Command):
    """Render an item filter template

    render_filter
        {file : filter template file}
        {--O|--options-file= : Options JSON file}
        {--d|--output-directory=. : Output directory}
        {--i|--keep-intermediate : Keep rendered intermediate template}
        {--o|output= : Output file}
        {--l|league=TEMP : Current league name}
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
        output_dir = pathlib.Path(str(self.option("output-directory")))
        output_filename = self.format_filename(str(self.option("output")))
        output_path = output_dir / output_filename
        options_filename = str(self.option("options-file"))
        tmpl_filename = str(self.argument("file"))
        output_dir.mkdir(exist_ok=True)

        loop = asyncio.get_event_loop()
        filter_context = loop.run_until_complete(
            insights.initialize_filter_context(league=league),
        )
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


class SyncInsightsCommand(CommandMixin, cleo.Command):
    """Fetch Path of Exile economy insights

    sync_insights
        {--l|league=TEMP : Current league name}

    """

    def handle(self) -> None:
        self.initialize_logging()
        self.line("<info>Syncing economy data from poe.ninja</info>")
        league = check_league_option(str(self.option("league")))
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            insights.initialize_insights_cache(league=league),
        )
