#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk

from button_gen import DARK_BG, StyledButton


def main() -> None:
    root = tk.Tk()
    root.title("Deploy Console")
    root.configure(bg=DARK_BG)
    root.resizable(False, False)

    shell = tk.Frame(root, bg=DARK_BG, padx=24, pady=24)
    shell.pack()

    tk.Label(shell, text="Deploy Console", font=("Sans", 18, "bold"), fg="#f8fafc", bg=DARK_BG).pack(anchor="w")
    tk.Label(shell, text="Promote a build, verify it, or roll it back.", font=("Sans", 10), fg="#94a3b8", bg=DARK_BG).pack(anchor="w", pady=(4, 16))

    log_box = tk.Listbox(shell, width=58, height=10, bg="#111827", fg="#e2e8f0", relief=tk.FLAT, highlightthickness=0)
    log_box.pack(fill=tk.BOTH)

    status = tk.StringVar(value="Idle")
    tk.Label(shell, textvariable=status, font=("Sans", 10), fg="#cbd5e1", bg=DARK_BG).pack(anchor="w", pady=(12, 0))

    controls = tk.Frame(shell, bg=DARK_BG)
    controls.pack(fill=tk.X, pady=(16, 0))

    deployed = [False]

    def write_log(message: str) -> None:
        log_box.insert(tk.END, message)
        log_box.see(tk.END)

    def set_busy(active: bool) -> None:
        deploy.set_state("disabled" if active else "normal")
        verify.set_state("disabled" if active else ("normal" if deployed[0] else "disabled"))
        rollback.set_state("disabled" if active else ("normal" if deployed[0] else "disabled"))

    def finish_verify() -> None:
        status.set("Verification passed")
        write_log("Health checks passed across all nodes")
        verify.configure_style(style="success")
        verify.pulse(count=1, ms=240)
        deploy.configure_style(style="success")
        set_busy(False)

    def run_verify() -> None:
        status.set("Running post-deploy verification...")
        write_log("Running smoke tests, tracing, and readiness checks")
        verify.configure_style(style="warning")
        set_busy(True)
        root.after(850, finish_verify)

    def finish_deploy() -> None:
        deployed[0] = True
        status.set("Deploy complete")
        write_log("Build promoted to production")
        deploy.configure_style(style="success")
        verify.set_state("normal")
        rollback.set_state("normal")
        root.after(250, verify.invoke)

    def run_deploy() -> None:
        status.set("Shipping build 2026.03.16...")
        write_log("Packaging release, uploading assets, draining workers")
        deploy.configure_style(style="warning")
        deploy.text = "Deploying..."
        set_busy(True)
        root.after(950, finish_deploy)

    def finish_rollback() -> None:
        deployed[0] = False
        status.set("Rollback complete")
        write_log("Production reverted to previous stable release")
        deploy.configure_style(style="primary")
        deploy.text = "Deploy"
        verify.configure_style(style="secondary")
        rollback.configure_style(style="secondary")
        set_busy(False)

    def run_rollback() -> None:
        if not deployed[0]:
            rollback.shake()
            status.set("Nothing to roll back")
            return
        status.set("Rolling back deployment...")
        write_log("Restoring previous release and reloading workers")
        rollback.configure_style(style="danger")
        set_busy(True)
        root.after(850, finish_rollback)

    deploy = StyledButton(controls, "Deploy", style="primary", command=run_deploy)
    deploy.pack(side=tk.LEFT)

    verify = StyledButton(controls, "Verify", style="secondary", command=run_verify)
    verify.pack(side=tk.LEFT, padx=8)
    verify.set_state("disabled")

    rollback = StyledButton(controls, "Rollback", style="danger", command=run_rollback)
    rollback.pack(side=tk.LEFT)
    rollback.set_state("disabled")

    deploy.bounce()
    verify.bounce(height=10, ms=420)
    rollback.bounce(height=8, ms=380)
    root.mainloop()


if __name__ == "__main__":
    main()
