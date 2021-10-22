"""Helpers available in the Jinja template environment."""
import functools
import math
import os
import pathlib
import re
import string
import typing

import backoff
import boto3
import botocore.exceptions
import matplotlib.colors
import pandas as pd
import pydub
import structlog

from wraeblast import constants, insights
from wraeblast.filtering import colors, elements


try:
    import pyttsx3

    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


logger = structlog.get_logger()

_valid_filename_chars = frozenset(
    f"-_.() {string.ascii_letters}{string.digits}"
)


def get_tts_bucket_name() -> str:
    return os.environ.get("WRAEBLAST_BUCKET_TTS", "wraeblast-tts")


@functools.cache
def list_tts_s3(
    bucket_name: typing.Optional[str] = None,
    prefix="",
) -> list[str]:
    if not bucket_name:
        bucket_name = get_tts_bucket_name()
    s3_client = boto3.client("s3")
    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
    object_names = []
    for page in pages:
        if not page["KeyCount"]:
            break
        for obj in page["Contents"]:
            object_names.append(obj["Key"])
    return object_names


def change_brightness(color: str, brightness: float) -> colors.Color:
    """Change the brightness (luminance) of the given color."""
    c = colors.Color(color)
    c.set_luminance(brightness)
    return c


@functools.cache
def colormap_pick(
    cmap_or_name: typing.Union[str, matplotlib.colors.Colormap],
    value: float,
    vmax: float,
    vmin: float = 1,
    log_scale: bool = True,
) -> colors.Color:
    """Get the individual color for a value from the given colormap."""
    if isinstance(cmap_or_name, str):
        cmap = colors.get_colormap_by_name(cmap_or_name)
    else:
        cmap = cmap_or_name
    if log_scale:
        value = math.log(value) if value > 0 else vmin
        vmin = math.log(vmin) if vmin > 0 else vmin
        vmax = math.log(vmax)
    return colors.get_color_for_value(
        colormap=cmap,
        value=value,
        vmax=vmax,
        vmin=vmin,
    )


# TODO: persistent lookup table of tags
def get_item_tags(row: pd.Series) -> list[str]:
    tags = []
    item_name = row.item_name.lower()
    for keyword in (
        "breachstone",
        "emblem",
        "fragment",
        "key",
        "sacrifice",
        "scarab",
        "simulacrum",
        "splinter",
        "vessel",
        "writ",
    ):
        if keyword in item_name:
            tags.append(keyword)

        breachlords = (
            "chayula",
            "tul",
            "uul-netol",
            "xoph",
        )
        if keyword in ("breachstone", "splinter"):
            for breachlord in breachlords:
                if breachlord in item_name:
                    tags += ["breach", f"breach:{breachlord}"]
                    break
    return tags


def get_stack_tags(
    stack_size: int,
    row: typing.Optional[pd.Series] = None,
    interval: int = 5,
) -> list[str]:
    tags = []
    if stack_size > 1:
        tags.append("stacks")
    for interval in range(
        interval, interval * (stack_size // interval) + 1, interval
    ):
        tags.append(f"stacks:{interval}")
    return tags


def get_quantile_threshold_tags(
    quantile: str,
    value: typing.Optional[int] = None,
    mask: bool = False,
) -> list[str]:
    if value is None:
        quantile, value = insights.get_quantile_tuple(quantile)
    if mask:
        start = 0
        end = value
    else:
        start = value
        end = insights.quantiles[quantile]
    quantiles = range(start, end)
    prefix = "QU" if quantile == "quintile" else quantile[0].upper()
    return [f"{prefix}{i}" for i in quantiles]


def nearest_named_color(
    cmap_or_name: typing.Union[str, matplotlib.colors.Colormap],
    value_or_threshold: typing.Union[str, float],
    vmax: float = 1,
    vmin: float = 0,
    log_scale: bool = True,
) -> str:
    if isinstance(value_or_threshold, str):
        if value_or_threshold.startswith("D"):
            value = 0.1 * (int(value_or_threshold[1:]) - 1)
        elif value_or_threshold.startswith("P"):
            value = 0.01 * (int(value_or_threshold[1:]) - 1)
        elif value_or_threshold.startswith("QU"):
            value = 0.2 * (int(value_or_threshold[2:]) - 1)
        elif value_or_threshold.startswith("Q"):
            value = 0.25 * (int(value_or_threshold[1:]) - 1)
        else:
            raise RuntimeError(f"invalid quantile: {value_or_threshold}")
        log_scale = False
    else:
        value = value_or_threshold
    target = colormap_pick(
        cmap_or_name,
        value,
        vmax=vmax,
        vmin=vmin,
        log_scale=log_scale,
    )
    candidates = [colors.Color(c.value) for c in elements.NamedColor]
    nearest_color = colors.get_nearest_color(target, candidates)
    return elements.NamedColor[str(nearest_color).upper()].value


def normalize_skill_gem_name(name: str) -> str:
    for alt_quality in constants.AltQuality:
        if name.startswith(alt_quality.value):
            return name[len(alt_quality.value) + 1 :]
    return name


def round_down(i: float, k: int) -> int:
    """Round down an integer."""
    return int(k * (i // k))


def slugify_filename(s: str) -> str:
    filename = "".join(c for c in s if c in _valid_filename_chars)
    filename = re.sub(r"[^\w\s-]", "", filename).strip().lower()
    filename = re.sub(r"[-\s]+", "-", filename)
    return filename


def text_color(
    color: typing.Union[colors.Color, str],
    lum_threshold: float = 0.5,
    dark_color: typing.Optional[colors.Color] = None,
    light_color: typing.Optional[colors.Color] = None,
    monochrome: bool = False,
    lum_shift: float = 0.6,
) -> colors.Color:
    """Get a contrasting color for the given color."""
    c = colors.Color(color)
    if c.luminance >= lum_threshold:
        if dark_color:
            return dark_color
        if monochrome:
            return colors.Color("black")
        lum = lum if (lum := c.get_luminance() - abs(lum_shift)) >= 0 else 0
    else:
        if light_color:
            return light_color
        if monochrome:
            return colors.Color("white")
        lum = lum if (lum := c.get_luminance() + abs(lum_shift)) <= 1 else 1.0
    c.set_luminance(lum)
    return c


def tts_pyttsx3(
    s: str,
    dest: pathlib.Path,
    volume: float = 1.0,
    rate: int = 200,
) -> None:
    engine = pyttsx3.init(driverName="espeak", debug=True)
    engine.setProperty("rate", rate)
    engine.setProperty("volume", volume)
    engine.save_to_file(s, str(dest))
    engine.runAndWait()


@backoff.on_exception(backoff.expo, botocore.exceptions.ClientError)
def tts_polly(
    s: str,
    key: str,
    dest: pathlib.Path,
    voice_id: str = "Aria",
    engine: str = "neural",
    sample_rate: int = 24_000,
    force_create: bool = False,
    volume: str = "x-loud",
) -> None:
    bucket_name = get_tts_bucket_name()
    objects = list_tts_s3()
    s3_client = boto3.client("s3")
    if not force_create and key in objects:
        logger.info("tts.downloading_cached", key=key)
        s3_client.download_file(bucket_name, key, str(dest))
        return
    else:
        logger.info("tts.generating", polly=True, key=key)
    polly_client = boto3.client("polly")
    response = polly_client.synthesize_speech(
        Engine=engine,
        OutputFormat="mp3",
        SampleRate=str(sample_rate),
        Text=f'<prosody volume="{volume}">{s}</prosody>',
        TextType="ssml",
        VoiceId=voice_id,
    )
    audio = response["AudioStream"].read()
    with dest.open("wb") as f:
        f.write(audio)
    response = s3_client.put_object(
        ACL="private",
        Body=audio,
        Bucket=bucket_name,
        Key=key,
    )


def tts(
    s: str,
    filename: typing.Optional[str] = None,
    output_path: str = "output",
    prefix: str = "FilterSounds/tts",
    overwrite: bool = False,
    volume: float = 1.0,
    rate: int = 200,
    volume_boost: int = 0,
    voice_id: str = "Aria",
) -> str:
    """Generate and save a text-to-speech sound clip to a file.

    If AWS credentials are present in the environment, Polly will be
    used instead of pyttsx3 to synthesize the given text.

    Args:
        s (str): The text to synthesize.
        filename (str, optional): Destination filename. By default,
            a slugified filename based on the input text is generated.
        output_path (str, optional): Output directory.
        prefix (str, optional): Directory to prefix filename with.
            Appended after output directory, and is also used for
            S3 key prefix.
        overwrite (bool, optional): If True, regenerates existing files.
            Defaults to False.
        volume (float, optional): Only used by pyttsx3. Controls media
            volume, in an accepted range of 0 to 1.0. Defaults to 1.0.
        rate (int, optional): Only used by pyttsx3. Controls rate of
            speech. Defaults to 200.
        volume_boost (int, optional): If non-zero, post-processes TTS
            files and increases their volume by the given value in dB.
            Note that when using AWS Polly, the post processing is only
            performed locally and not reflected in the S3 cache.
            Defaults to 0.
        voice_id (str, optional): AWS Polly voice ID. Defaults to
            *Aria*.

    Returns:
        str: The path to the generated TTS clip, relative to the filter.

    """
    aws_enabled = "AWS_ACCESS_KEY_ID" in os.environ
    if filename is None:
        filename = f"{slugify_filename(s)}.mp3"
        if aws_enabled:
            filename = str(pathlib.Path(voice_id) / filename)
    else:
        filename_path = pathlib.Path(filename)
        filename = str(
            filename_path.with_stem(slugify_filename(filename_path.stem))
        )

    filepath = pathlib.Path(output_path) / pathlib.Path(prefix) / filename
    if overwrite or not filepath.exists():
        filepath.parent.mkdir(parents=True, exist_ok=True)
        if aws_enabled:
            tts_polly(
                s=s,
                key=filename,
                dest=filepath,
                voice_id=voice_id,
            )
        elif "CI" not in os.environ:
            tts_pyttsx3(
                s=s,
                dest=filepath,
                volume=volume,
                rate=rate,
            )
        if "CI" not in os.environ and volume_boost:
            seg = pydub.AudioSegment.from_mp3(str(filepath))
            boosted_seg = seg + volume_boost  # type: ignore
            boosted_seg.export(filepath, format="mp3")

    return str(pathlib.Path(prefix) / filename)
