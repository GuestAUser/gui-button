#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk

from button_gen import DARK_BG, STYLES, ButtonState, Style, StyledButton

BG = DARK_BG
PANEL = "#111827"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"


def main() -> None:
    root = tk.Tk()
    root.title("Operations Workspace")
    root.configure(bg=BG)
    root.resizable(False, False)

    shell = tk.Frame(root, bg=BG, padx=24, pady=24)
    shell.pack()

    header = tk.Frame(shell, bg=BG)
    header.pack(fill=tk.X)
    tk.Label(header, text="Operations Workspace", font=("Sans", 22, "bold"), fg=TEXT, bg=BG).pack(anchor="w")
    tk.Label(header, text="A realistic control room for deployments, incidents, and runtime theming.", font=("Sans", 10), fg=MUTED, bg=BG).pack(anchor="w", pady=(4, 18))

    main_row = tk.Frame(shell, bg=BG)
    main_row.pack()

    left = tk.Frame(main_row, bg=PANEL, padx=18, pady=18)
    left.pack(side=tk.LEFT, anchor="n")
    right = tk.Frame(main_row, bg=PANEL, padx=18, pady=18)
    right.pack(side=tk.LEFT, padx=(16, 0), anchor="n")

    status = tk.StringVar(value="System nominal")
    timeline = tk.Listbox(left, width=48, height=14, bg="#0b1220", fg=TEXT, relief=tk.FLAT, highlightthickness=0)
    timeline.pack()

    def add_event(message: str) -> None:
        timeline.insert(tk.END, message)
        timeline.see(tk.END)
        status.set(message)

    def invoke_target() -> None:
        target.invoke()
        add_event("invoke() triggered")

    def disable_target() -> None:
        target.set_state(ButtonState.DISABLED)
        add_event("set_state('disabled')")

    def enable_target() -> None:
        target.set_state(ButtonState.NORMAL)
        add_event("set_state('normal')")

    def trigger_shake() -> None:
        target.shake()
        add_event("shake()")

    def trigger_bounce() -> None:
        target.bounce()
        add_event("bounce()")

    def trigger_pulse() -> None:
        target.pulse(count=1, ms=260)
        add_event("pulse()")

    def stop_effects() -> None:
        target.cancel_effects()
        add_event("cancel_effects()")

    def apply_preset(name: str) -> None:
        target.configure_style(style=name)
        add_event(f"configure_style(style={name!r})")

    def apply_custom_theme() -> None:
        target.configure_style(style=Style("#8b5cf6", "#ffffff", radius=20), pad_x=42, font_size=18)
        add_event("configure_style(custom Style, pad_x=42, font_size=18)")

    def clear_override() -> None:
        target.configure_style(style="primary", bg="", fg="", hover_bg="", active_bg="", radius=0, pad_x=32, font_size=16)
        add_event("configure_style(...cleared overrides...)")

    tk.Label(left, textvariable=status, font=("Sans", 10), fg=MUTED, bg=PANEL).pack(anchor="w", pady=(14, 0))

    section = tk.Frame(left, bg=PANEL)
    section.pack(fill=tk.X, pady=(16, 0))

    target = StyledButton(
        section,
        "Deploy Release",
        style="primary",
        font_size=16,
        pad_x=32,
        command=lambda: add_event("Deploy action executed"),
    )
    target.pack(anchor="w")
    target.bounce()

    api_group = tk.Frame(right, bg=PANEL)
    api_group.pack(fill=tk.X)
    tk.Label(api_group, text="Public API", font=("Sans", 14, "bold"), fg=TEXT, bg=PANEL).pack(anchor="w")

    control_row = tk.Frame(api_group, bg=PANEL)
    control_row.pack(anchor="w", pady=(12, 0))

    StyledButton(
        control_row,
        "Invoke",
        style="success",
        command=invoke_target,
    ).pack(side=tk.LEFT)

    StyledButton(
        control_row,
        "Disable",
        style="warning",
        command=disable_target,
    ).pack(side=tk.LEFT, padx=6)

    StyledButton(
        control_row,
        "Enable",
        style="secondary",
        command=enable_target,
    ).pack(side=tk.LEFT)

    effect_row = tk.Frame(api_group, bg=PANEL)
    effect_row.pack(anchor="w", pady=(10, 0))

    StyledButton(
        effect_row,
        "Shake",
        style="warning",
        command=trigger_shake,
    ).pack(side=tk.LEFT)
    StyledButton(
        effect_row,
        "Bounce",
        style="success",
        command=trigger_bounce,
    ).pack(side=tk.LEFT, padx=6)
    StyledButton(
        effect_row,
        "Pulse",
        style="primary",
        command=trigger_pulse,
    ).pack(side=tk.LEFT)
    StyledButton(
        effect_row,
        "Stop Effects",
        style="danger",
        command=stop_effects,
    ).pack(side=tk.LEFT, padx=(6, 0))

    tk.Label(right, text="Runtime Styling", font=("Sans", 14, "bold"), fg=TEXT, bg=PANEL).pack(anchor="w", pady=(18, 0))

    style_row = tk.Frame(right, bg=PANEL)
    style_row.pack(anchor="w", pady=(12, 0))
    for name in ("primary", "success", "warning", "danger", "light"):
        StyledButton(
            style_row,
            name.title(),
            style=name,
            font_size=10,
            pad_x=12,
            pad_y=8,
            command=lambda n=name: apply_preset(n),
        ).pack(side=tk.LEFT, padx=(0, 4))

    custom_row = tk.Frame(right, bg=PANEL)
    custom_row.pack(anchor="w", pady=(10, 0))

    StyledButton(
        custom_row,
        "Purple Theme",
        style=Style("#8b5cf6", "#ffffff", radius=20),
        font_size=10,
        command=apply_custom_theme,
    ).pack(side=tk.LEFT)

    StyledButton(
        custom_row,
        "Clear Override",
        style="secondary",
        font_size=10,
        command=clear_override,
    ).pack(side=tk.LEFT, padx=(6, 0))

    tk.Label(right, text="Live Use Cases", font=("Sans", 14, "bold"), fg=TEXT, bg=PANEL).pack(anchor="w", pady=(18, 0))

    flows = tk.Frame(right, bg=PANEL)
    flows.pack(anchor="w", pady=(12, 0))

    def run_release_flow() -> None:
        target.configure_style(style="warning")
        target.text = "Deploying..."
        target.set_state("disabled")
        add_event("Release flow started")

        def verify() -> None:
            target.configure_style(style="success")
            target.text = "Verifying"
            target.set_state("normal")
            target.invoke()
            add_event("Verification started via invoke()")

        def finish() -> None:
            target.text = "Release Live"
            target.pulse(count=1, ms=260)
            add_event("Release promoted")

        root.after(900, verify)
        root.after(1650, finish)

    def run_incident_flow() -> None:
        target.configure_style(style="danger")
        target.text = "Incident Mode"
        target.shake(intensity=8, ms=420)
        add_event("Incident declared; operator attention requested")

    StyledButton(flows, "Release Flow", style="success", command=run_release_flow).pack(side=tk.LEFT)
    StyledButton(flows, "Incident Flow", style="danger", command=run_incident_flow).pack(side=tk.LEFT, padx=6)

    for i, name in enumerate(("primary", "secondary", "success", "danger", "warning", "dark", "light")):
        root.after(250 + i * 90, lambda n=name: add_event(f"Preset available: {n}"))

    root.mainloop()


if __name__ == "__main__":
    main()
