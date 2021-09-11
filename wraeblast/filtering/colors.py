import enum
import typing

import colorcet
import colormath.color_conversions
import colormath.color_diff
import colormath.color_objects
import colour
import matplotlib
import matplotlib.cm
import matplotlib.colors
import palettable
import palettable.palette


ColorType_RGB = tuple[float, float, float]
ColorType_RGBA = tuple[float, float, float, float]

_palettable_modules = (
    palettable.cartocolors.diverging,
    palettable.cartocolors.qualitative,
    palettable.cartocolors.sequential,
    palettable.cmocean.diverging,
    palettable.cmocean.sequential,
    palettable.colorbrewer.diverging,
    palettable.colorbrewer.qualitative,
    palettable.colorbrewer.sequential,
    palettable.lightbartlein.diverging,
    palettable.lightbartlein.sequential,
    palettable.matplotlib,
    palettable.mycarta,
    palettable.scientific.diverging,
    palettable.scientific.sequential,
    palettable.tableau,
    palettable.wesanderson,
)
_colormaps = {
    cm: getattr(matplotlib.cm, cm)
    for cm in matplotlib.cm.__builtin_cmaps  # type: ignore
} | colorcet.cm
for palettable_module in _palettable_modules:
    for name in dir(palettable_module):
        obj = getattr(palettable_module, name)
        if isinstance(obj, palettable.palette.Palette):
            _colormaps[name] = obj.mpl_colormap


def get_colormap_by_name(name: str) -> matplotlib.colors.Colormap:
    """Return a colormap by name.

    Supported colormaps are pulled from the matplotlib, palettable,
    and colorcet libraries.

    """
    return _colormaps[name]
    # try:
    #     return matplotlib.cm.get_cmap(name)
    # except ValueError:
    #     if name in dir(colorcet.cm):
    #         return getattr(colorcet.cm, name)
    #     else:
    #         for mod in _palettable_modules:
    #             if name in dir(mod):
    #                 return getattr(mod, name).mpl_colormap
    # raise ValueError(name)


def get_color_for_value(
    colormap: matplotlib.colors.Colormap,
    value: float,
    vmax: float,
    vmin: float = 1,
) -> "Color":
    """Return the color from a colormap for the given value."""
    norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
    rgba = colormap(norm(value))
    return Color(rgb=rgba[:3])


def get_nearest_color(target: "Color", candidates: list["Color"]) -> "Color":
    target_srgb = colormath.color_objects.sRGBColor(*target.rgb)
    candidates_srgb = [
        colormath.color_objects.sRGBColor(*c.rgb) for c in candidates
    ]

    target_lab = colormath.color_conversions.convert_color(
        target_srgb, colormath.color_objects.LabColor
    )
    candidates_lab = [
        colormath.color_conversions.convert_color(
            c, colormath.color_objects.LabColor
        )
        for c in candidates_srgb
    ]
    deltas = {
        i: colormath.color_diff.delta_e_cie2000(target_lab, c)
        for i, c in enumerate(candidates_lab)
    }
    return candidates[min(deltas, key=deltas.get)]  # type: ignore


def linear_colormap_from_color_list(
    name: str,
    colors: list["Color"],
) -> matplotlib.colors.Colormap:
    """Build a linear segmented colormap from a list of colors."""
    return matplotlib.colors.LinearSegmentedColormap.from_list(
        name=name,
        colors=[c.rgb for c in colors],
    )


class Color(colour.Color):
    """Represents a color."""

    alpha: float = 1

    def __init__(
        self,
        color: typing.Optional[
            typing.Union[
                colour.Color,
                ColorType_RGB,
                ColorType_RGBA,
                str,
            ]
        ] = None,
        *args,
        alpha: float = 1,
        **kwargs,
    ) -> None:
        if isinstance(color, tuple):
            alpha = float(color[3]) if len(color) == 4 else alpha
            super().__init__(rgb=color[:3], *args, **kwargs)
        elif (
            isinstance(color, str) and color.upper() in NamedColor.__members__
        ):
            super().__init__(NamedColor[color.upper()].value, *args, **kwargs)
        else:
            super().__init__(color=color, *args, **kwargs)
        self.__dict__["alpha"] = alpha

    @classmethod
    def from_rgb_bytes(cls, rgb: ColorType_RGB) -> "Color":
        """Create a color instance from the given RGB bytes."""
        return Color(rgb=ColorType_RGBA(c / 255 for c in rgb))

    @classmethod
    def from_rgba_bytes(cls, rgba: ColorType_RGBA) -> "Color":
        """Create a color instance from the given RGBA bytes."""
        rgba = ColorType_RGBA(c / 255 for c in rgba)
        alpha = rgba[3] if len(rgba) == 4 else 1
        return Color(rgb=rgba[:3], alpha=alpha)

    @property
    def rgb_as_bytes(self) -> ColorType_RGB:
        """Return an RGB tuple as bytes (range of 0-255)."""
        return ColorType_RGB(int(c * 255) for c in self.rgb)

    @property
    def rgba_as_bytes(self) -> ColorType_RGBA:
        """Return an RGBA tuple as bytes (range of 0-255)."""
        return ColorType_RGBA(self.rgb_as_bytes + (self.alpha * 255,))

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: typing.Any):
        try:
            return cls(v)
        except ValueError:
            raise


class NamedColor(enum.Enum):
    DEFAULT = Color.from_rgb_bytes((127, 127, 127))
    VALUEDEFAULT = Color.from_rgb_bytes((255, 255, 255))
    PINK = Color.from_rgb_bytes((255, 192, 203))
    DODGERBLUE = Color.from_rgb_bytes((30, 144, 255))
    FIRE = Color.from_rgb_bytes((150, 0, 0))
    COLD = Color.from_rgb_bytes((54, 100, 146))
    LIGHTNING = Color.from_rgb_bytes((255, 215, 0))
    CHAOS = Color.from_rgb_bytes((208, 32, 144))
    AUGMENTED = Color.from_rgb_bytes((136, 136, 255))
    CRAFTED = Color.from_rgb_bytes((184, 218, 242))
    UNMET = Color.from_rgb_bytes((210, 0, 0))
    UNIQUEITEM = Color.from_rgb_bytes((175, 96, 37))
    RAREITEM = Color.from_rgb_bytes((255, 255, 119))
    MAGICITEM = Color.from_rgb_bytes((136, 136, 255))
    WHITEITEM = Color.from_rgb_bytes((200, 200, 200))
    GEMITEM = Color.from_rgb_bytes((27, 162, 155))
    CURRENCYITEM = Color.from_rgb_bytes((170, 158, 130))
    QUESTITEM = Color.from_rgb_bytes((74, 230, 58))
    NEMESISMOD = Color.from_rgb_bytes((255, 200, 0))
    NEMESISMODOUTLINE = Color.from_rgba_bytes((255, 40, 0, 220))
    TITLE = Color.from_rgb_bytes((231, 180, 120))
    CORRUPTED = Color.from_rgb_bytes((210, 0, 0))
    FAVOUR = Color.from_rgb_bytes((170, 158, 130))
    SUPPORTERPACKNEWITEM = Color.from_rgb_bytes((180, 96, 0))
    SUPPORTERPACKITEM = Color.from_rgb_bytes((163, 141, 109))
    BLOODLINEMOD = Color.from_rgb_bytes((210, 0, 220))
    BLOODLINEMODOUTLINE = Color.from_rgba_bytes((74, 0, 160, 200))
    TORMENTMOD = Color.from_rgb_bytes((50, 230, 100))
    TORMENTMODOUTLINE = Color.from_rgba_bytes((0, 100, 150, 200))
    CANTTRADEORMODIFY = Color.from_rgb_bytes((210, 0, 0))
