#!/usr/bin/env python3
"""GUI button generator and embeddable tkinter widget.

CLI::

    python button_gen.py "Click Me"
    python button_gen.py "Submit" --style success --dark
    python button_gen.py "Delete" --style danger --action exit

Library::

    import tkinter as tk
    from button_gen import DARK_BG, StyledButton

    root = tk.Tk()
    root.configure(bg=DARK_BG)
    button = StyledButton(root, "Click Me", command=lambda: print("clicked"))
    button.pack(padx=20, pady=20)
    button.bounce()
    root.mainloop()
"""

from __future__ import annotations

import argparse
import math
import platform
import sys
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, Literal, TypeVar, cast

try:
    import tkinter as tk
    import tkinter.font as tkfont
    from tkinter import messagebox
except ImportError as exc:
    install_hint = (
        "tkinter is required. Install it:\n"
        "  Debian/Ubuntu:  sudo apt install python3-tk\n"
        "  Arch:           sudo pacman -S tk\n"
        "  macOS:          brew install python-tk\n"
        "  FreeBSD:        pkg install py311-tkinter"
    )
    raise ImportError(install_hint) from exc

_VERSION = "1.0.0"
LIGHT_BG = "#f1f5f9"
DARK_BG = "#0f172a"
_FRAME_MS = 16

_PLATFORM_FONTS: dict[str, str] = {
    "Darwin": "SF Pro Display",
    "Windows": "Segoe UI",
    "Linux": "Sans",
}


@dataclass(frozen=True, slots=True)
class Style:
    bg: str
    fg: str
    hover_bg: str = ""
    active_bg: str = ""
    radius: int = 12


@dataclass(frozen=True, slots=True)
class StateVisual:
    fill: str
    text_fill: str
    shadow_fill: str
    scale: float
    shadow_visible: bool


class ButtonState(str, Enum):
    NORMAL = "normal"
    HOVER = "hover"
    PRESSED = "pressed"
    DISABLED = "disabled"


STYLES: dict[str, Style] = {
    "primary": Style("#2563eb", "#ffffff"),
    "secondary": Style("#64748b", "#ffffff"),
    "success": Style("#16a34a", "#ffffff"),
    "danger": Style("#dc2626", "#ffffff"),
    "warning": Style("#d97706", "#ffffff"),
    "dark": Style("#1e293b", "#ffffff"),
    "light": Style("#e2e8f0", "#1e293b"),
}

_F = TypeVar("_F", bound=Callable[..., Any])


def _restartable_effect(name: str) -> Callable[[_F], _F]:
    def decorator(func: _F) -> _F:
        @wraps(func)
        def wrapper(self: StyledButton, *args: Any, **kwargs: Any) -> Any:
            self.cancel_effects(name)
            return func(self, *args, **kwargs)

        return cast(_F, wrapper)

    return decorator


def _darken(hex_color: str, factor: float = 0.85) -> str:
    value = hex_color.lstrip("#")
    if len(value) not in (3, 6) or not all(c in "0123456789abcdefABCDEF" for c in value):
        return hex_color
    if len(value) == 3:
        value = value[0] * 2 + value[1] * 2 + value[2] * 2
    red = min(max(int(int(value[0:2], 16) * factor), 0), 255)
    green = min(max(int(int(value[2:4], 16) * factor), 0), 255)
    blue = min(max(int(int(value[4:6], 16) * factor), 0), 255)
    return f"#{red:02x}{green:02x}{blue:02x}"


def _lerp(c1: str, c2: str, t: float) -> str:
    try:
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    except (ValueError, IndexError):
        return c2
    red = int(r1 + (r2 - r1) * t)
    green = int(g1 + (g2 - g1) * t)
    blue = int(b1 + (b2 - b1) * t)
    return f"#{red:02x}{green:02x}{blue:02x}"


def _ease_out_bounce(t: float) -> float:
    if t < 1 / 2.75:
        return 7.5625 * t * t
    if t < 2 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    if t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    t -= 2.625 / 2.75
    return 7.5625 * t * t + 0.984375


def _to_hex(widget: tk.Misc, color: str) -> str:
    try:
        red, green, blue = widget.winfo_rgb(color)
        return f"#{red >> 8:02x}{green >> 8:02x}{blue >> 8:02x}"
    except tk.TclError:
        return color


def _platform_font() -> str:
    return _PLATFORM_FONTS.get(platform.system(), "TkDefaultFont")


def _enable_dpi_awareness() -> None:
    if platform.system() != "Windows":
        return
    try:
        import ctypes  # noqa: PLC0415

        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # type: ignore[attr-defined]
    except (ImportError, AttributeError, OSError):
        pass


class AnimationCoordinator:
    def __init__(self, owner: StyledButton) -> None:
        self._owner = owner
        self._offsets: dict[str, tuple[float, float]] = {}
        self._scales: dict[str, float] = {}
        self._colors: dict[str, tuple[int, str]] = {}
        self._after_ids: dict[str, list[str]] = {}

    def schedule(self, effect: str, delay_ms: int, callback: Callable[[], None]) -> None:
        task_ids = self._after_ids.setdefault(effect, [])
        task_id = ""

        def runner() -> None:
            try:
                callback()
            finally:
                ids = self._after_ids.get(effect)
                if ids is not None:
                    try:
                        ids.remove(task_id)
                    except ValueError:
                        pass
                    if not ids:
                        self._after_ids.pop(effect, None)

        task_id = self._owner.after(delay_ms, runner)
        task_ids.append(task_id)

    def cancel(self, *effects: str) -> None:
        targets = effects or tuple(self._after_ids)
        for effect in targets:
            for task_id in self._after_ids.pop(effect, []):
                try:
                    self._owner.after_cancel(task_id)
                except (tk.TclError, ValueError):
                    pass

    def cancel_all(self) -> None:
        self.cancel(*tuple(self._after_ids))

    def set_offset(self, name: str, x: float, y: float, *, render: bool = True) -> None:
        self._offsets[name] = (x, y)
        if render:
            self._owner._render()

    def clear_offset(self, name: str, *, render: bool = True) -> None:
        if self._offsets.pop(name, None) is not None and render:
            self._owner._render()

    def total_offset(self) -> tuple[float, float]:
        dx = sum(value[0] for value in self._offsets.values())
        dy = sum(value[1] for value in self._offsets.values())
        return dx, dy

    def set_scale(self, name: str, scale: float, *, render: bool = True) -> None:
        self._scales[name] = scale
        if render:
            self._owner._render()

    def clear_scale(self, name: str, *, render: bool = True) -> None:
        if self._scales.pop(name, None) is not None and render:
            self._owner._render()

    def total_scale(self) -> float:
        scale = 1.0
        for value in self._scales.values():
            scale *= value
        return scale

    def set_color(self, name: str, color: str, priority: int, *, render: bool = True) -> None:
        self._colors[name] = (priority, color)
        if render:
            self._owner._render()

    def clear_color(self, name: str, *, render: bool = True) -> None:
        if self._colors.pop(name, None) is not None and render:
            self._owner._render()

    def resolve_fill(self, fallback: str) -> str:
        if not self._colors:
            return fallback
        _, color = max(self._colors.values(), key=lambda item: item[0])
        return color


class StyledButton(tk.Canvas):
    """Canvas-backed interactive button with animations and a formal state model.

    Public methods intentionally mirror button-like behavior while adding motion
    effects and runtime style updates.
    """

    _SHADOW_DX = 3
    _SHADOW_DY = 4
    _PRESS_SHIFT = 2
    _ANIM_PAD = 8
    _PULSE_PRIORITY = 20

    def __init__(
        self,
        parent: tk.Misc,
        text: str = "",
        *,
        command: Callable[[], None] | None = None,
        style: str | Style = "primary",
        bg: str = "",
        fg: str = "",
        hover_bg: str = "",
        active_bg: str = "",
        font_family: str = "",
        font_size: int = 14,
        radius: int = 0,
        pad_x: int = 28,
        pad_y: int = 12,
        shadow: bool = True,
        animate: bool = True,
        ripple: bool = True,
    ) -> None:
        self._text_value = text
        self._command = command
        self._font_family = font_family or _platform_font()
        self._font_size = font_size
        self._radius = radius or self._resolve_style(style).radius
        self._pad_x = pad_x
        self._pad_y = pad_y
        self._has_shadow = shadow
        self._do_animate = animate
        self._do_ripple = ripple
        self._pointer_inside = False
        self._press_origin: Literal["mouse", "keyboard", "programmatic", None] = None
        self._state = ButtonState.NORMAL
        self._effect_items: dict[str, list[int]] = {}
        self._base_style = self._resolve_style(style)
        self._style_overrides: dict[str, object] = {}
        if bg:
            self._style_overrides["bg"] = bg
        if fg:
            self._style_overrides["fg"] = fg
        if hover_bg:
            self._style_overrides["hover_bg"] = hover_bg
        if active_bg:
            self._style_overrides["active_bg"] = active_bg
        if radius:
            self._style_overrides["radius"] = radius

        canvas_bg = self._resolve_parent_bg(parent)
        self._canvas_bg_hex = _to_hex(parent, canvas_bg)

        self._font = tkfont.Font(
            family=self._font_family,
            size=self._font_size,
            weight="bold",
        )
        self._cw = 0
        self._ch = 0
        self._min_cw = 0
        self._min_ch = 0
        self._remeasure_text(text)

        super().__init__(
            parent,
            width=self._canvas_width(),
            height=self._canvas_height(),
            bg=canvas_bg,
            highlightthickness=2,
            highlightbackground=canvas_bg,
            highlightcolor="#3b82f6",
            borderwidth=0,
            takefocus=True,
            cursor="hand2",
        )

        self._bg = self._base_style.bg
        self._fg = self._base_style.fg
        self._hover_bg = self._base_style.hover_bg
        self._active_bg = self._base_style.active_bg

        self._coordinator = AnimationCoordinator(self)
        self._render_cache: dict[str, object] = {}

        self._shadow_id: int | None = None
        if self._has_shadow:
            self._shadow_id = self.create_polygon(0, 0, 0, 0, smooth=True, width=0)
        self._rect_id = self.create_polygon(0, 0, 0, 0, smooth=True, width=0)
        self._text_id = self.create_text(0, 0, text=text, font=self._font)

        self._apply_style_values()
        self._rebuild_palette()
        self._transition_to(ButtonState.NORMAL, force=True)
        self._bind_events()

    def _resolve_style(self, style: str | Style) -> Style:
        return STYLES.get(style, STYLES["primary"]) if isinstance(style, str) else style

    def _resolve_parent_bg(self, parent: tk.Misc) -> str:
        try:
            return str(parent.cget("bg"))
        except tk.TclError:
            return LIGHT_BG

    def _canvas_width(self) -> int:
        shadow_x = self._SHADOW_DX if self._has_shadow else 0
        return self._cw + shadow_x + 2 * self._ANIM_PAD

    def _canvas_height(self) -> int:
        shadow_y = self._SHADOW_DY if self._has_shadow else 0
        return self._ch + shadow_y + 2 * self._ANIM_PAD

    def _content_box(self, *, scale: float, dx: float, dy: float) -> tuple[float, float, float, float]:
        pad = self._ANIM_PAD
        cx = pad + self._cw / 2 + dx
        cy = pad + self._ch / 2 + dy
        hw = self._cw * scale / 2
        hh = self._ch * scale / 2
        return cx - hw, cy - hh, cx + hw, cy + hh

    def _rounded_points(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        radius: int,
    ) -> list[float]:
        radius = min(radius, int((x2 - x1) / 2), int((y2 - y1) / 2))
        return [
            x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
        ]

    def _bind_events(self) -> None:
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_pointer_press)
        self.bind("<ButtonRelease-1>", self._on_pointer_release)
        self.bind("<KeyPress-Return>", self._on_key_press)
        self.bind("<KeyRelease-Return>", self._on_key_release)
        self.bind("<KeyPress-space>", self._on_key_press)
        self.bind("<KeyRelease-space>", self._on_key_release)

    def _remeasure_text(self, text: str) -> None:
        text_width = int(self._font.measure(text)) if text else 40
        text_height = int(self._font.metrics("linespace"))
        content_width = text_width + 2 * self._pad_x
        content_height = text_height + 2 * self._pad_y
        if not self._min_cw:
            self._min_cw = content_width
            self._min_ch = content_height
        self._cw = max(content_width, self._min_cw)
        self._ch = max(content_height, self._min_ch)

    def _apply_style_values(self) -> None:
        self._bg = cast(str, self._style_overrides.get("bg", self._base_style.bg))
        self._fg = cast(str, self._style_overrides.get("fg", self._base_style.fg))
        self._hover_bg = cast(str, self._style_overrides.get("hover_bg", self._base_style.hover_bg))
        self._active_bg = cast(str, self._style_overrides.get("active_bg", self._base_style.active_bg))
        self._radius = cast(int, self._style_overrides.get("radius", self._base_style.radius))

    def _rebuild_palette(self) -> None:
        self._bg_hex = _to_hex(self, self._bg)
        self._text_fill = _to_hex(self, self._fg)
        self._hover_fill = self._hover_bg or _darken(self._bg_hex, 0.78)
        self._pressed_fill = self._active_bg or _darken(self._bg_hex, 0.58)
        self._disabled_fill = _lerp(self._bg_hex, self._canvas_bg_hex, 0.45)
        self._disabled_text_fill = _lerp(self._text_fill, self._canvas_bg_hex, 0.40)
        self._shadow_fill = _darken(self._canvas_bg_hex, 0.55)
        self._disabled_shadow_fill = _lerp(self._shadow_fill, self._canvas_bg_hex, 0.55)

    def _visual_for_state(self, state: ButtonState) -> StateVisual:
        if state is ButtonState.HOVER:
            return StateVisual(self._hover_fill, self._text_fill, self._shadow_fill, 1.01, self._has_shadow)
        if state is ButtonState.PRESSED:
            return StateVisual(self._pressed_fill, self._text_fill, self._shadow_fill, 0.98, False)
        if state is ButtonState.DISABLED:
            return StateVisual(
                self._disabled_fill,
                self._disabled_text_fill,
                self._disabled_shadow_fill,
                1.0,
                self._has_shadow,
            )
        return StateVisual(self._bg_hex, self._text_fill, self._shadow_fill, 1.0, self._has_shadow)

    def _render(self, *, force: bool = False) -> None:
        visual = self._visual_for_state(self._state)
        dx, dy = self._coordinator.total_offset()
        scale = visual.scale * self._coordinator.total_scale()
        fill = self._coordinator.resolve_fill(visual.fill)

        x1, y1, x2, y2 = self._content_box(scale=scale, dx=dx, dy=dy)
        rect_points = tuple(self._rounded_points(x1, y1, x2, y2, self._radius))
        text_coords = (self._ANIM_PAD + self._cw / 2 + dx, self._ANIM_PAD + self._ch / 2 + dy)

        if force or self._render_cache.get("rect_points") != rect_points:
            self.coords(self._rect_id, *rect_points)
            self._render_cache["rect_points"] = rect_points
        if force or self._render_cache.get("rect_fill") != fill:
            self.itemconfigure(self._rect_id, fill=fill)
            self._render_cache["rect_fill"] = fill
        if force or self._render_cache.get("text_coords") != text_coords:
            self.coords(self._text_id, *text_coords)
            self._render_cache["text_coords"] = text_coords
        if force or self._render_cache.get("text_fill") != visual.text_fill:
            self.itemconfigure(self._text_id, fill=visual.text_fill)
            self._render_cache["text_fill"] = visual.text_fill

        if self._shadow_id is not None:
            if visual.shadow_visible:
                shadow_points = tuple(
                    self._rounded_points(
                        x1 + self._SHADOW_DX,
                        y1 + self._SHADOW_DY,
                        x2 + self._SHADOW_DX,
                        y2 + self._SHADOW_DY,
                        self._radius,
                    )
                )
                if force or self._render_cache.get("shadow_points") != shadow_points:
                    self.coords(self._shadow_id, *shadow_points)
                    self._render_cache["shadow_points"] = shadow_points
                if force or self._render_cache.get("shadow_fill") != visual.shadow_fill:
                    self.itemconfigure(self._shadow_id, fill=visual.shadow_fill)
                    self._render_cache["shadow_fill"] = visual.shadow_fill
                if force or self._render_cache.get("shadow_state") != "normal":
                    self.itemconfigure(self._shadow_id, state="normal")
                    self.tag_lower(self._shadow_id)
                    self._render_cache["shadow_state"] = "normal"
            elif force or self._render_cache.get("shadow_state") != "hidden":
                self.itemconfigure(self._shadow_id, state="hidden")
                self._render_cache["shadow_state"] = "hidden"

        self.tag_raise(self._text_id)

    def _transition_to(self, target: ButtonState, *, force: bool = False) -> None:
        if target is self._state and not force:
            return
        previous = self._state
        previous_visual = self._visual_for_state(previous)
        self._exit_state(previous, target)
        self._state = target
        self._enter_state(previous, target)
        self._animate_state_transition(previous_visual, self._visual_for_state(target), force=force)
        self._render()

    def _exit_state(self, previous: ButtonState, target: ButtonState) -> None:
        if previous is ButtonState.PRESSED:
            self._coordinator.clear_offset("state_press", render=False)

    def _enter_state(self, previous: ButtonState, target: ButtonState) -> None:
        if target is ButtonState.PRESSED:
            self._coordinator.set_offset(
                "state_press",
                self._PRESS_SHIFT,
                self._PRESS_SHIFT,
                render=False,
            )
        elif target is ButtonState.DISABLED:
            self._press_origin = None
            self.cancel_effects("invoke")
            try:
                self.grab_release()
            except tk.TclError:
                pass
        self.configure(cursor="arrow" if target is ButtonState.DISABLED else "hand2")

    def _animate_state_transition(
        self,
        previous_visual: StateVisual,
        target_visual: StateVisual,
        *,
        force: bool = False,
    ) -> None:
        self.cancel_effects("state_transition")
        if force or not self._do_animate:
            return
        if (
            previous_visual.fill == target_visual.fill
            and abs(previous_visual.scale - target_visual.scale) < 1e-6
        ):
            return

        target_scale = target_visual.scale or 1.0

        def on_step(t: float) -> None:
            eased = 1 - (1 - t) ** 3
            fill = _lerp(previous_visual.fill, target_visual.fill, eased)
            scale = previous_visual.scale + (target_visual.scale - previous_visual.scale) * eased
            self._coordinator.set_color("state_transition", fill, 5, render=False)
            self._coordinator.set_scale("state_transition", scale / target_scale, render=False)
            self._render()

        def on_complete() -> None:
            self._coordinator.clear_color("state_transition", render=False)
            self._coordinator.clear_scale("state_transition", render=False)
            self._render()

        self._animate("state_transition", 110, on_step, on_complete)

    def _animate(
        self,
        effect: str,
        duration_ms: int,
        on_step: Callable[[float], None],
        on_complete: Callable[[], None] | None = None,
    ) -> None:
        if not self._do_animate:
            on_step(1.0)
            if on_complete is not None:
                on_complete()
            return
        steps = max(1, math.ceil(duration_ms / _FRAME_MS))
        for index in range(steps + 1):
            t = index / steps
            delay = round(index * duration_ms / steps)
            self._coordinator.schedule(effect, delay, lambda t=t: on_step(t))
        if on_complete is not None:
            self._coordinator.schedule(effect, duration_ms + 1, on_complete)

    def _contains(self, x: int, y: int) -> bool:
        pad = self._ANIM_PAD
        return pad <= x <= pad + self._cw and pad <= y <= pad + self._ch

    def _center_point(self) -> tuple[int, int]:
        pad = self._ANIM_PAD
        return pad + self._cw // 2, pad + self._ch // 2

    def _release_to_resting_state(self) -> None:
        target = ButtonState.HOVER if self._pointer_inside else ButtonState.NORMAL
        self._transition_to(target)

    def _fire(self, x: int | None = None, y: int | None = None) -> None:
        if self._state is ButtonState.DISABLED:
            return
        if self._do_ripple:
            self.ripple(x=x, y=y)
        if self._command is not None:
            self._command()

    def _on_enter(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        if self._state is ButtonState.DISABLED:
            return
        self._pointer_inside = True
        if self._press_origin == "mouse":
            self._transition_to(ButtonState.PRESSED)
        elif self._state is ButtonState.NORMAL:
            self._transition_to(ButtonState.HOVER)

    def _on_leave(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        if self._state is ButtonState.DISABLED:
            return
        self._pointer_inside = False
        if self._press_origin == "mouse":
            self._transition_to(ButtonState.NORMAL)
        elif self._state is ButtonState.HOVER:
            self._transition_to(ButtonState.NORMAL)

    def _on_pointer_press(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        if self._state is ButtonState.DISABLED or self._press_origin is not None:
            return
        self.focus_set()
        self._press_origin = "mouse"
        self._transition_to(ButtonState.PRESSED)
        try:
            self.grab_set()
        except tk.TclError:
            pass

    def _on_pointer_release(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        if self._press_origin != "mouse":
            return
        self._press_origin = None
        try:
            self.grab_release()
        except tk.TclError:
            pass
        triggered = self._contains(event.x, event.y)
        self._pointer_inside = triggered
        self._release_to_resting_state()
        if triggered:
            self._fire(event.x, event.y)

    def _on_key_press(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        if self._state is ButtonState.DISABLED or self._press_origin is not None:
            return
        self._press_origin = "keyboard"
        self._transition_to(ButtonState.PRESSED)

    def _on_key_release(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        if self._press_origin != "keyboard":
            return
        self._press_origin = None
        x, y = self._center_point()
        self._release_to_resting_state()
        self._fire(x, y)

    def invoke(self) -> None:
        """Trigger the button programmatically with full visual feedback.

        The method mirrors pointer and keyboard activation: it enters the
        pressed state briefly, then runs the command and ripple effect.
        """
        if self._state is ButtonState.DISABLED or self._press_origin is not None:
            return
        self.cancel_effects("invoke")
        self._press_origin = "programmatic"
        self._transition_to(ButtonState.PRESSED)

        def complete_invoke() -> None:
            if self._press_origin != "programmatic":
                return
            self._press_origin = None
            x, y = self._center_point()
            self._release_to_resting_state()
            self._fire(x, y)

        if not self._do_animate:
            complete_invoke()
            return
        self._coordinator.schedule("invoke", 90, complete_invoke)

    def set_state(self, state: str | ButtonState) -> None:
        """Set the widget state.

        Args:
            state: One of ``normal``, ``hover``, ``pressed``, or ``disabled``.

        Raises:
            ValueError: If ``state`` is not a valid button state.
        """
        try:
            target = state if isinstance(state, ButtonState) else ButtonState(state)
        except ValueError as exc:
            valid = ", ".join(member.value for member in ButtonState)
            raise ValueError(f"invalid state {state!r}; expected one of: {valid}") from exc

        if target is ButtonState.DISABLED:
            self.cancel_effects()
            self._pointer_inside = False
        self._transition_to(target)

    def configure_style(self, **kwargs: object) -> None:
        """Update widget styling at runtime.

        Supported keys are ``style``, ``bg``, ``fg``, ``hover_bg``,
        ``active_bg``, ``font_family``, ``font_size``, ``radius``, ``pad_x``,
        ``pad_y``, ``shadow``, ``animate``, and ``ripple``. Passing ``""`` for
        a color override or ``0`` for ``radius`` clears that override and falls
        back to the active preset style.

        Raises:
            ValueError: If an unknown key is supplied.
        """
        allowed = {
            "style",
            "bg",
            "fg",
            "hover_bg",
            "active_bg",
            "font_family",
            "font_size",
            "radius",
            "pad_x",
            "pad_y",
            "shadow",
            "animate",
            "ripple",
        }
        unknown = sorted(set(kwargs) - allowed)
        if unknown:
            raise ValueError(f"unknown style keys: {', '.join(unknown)}")

        style = self._base_style
        if "style" in kwargs:
            style = self._resolve_style(cast(str | Style, kwargs["style"]))
            self._base_style = style

        for key in ("bg", "fg", "hover_bg", "active_bg"):
            if key not in kwargs:
                continue
            value = cast(str, kwargs[key])
            if value == "":
                self._style_overrides.pop(key, None)
            else:
                self._style_overrides[key] = value

        if "radius" in kwargs:
            value = cast(int, kwargs["radius"])
            if value == 0:
                self._style_overrides.pop("radius", None)
            else:
                self._style_overrides["radius"] = value

        if "font_family" in kwargs:
            self._font_family = cast(str, kwargs["font_family"]) or _platform_font()
        if "font_size" in kwargs:
            self._font_size = cast(int, kwargs["font_size"])
        if "pad_x" in kwargs:
            self._pad_x = cast(int, kwargs["pad_x"])
        if "pad_y" in kwargs:
            self._pad_y = cast(int, kwargs["pad_y"])
        if "shadow" in kwargs:
            self._has_shadow = cast(bool, kwargs["shadow"])
        if "animate" in kwargs:
            self._do_animate = cast(bool, kwargs["animate"])
        if "ripple" in kwargs:
            self._do_ripple = cast(bool, kwargs["ripple"])

        self._font = tkfont.Font(
            family=self._font_family,
            size=self._font_size,
            weight="bold",
        )
        self.itemconfigure(self._text_id, font=self._font)

        self._apply_style_values()
        self._remeasure_text(self._text_value)
        self.configure(width=self._canvas_width(), height=self._canvas_height())

        if self._has_shadow and self._shadow_id is None:
            self._shadow_id = self.create_polygon(0, 0, 0, 0, smooth=True, width=0)
        if not self._has_shadow and self._shadow_id is not None:
            self.delete(self._shadow_id)
            self._shadow_id = None

        self._rebuild_palette()
        self._render(force=True)

    def cancel_effects(self, *effects: str) -> None:
        """Cancel scheduled animations and transient effect layers.

        Args:
            *effects: Optional effect names. If omitted, all effects are
                cancelled and all temporary layers are cleared.
        """
        targets = effects or (
            "state_transition",
            "shake",
            "bounce",
            "pulse",
            "ripple",
            "invoke",
        )
        self._coordinator.cancel(*targets)
        for effect in targets:
            self._coordinator.clear_offset(effect, render=False)
            self._coordinator.clear_scale(effect, render=False)
            self._coordinator.clear_color(effect, render=False)
            for item_id in self._effect_items.pop(effect, []):
                try:
                    self.delete(item_id)
                except tk.TclError:
                    pass
        self._render()

    @_restartable_effect("shake")
    def shake(self, intensity: int = 6, ms: int = 400) -> None:
        """Run a damped horizontal shake animation.

        Args:
            intensity: Maximum horizontal travel in pixels.
            ms: Total animation duration in milliseconds.
        """

        def on_step(t: float) -> None:
            dx = math.sin(t * math.pi * 4) * intensity * (1 - t)
            self._coordinator.set_offset("shake", dx, 0.0)

        def on_complete() -> None:
            self._coordinator.clear_offset("shake")

        self._animate("shake", ms, on_step, on_complete)

    @_restartable_effect("bounce")
    def bounce(self, height: int = 12, ms: int = 500) -> None:
        """Run a vertical entrance bounce.

        Args:
            height: Peak bounce height in pixels.
            ms: Total animation duration in milliseconds.
        """

        def on_step(t: float) -> None:
            dy = -height * (1 - _ease_out_bounce(t))
            self._coordinator.set_offset("bounce", 0.0, dy)

        def on_complete() -> None:
            self._coordinator.clear_offset("bounce")

        self._animate("bounce", ms, on_step, on_complete)

    @_restartable_effect("pulse")
    def pulse(self, count: int = 2, ms: int = 700) -> None:
        """Flash the button with a temporary color and scale pulse.

        Args:
            count: Number of pulse beats.
            ms: Total animation duration in milliseconds.
        """

        def on_step(t: float) -> None:
            current_base = self._visual_for_state(self._state).fill
            wave = math.sin(t * math.pi * count)
            amount = max(wave, 0.0) * 0.28
            self._coordinator.set_color(
                "pulse",
                _lerp(current_base, "#ffffff", amount),
                self._PULSE_PRIORITY,
            )
            self._coordinator.set_scale("pulse", 1.0 + max(wave, 0.0) * 0.035)

        def on_complete() -> None:
            self._coordinator.clear_color("pulse", render=False)
            self._coordinator.clear_scale("pulse", render=False)
            self._render()

        self._animate("pulse", ms, on_step, on_complete)

    @_restartable_effect("ripple")
    def ripple(self, x: int | None = None, y: int | None = None, ms: int = 350) -> None:
        """Run a ripple highlight from a point inside the button.

        Args:
            x: X coordinate relative to the widget. Defaults to the center.
            y: Y coordinate relative to the widget. Defaults to the center.
            ms: Total ripple duration in milliseconds.
        """
        center_x, center_y = self._center_point()
        cx = center_x if x is None else x
        cy = center_y if y is None else y
        base_fill = self._coordinator.resolve_fill(self._visual_for_state(self._state).fill)
        ripple_fill = _lerp(base_fill, "#ffffff", 0.35)
        item_id = self.create_oval(cx, cy, cx, cy, fill=ripple_fill, outline="")
        self._effect_items.setdefault("ripple", []).append(item_id)
        self.tag_raise(self._text_id)
        max_radius = int(max(self._cw, self._ch) * 0.72)

        def on_step(t: float) -> None:
            radius = int(max_radius * t)
            fill = _lerp(ripple_fill, base_fill, t)
            try:
                self.coords(item_id, cx - radius, cy - radius, cx + radius, cy + radius)
                self.itemconfigure(item_id, fill=fill)
            except tk.TclError:
                return
            self.tag_raise(self._text_id)

        def on_complete() -> None:
            try:
                self.delete(item_id)
            except tk.TclError:
                pass
            self._effect_items.pop("ripple", None)

        self._animate("ripple", ms, on_step, on_complete)

    @property
    def text(self) -> str:
        return self._text_value

    @text.setter
    def text(self, value: str) -> None:
        self._text_value = value
        self.itemconfigure(self._text_id, text=value)
        self._remeasure_text(value)
        self.configure(width=self._canvas_width(), height=self._canvas_height())
        self._render(force=True)

    def destroy(self) -> None:
        self.cancel_effects()
        super().destroy()


class ButtonApp:
    def __init__(
        self,
        text: str,
        *,
        style: str = "primary",
        bg: str = "",
        fg: str = "",
        font_family: str = "",
        font_size: int = 14,
        title: str = "",
        action: str = "print",
        dark: bool = False,
    ) -> None:
        self._text = text
        self._action = action
        self._clicks = 0
        window_bg = DARK_BG if dark else LIGHT_BG

        _enable_dpi_awareness()
        self._root = tk.Tk()
        self._root.title(title or text)
        self._root.configure(bg=window_bg)
        self._root.minsize(220, 120)
        self._root.protocol("WM_DELETE_WINDOW", self._quit)

        self._button = StyledButton(
            self._root,
            text,
            style=style,
            bg=bg,
            fg=fg,
            font_family=font_family,
            font_size=font_size,
            command=self._on_click,
        )
        self._button.pack(expand=True, padx=40, pady=40)
        self._center()
        self._button.bounce()

    def _on_click(self) -> None:
        self._clicks += 1
        if self._action == "print":
            print(f"[click {self._clicks}] {self._text}")
        elif self._action == "exit":
            self._quit()
        elif self._action == "notify":
            messagebox.showinfo("Clicked", f"{self._text}\n(click #{self._clicks})")
        elif self._action == "count":
            self._button.text = f"{self._text} ({self._clicks})"
            self._button.pulse(count=1, ms=240)

    def _center(self) -> None:
        self._root.update_idletasks()
        width = self._root.winfo_reqwidth()
        height = self._root.winfo_reqheight()
        x = (self._root.winfo_screenwidth() - width) // 2
        y = (self._root.winfo_screenheight() - height) // 2
        self._root.geometry(f"{width}x{height}+{x}+{y}")

    def _quit(self) -> None:
        self._root.destroy()

    def run(self) -> None:
        self._root.mainloop()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="button_gen",
        description="Generate a GUI button from the command line.",
        epilog=(
            "examples:\n"
            '  %(prog)s "Click Me"\n'
            '  %(prog)s "Submit" --style success --dark\n'
            '  %(prog)s "Delete" --style danger --action exit\n'
            '  %(prog)s "Count"  --action count --font-size 20'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("text", help="label displayed on the button")

    appearance = parser.add_argument_group("appearance")
    appearance.add_argument(
        "--style",
        choices=list(STYLES),
        default="primary",
        help="preset style (default: %(default)s)",
    )
    appearance.add_argument("--bg", default="", metavar="COLOR", help="override background colour")
    appearance.add_argument("--fg", default="", metavar="COLOR", help="override text colour")
    appearance.add_argument("--dark", action="store_true", help="use dark window theme")

    typography = parser.add_argument_group("typography")
    typography.add_argument(
        "--font-family",
        default="",
        metavar="FONT",
        help="font family (default: platform-specific)",
    )
    typography.add_argument(
        "--font-size",
        type=int,
        default=14,
        metavar="PT",
        help="font size in points (default: %(default)s)",
    )

    layout = parser.add_argument_group("layout")
    layout.add_argument("--title", default="", metavar="TEXT", help="window title (default: button text)")

    behaviour = parser.add_argument_group("behaviour")
    behaviour.add_argument(
        "--action",
        choices=("print", "exit", "notify", "count"),
        default="print",
        help="click action (default: %(default)s)",
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {_VERSION}")
    return parser


def _validate(args: argparse.Namespace) -> list[str]:
    errors: list[str] = []
    if not args.text.strip():
        errors.append("button text must not be empty or whitespace-only")
    if not 8 <= args.font_size <= 72:
        errors.append(f"--font-size must be 8-72, got {args.font_size}")
    return errors


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    errors = _validate(args)
    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        return 1

    try:
        app = ButtonApp(
            args.text,
            style=args.style,
            bg=args.bg,
            fg=args.fg,
            font_family=args.font_family,
            font_size=args.font_size,
            title=args.title,
            action=args.action,
            dark=args.dark,
        )
        app.run()
    except tk.TclError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
