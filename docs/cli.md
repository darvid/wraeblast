# Command Line Interface

## Global Options

```shell
  -h (--help)               Display this help message
  -q (--quiet)              Do not output any message
  -v (--verbose)            Increase the verbosity of messages: "-v" for normal output, "-vv" for more verbose output and "-vvv" for
                            debug
  -V (--version)            Display this application version
  --ansi                    Force ANSI output
  --no-ansi                 Disable ANSI output
  -n (--no-interaction)     Do not ask any interactive question
```

## Commands

### ``render_filter``

```shell
❯ wraeblast render_filter --help
USAGE
  wraeblast render_filter [-O <...>] [-d <...>] [-i] [-o <...>] [-l <...>] [-p <...>] <file>

ARGUMENTS
  <file>                    filter template file

OPTIONS
  -O (--options-file)       Options JSON file
  -d (--output-directory)   Output directory (default: ".")
  -i (--keep-intermediate)  Keep rendered intermediate template
  -o (--output)             Output file
  -l (--league)             Current league name (default: "TEMP")
  -p (--preset)             Preset name (default: "default")

```

### ```sync_insights```

```shell
❯ wraeblast sync_insights --help
USAGE
  wraeblast sync_insights [-l <...>]

OPTIONS
  -l (--league)          Current league name (default: "TEMP")
```
