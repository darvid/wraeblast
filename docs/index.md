# Overview

An experimental library for interfacing with [Path of Exile][1] game and
[economy data][2], and accompanying tools, including a [rich item filter
generation framework](/filtering/overview).

## Features

* Complete standard item filter grammar parsing support.
* Economy insights API powered by [poe.ninja][2]
    * Integration with [pandas][3] for data normalization and analysis
    * Local caching and rate limiting
* Powerful extended item filter framework
    * Internally uses single API to express both standard and extended
      filter rules
    * [Jinja2][4]-templated YAML filter format
    * Extended filter features include:
        * Rule tagging
        * Presets (i.e. feature flags)
        * Styles
        * Template environment helpers for color manipulation, economy
          data quantization and grouping, filter alert sound generation
          with text-to-speech (TTS) synthesization, and more
* [Matplotlib][5] [colormap][6] integration, enabling dynamic procedural
  generation of rule colors

## Installation

### With `conda`

```shell
$ conda env create -f environment.yml
$ conda develop .
# Optionally install Jupyter in the conda environment:
$ conda install -c anaconda ipykernel jupyter
```

### With ``pip``

```shell
❯ pip install wraeblast
```

### With ``git``

```shell
❯ git clone https://github.com/darvid/wraeblast
❯ cd wraeblast
❯ poetry install
```

[1]: https://pathofexile.com
[2]: https://poe.ninja
[3]: https://pandas.pydata.org/
[4]: https://jinja.palletsprojects.com/en/3.0.x/
[5]: https://matplotlib.org/
[6]: https://matplotlib.org/stable/tutorials/colors/colormaps.html
