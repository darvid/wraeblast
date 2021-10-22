<h1 align="center">
  wraeblast
  <br>
</h1>

<p align="center">
  <a href="https://github.com/darvid/wraeblast/actions/workflows/library.yml">
    <img title="Library workflow status" src="https://github.com/darvid/wraeblast/actions/workflows/library.yml/badge.svg">
  </a>
  <a href="https://github.com/darvid/wraeblast/actions/workflows/filters.yml">
    <img title="Filters workflow status" src="https://github.com/darvid/wraeblast/actions/workflows/filters.yml/badge.svg?event=workflow_dispatch">
  </a>
  <a href="https://wraeblast.readthedocs.io">
    <img title="Library Documentation" src="https://readthedocs.org/projects/wraeblast/badge/?version=latest">
  </a>
  <a href="https://discord.gg/gRtHu7USBw">
    <img alt="Discord" src="https://img.shields.io/discord/886072454349467651">
  </a>
</p>
<p align="center">
  A library for interfacing with
  <a href="https://pathofexile.com">Path of Exile</a> game and
  <a href="https://poe.ninja">economy data</a>, and a
  <a href="https://github.com/darvid/wraeblast/releases">set of item
  filters</a> geared towards trade league players.
</p>

**3.16 Scourge League Update:** The trade filter is expected to be
updated within the first few days of the upcoming league. **Wraeblast**
relies heavily on economy data, and some of the cluster jewel filtering
has to map passive descriptions to seemingly GGG internal, undocumented
cluster jewel passive names. This work can only be done once the data is
available either through data-mining or post-launch. Do note, however,
that a **league start filter** is in the works with limited TTS, and
obviously sans economy data. See the [3.16 Scourge League project board][18]
to track progress.

<!--ts-->
   * [Filter Generation](#filter-generation)
      * [Framework Features](#framework-features)
      * [Filter Features](#filter-features)
         * [Demos](#demos)
         * [Installation](#installation)
      * [<del>Rationale</del> Development Manifesto](#rationale-development-manifesto)
      * [Architecture](#architecture)
      * [Usage](#usage)
      * [Roadmap](#roadmap)
   * [[REDACTED]](#redacted)

<!-- Added by: david, at: Wed 08 Sep 2021 11:38:07 PM EDT -->

<!--te-->

## Filter Generation

**Wraeblast** provides an **experimental**, feature-rich
[item filter][1] development framework and toolkit, as well as a
dogfooded [trade league filter][12].

⚠️ **DISCLAIMER**: ⚠️ This is an experimental, proof-of-concept project,
and the author is not responsible for any loss of currency or efficiency
as a result of using this project's filters. Please use [FilterBlade][7]
for regular gameplay unless you're brave enough to deal with a pre-alpha
filter.

### Framework Features

* Economy insights API powered by [poe.ninja][2]
  * Integration with [pandas][3] for data normalization and analysis
  * Local caching and rate limiting
* Powerful extended item filter framework
  * Internally uses single API to express both standard and extended
    filter rules
  * [Jinja2][4]-templated YAML filter format
  * Some extended filter features include:
    * Rule tagging
    * Presets (i.e. feature flags)
    * Styles
    * Template environment helpers for 🌈 color manipulation, 📈 economy
      data quantization and grouping, 🔊 filter alert sound generation
      (TTS), and more
* [Matplotlib][5] [colormap][6] integration, enabling procedural
  generation of *item*-based (not just tier-based like many popular
  community filters) filter colors.
* ...and many other technical features under the hood.

### Filter Features

* 📊 **Quantile based variants** for efficient farming.[†](#f1)

  Currently provides two variants: **D2** (2nd decile) and **QU4** (4th
  quintile). Additional quantiles will probably be included in nightly
  releases, depending on feedback and experimentation.
* 🌌 **54 colormaps** (108 if you include reversed colormaps, indicated
  by an `_r` prefix) included *per quantile variant*.

  There are even more colormap palettes available, it would just be too
  cost prohibitive to include them all at present. See the
  [Palettable][13] documentation for colormap previews (only sequential
  colormaps are used).

  Some form of item filter preview may be added as a feature in the
  future, but for now either refer to the documentation or just try them
  out in game.
* 🔊 **[AWS Polly][14] Neural Text-To-Speech ([NTTS][15])** powered
  synthesized alert sounds for ✨all✨ valuable filter rules (quantile
  dependent).

  Get instant, **aural** feedback for currency, fragments, skill gems,
  cluster jewels, and more. Anything tracked by [poe.ninja][2] can be
  supported by TTS.

  Filter sounds for relevant items are also generated for varying stack
  sizes, for more accurate chaos value approximations.

  The `Aria` (New Zealand English, appropriately) voice is currently the
  default for the trade league filters included with this project, but
  any voice supported by AWS Polly can be used when developing new
  filters.


<a name="f1">†</a> *TLDR:* think of quantiles like strictness, with an
arguably better ranking of item and currency value in a trade league
than hard-coded tiers.

#### Demos

* [20% deli, beyond+nemesis map](https://streamable.com/ppi4sd) with `D3` quantile,
  `TealGrn_r` colormap filter.
* [Expedition artifacts](https://streamable.com/8ng40x), also using
  `TealGrn_r` colormap filter.
* [Various drops](https://streamable.com/kqv021) with `QU4` quantile,
  `SunsetDark_r` colormap filter.
* *More coming soon*

#### Installation

Download the filter variant(s) of your choice from the [releases][16],
as well as the latest, compressed TTS filter sounds. Extract both
the `.filter` and the `FilterSounds` directory to your `Path of Exile`
directory.

Filter syncing is currently not supported, and would be largely useless
regardless without a way to sync filter sound files.

Note that **updating the filter also requires updating the TTS files**,
and you can simply choose to overwrite existing files every time, or
delete the entire TTS folder before installing the latest version.

### ~~Rationale~~ Development Manifesto

* Path of Exile's current loot system *requires* complex filters for
  efficient gameplay 🤦
* Complex filters *require* a 🔨 filter generation/templating layer 🔨
  (this is exactly what [NeverSink][8] has done)
* Many community maintained filters (including [NeverSink's][8]) are
  ✨ awesome ✨ and work well for the majority of the playerbase,
  but have some shortcomings:
  * 🚀 Über strict isn't always über enough for softcore juiced map
    blasters (filter *"strictness"* in general is a trap)
  * 🌈 Filter customization is somewhat limiting and tedious to do
    through a web interface (*loot filters are code*)
  * 📈 Economy-based presets and filters leverage a small subset of the
    available data from [poe.ninja][2]
  * 🛁 Filter rules take the kitchen sink approach and include a large
    amount of rules for low-value recipes and items
  * 🔊 Default alert sounds and sound rules are usually sparse, and
    adding custom sounds is a time-consuming process

### Architecture

```text
  ┌────────────────────────┐
  │                        │
  │ .yaml.j2 filter source ├────┐
  │                        │    │  ┌─────────────────────┐  ┌──────────┐
  └────────────────────────┘    │  │                     │  │          │
                                ├──┤    rendered .yaml   ├──┤  final   │
┌─────────────────────────────┐ │  │ intermediate filter │  │ .filter  │
│                             │ │  │                     │  │          │
│ .config.json filter options ├─┘  └─────────────────────┘  └──────────┘
│                             │
└─────────────────────────────┘
```

1. Economy insights data (currently just poe.ninja) is fetched and cached
2. The ``.yaml.j2`` is rendered with the economy data, colormaps, and filter
   option overrides from the ``.config.json`` file as context, if provided.
3. The resulting intermediate ``.yaml``  is then parsed by the extended
   filter parser, and outputs a final ``.filter`` file, and any associated
   sounds.

### Usage

See ``wraeblast --help`` and ``wraeblast render_filter --help`` for detailed
command line usage.

```shell
❯ wraeblast render_filter \
    -l Scourge \
    -d output \
    -O filters/softcore.config.json \
    -o softcore.filter -i -vvv filters/softcore.yaml.j2
```

For detailed library installation instructions and usage, see the
[technical documentation][17].

### Roadmap

* [X] Base filter generation functionality that nobody cares about
* [ ] Basic filters for different play styles: HC SSF, SC SSF, casual,
  deli farming, harby farming, legion farming, and all-around blasting 🚀
* [ ] Features for league launches: shimming new item classes without
      relying on poe.ninja data, early league specific colormaps,
      thresholds, etc.
* [ ] Performance improvements
* [ ] Unit tests and documentation
* [ ] Filter preview image generation
* [ ] Filter compression/deduping of rules
* [ ] Investigate auto-updating, but yet another downloadable tool to
      do it is out of the question (probably)
* [ ] Integration with [poeprofit][11] (i.e. dedicated styles and sounds
  for profitable strategies)
* [ ] Web frontend for downloading up-to-date filters (sans
  the complex configuration menus full of knobs and sliders and color
  pickers)
* [ ] Become obsolete when PoE 2 comes out 👻

## [REDACTED]

Additional features and tools are planned and will be incorporated into
this project in the near future.

[1]: https://pathofexile.fandom.com/wiki/Guide:Item_filter
[2]: https://poe.ninja/
[3]: https://pandas.pydata.org/
[4]: https://jinja.palletsprojects.com/en/3.0.x/
[5]: https://matplotlib.org/
[6]: https://matplotlib.org/stable/tutorials/colors/colormaps.html
[7]: https://www.filterblade.xyz/
[8]: https://github.com/NeverSinkDev
[9]: https://streamable.com/dt2j1b
[10]: https://streamable.com/lxee3z
[11]: https://poeprofit.com/
[12]: https://github.com/darvid/wraeblast/tree/main/filters/trade
[13]: https://jiffyclub.github.io/palettable/#finding-palettes
[14]: https://aws.amazon.com/polly/
[15]: https://docs.aws.amazon.com/polly/latest/dg/NTTS-main.html
[16]: https://github.com/darvid/wraeblast/releases
[17]: https://wraeblast.readthedocs.io/en/latest/
[18]: https://github.com/darvid/wraeblast/projects/7
