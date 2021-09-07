<h1 align="center">
  wraeblast
  <br>
</h1>

<h4 align="center">
    A library for interfacing with
    <a href="https://pathofexile.com">Path of Exile</a> game and
    <a href="https://poe.ninja">economy data</a>, and accompanying tools.
</h4>

The ultimate goal of this library is to provide a rich API for
developing Path of Exile tools and applications, as well as facilitate
data science and visualization.

<!--ts-->
   * [Filter Generation](#filter-generation)
      * [Features](#features)
      * [<del>Rationale</del> Development Manifesto](#rationale-development-manifesto)
      * [Showcase](#showcase)
      * [Architecture](#architecture)
      * [Usage](#usage)
      * [Roadmap](#roadmap)
   * [[REDACTED]](#redacted)

<!-- Added by: david, at: Thu 02 Sep 2021 10:43:01 PM EDT -->

<!--te-->

## Filter Generation

**Wraeblast** provides an **experimental**, feature-rich
[item filter][1] development framework and toolkit.

⚠️ **DISCLAIMER**: ⚠️ Any filters distributed by this project are
*examples* and not currently supported, maintained, or guaranteed to be
updated. Please use [FilterBlade][7] if you're looking for a loot filter
to configure and download.

### Features

* Complete standard item filter grammar parsing support.
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

### ~~Rationale~~ Development Manifesto

* Path of Exile's current loot system *requires* complex filters 🤦
* Complex filters *require* a 🔨 filter generation/templating layer 🔨
  (this is exactly what [NeverSink][8] has done)
* Many community maintained filters (including NeverSink) are
  ✨ awesome ✨ and work well for the majority of the playerbase,
  but have some shortcomings:
  * 🚀 Über strict isn't always über enough for softcore juiced map
    blasters
  * 🌈 Filter customization is somewhat limiting and tedious to do
    through a web interface
  * 📈 Economy-based presets and filters leverage a very small subset
    of the available data from [poe.ninja][2]
  * 👕 Most filters tend to adopt a one-size-fits-all strategy, with
    a plethora of rules for _all_ the content in the game, visually
    distinct colors but impossible to remember for most players
  * 🔊 Configuring custom sounds is a chore
* What if we had a filter _framework_ that was developer-oriented (for
  now), data-driven, and complexity _reducing_?

  Some ground rules:

  * **Wraeblast is not a filter.** An example filter is included, but
    is _not_ the focus of this project.
  * Don't cater to everyone. Provide the tools for **developers
    first**, players second, to craft the filters based on play style,
    league (SC/HC), and current progression.
  * Don't re-invent the wheel: use existing, well documented, industry
    standard tools, markup language formats, and libraries like Jinja2,
    YAML, matplotlib, etc. rather than baking new ones.

### Showcase

Click the thumbnails to ▶️ play

* ✨ Automatically generated text-to-speech filter sounds ✨

  ``` yaml+jinja
  # Cluster jewels
  # ...
  - conditions:
    # ...
    actions:
      # ...
      {%- if item.chaos_value >= 10 %}
      CustomAlertSound: '{{ tts("{} c".format(round_down(item.chaos_value, 10))) }}'
      {%- endif %}
    tags:
    # ...
  ```

  [<img src="https://i.imgur.com/qWcVNVz.jpg">][9]

* ✨ Colormap demo ✨

  [<img src="https://i.imgur.com/GeV3yZu.jpg">][10]

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
    -l Expedition \
    -d output \
    -O filters/softcore.config.json \
    -o softcore.filter -i -vvv filters/softcore.yaml.j2
```

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
