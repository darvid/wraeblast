# Overview

**Wraeblast** provides an **experimental**, feature-rich
[item filter][1] development framework and toolkit for Path of Exile.

!!! note
    While an example trade league filter is included with the project,
    ongoing development is focused on the _library_, not the filter.
    No guarantees are made about filter quality, feature completeness,
    accuracy, or updates. Use at your own risk.

## Architecture

### Filter Template

The filter template is a Jinja2 templated YAML file (``.yaml.j2``), which
provides a more structured approach to developing item filters. While
the templating environment provides core features like colormaps,
economy insights, and text-to-speech synthesis helpers, it is entirely
possible to build simple item filters without any templating whatsoever,
while still being able to leverage all of the organizational features
**Wraeblast** provides.

The intermediate template YAML rendered by Jinja2 can be saved to a file
for debugging purposes by passing the ``-i`` flag to the ``render_filter`` [CLI
subcommand](/cli#render_filter).

### Filter Options

The filter options file is an optional, JSON formatted file that
configures thresholds, colormaps, and other related _pre-render_
options. These options are available in the template environment via the
``options`` object, and are deserialized to a ``ItemFilterPrerenderOptions``
object.

For example, to override the **maps** colormap and generate rules:

=== "example.config.json"

    ```json linenums="1" hl_lines="3"
    {
        "colormaps": {
            "maps": {
                "name": "Hawaii_20_r"
            }
        }
    }
    ```

=== "example.yaml.j2"

    ```yaml+jinja linenums="1" hl_lines="2"
    {%- for item in ctx.invitations.lines: -%}
    {%- set bg = options.colormaps.maps.pick(item.chaos_value) %}
    - name: "Invitations - {{ item.name }}"
      conditions:
        BaseType: "{{ item.name }}"
      actions:
        SetBackgroundColor: '{{ bg.hex }}'
        SetBorderColor: '{{ text_color(bg) }}'
        SetTextColor: '{{ text_color(bg) }}'
      tags:
        - maps
        - invitations
    {%- endfor %}
    ```

### Economy Insights

The [``insights``](/reference/#wraeblast.insights) module provides a simple
API for slicing and dicing economy data from [poe.ninja][2]. Economy
data for the given league is fetched asynchronously at the start of
each command line invocation, and cached locally for a short period of
time. Extended item filter templates can access the
[``ItemFilterContext``](/reference/#wraeblast.insights.ItemFilterContext)
object via ``ctx``.

## Similar Tools

It should be mentioned that other item filter tools and libraries exist,
which serve similar but not identical purposes to **Wraeblast**.

* [NeverSink][3] filters are known for being extensible via the
  [FilterBlade][4] web UI, but the underlying framework for structuring
  the base filters is a [custom DSL][5].
* [FilterBlast][6] is another popular in-browser filter configuration
  tool, which adds a [comment layer syntax][7] on top of standard item
  filters, allowing for parametrization of various filter elements.
* [Filtration][7] is a graphical desktop application for creating and
  customizing filters. It appears to be unmaintained for a few years.

There are probably other tools that haven't been mentioned here.
These are all excellent projects, however the use cases and goals for
**Wraeblast** differ quite a bit.

## Goals

### Strictness

Filter strictness is an extremely common concept that most Path of Exile
players are familiar with. Starting a new league? Download the
*"regular"* strictness, of course. Two weeks into the league? Time to
switch to *"semi-strict"*, or *"turbo-Ω-omni-strict"* if you're a real
juicer. This probably works well enough for most players, but strictness
is subjective depending on an individual player's goals and experience.

One of the major goals for **Wraeblast** is to make filter
*"strictness"* completely granular, quantifiable, and configurable by
the discerning player.

### Visual Clarity

While this is more of an underlying problem of the loot system that Path
of Exile 2 will hopefully resolve, loot filters play a big part in the
time saved or wasted by a player progressing through the end game.
Currently, most community maintained filters provide a decent amount of
colorful options, and are good at distinguishing between a couple tiers
of items: items that *might be valuable*, and items that are *definitely
garbage*.

**Wraeblast** attempts to improve visual clarity by:

* Making wholesale filter color changes extremely easy to configure
  with colormaps, which has the added benefit of making color variations
  more frequent, vibrant, and meaningful.
* Leveraging data science tools to interpret and transform economy data
  within the filter template itself.

### Graphical Filter Editing

No.

### Filter Depth

Popular community filters include rules for every vendor recipe, base
types for crafting that may or may not be applicable or even profitable
in a given league, and rare but possibly valuable item drops, like
double corrupted items, items with Incursion modifiers, and so on. While
useful in some situations, it is unlikely that the average player can
keep track of every rule and visual cue.

Conversely, while some community filters *are* cognizant of trade league
economy data, customization and configurability is arguably lackluster
aside from re-organizing items within pre-defined tiers, and requires
a significant time investment, sometimes more than once per league.

**Wraeblast** solves this problem not by building the ultimate kitchen
sink filter, but rather by focusing on the data. Economy data is at the
forefront of the filter template environment, and the tools to generate
visually appealing, laser focused item filters are provided to aspiring
filter authors and players. (The example trade league filters included
in this project are pretty cool, too.)

[1]: https://pathofexile.fandom.com/wiki/Guide:Item_filter
[2]: https://poe.ninja/
[3]: https://github.com/NeverSinkDev
[4]: https://www.filterblade.xyz/
[5]: https://github.com/NeverSinkDev/Filter-Precursors
[6]: https://filterblast.xyz/
[7]: https://filterblast.xyz/item-filter-syntax.html#extended
[8]: https://github.com/ben-wallis/Filtration
