import math

from wraeblast.filtering import colors


def _isclose_many(t1: tuple[float, ...], t2: tuple[float, ...]):
    for i, fl in enumerate(t1):
        yield math.isclose(fl, t2[i])


def test_colormap():
    white = colors.Color("white")
    black = colors.Color("black")
    cm = colors.linear_colormap_from_color_list(
        "foo",
        [white, black],
    )
    vmax = 30_000

    assert colors.get_color_for_value(cm, 30_000, vmax) == black
    assert colors.get_color_for_value(cm, 35_000, vmax) == black
    assert colors.get_color_for_value(cm, 2_000, vmax, 5000) == white
    assert colors.get_color_for_value(cm, 7_000, vmax, 5000) == colors.Color(
        "#ebebeb"
    )
    assert colors.get_color_for_value(cm, 0, vmax) == white
    assert colors.get_color_for_value(cm, 20_000, vmax) == colors.Color("#555")


def test_color():
    assert colors.Color("chaos") == colors.Color("CHAOS")

    for c in colors.NamedColor:
        assert colors.Color(c.name).rgb == c.value.rgb

    assert all(
        _isclose_many(
            colors.Color.from_rgb_bytes((175, 96, 37)).rgb,
            (175 / 255, 96 / 255, 37 / 255),
        )
    )
