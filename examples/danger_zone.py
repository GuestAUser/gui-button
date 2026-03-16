#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk

from button_gen import DARK_BG, StyledButton


def main() -> None:
    root = tk.Tk()
    root.title("Danger Zone")
    root.configure(bg=DARK_BG)
    root.resizable(False, False)

    card = tk.Frame(root, bg="#111827", padx=24, pady=24)
    card.pack(padx=28, pady=28)

    tk.Label(card, text="Danger Zone", font=("Sans", 18, "bold"), fg="#f8fafc", bg="#111827").pack(anchor="w")
    tk.Label(card, text="A realistic two-step destructive flow.", font=("Sans", 10), fg="#94a3b8", bg="#111827").pack(anchor="w", pady=(4, 18))

    status = tk.StringVar(value="System protected")
    tk.Label(card, textvariable=status, font=("Sans", 10), fg="#cbd5e1", bg="#111827").pack(anchor="w", pady=(0, 18))

    armed = [False]

    def arm_system() -> None:
        armed[0] = not armed[0]
        if armed[0]:
            arm.text = "Disarm"
            arm.configure_style(style="warning")
            destroy.set_state("normal")
            destroy.pulse(count=1, ms=240)
            status.set("Destructive actions are armed")
        else:
            arm.text = "Arm"
            arm.configure_style(style="secondary")
            destroy.set_state("disabled")
            status.set("System protected")

    def finish_destroy() -> None:
        status.set("Environment removed")
        arm.set_state("disabled")
        destroy.text = "Deleted"
        destroy.configure_style(style="danger")
        destroy.set_state("disabled")

    def destroy_environment() -> None:
        if not armed[0]:
            destroy.shake()
            status.set("Arm the system before destroying it")
            return
        status.set("Destroying environment and revoking access...")
        arm.set_state("disabled")
        destroy.set_state("disabled")
        destroy.text = "Deleting..."
        root.after(1200, finish_destroy)

    row = tk.Frame(card, bg="#111827")
    row.pack()

    arm = StyledButton(row, "Arm", style="secondary", command=arm_system)
    arm.pack(side=tk.LEFT)

    destroy = StyledButton(row, "Destroy", style="danger", command=destroy_environment)
    destroy.pack(side=tk.LEFT, padx=(10, 0))
    destroy.set_state("disabled")

    root.mainloop()


if __name__ == "__main__":
    main()
