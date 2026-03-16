#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk

from button_gen import DARK_BG, StyledButton


def main() -> None:
    root = tk.Tk()
    root.title("Download Manager")
    root.configure(bg=DARK_BG)
    root.resizable(False, False)

    shell = tk.Frame(root, bg=DARK_BG, padx=24, pady=24)
    shell.pack()

    tk.Label(shell, text="Download Manager", font=("Sans", 18, "bold"), fg="#f8fafc", bg=DARK_BG).pack(anchor="w")
    tk.Label(shell, text="Simulated file transfer with real control states.", font=("Sans", 10), fg="#94a3b8", bg=DARK_BG).pack(anchor="w", pady=(4, 18))

    progress_frame = tk.Frame(shell, bg="#111827", width=460, height=18)
    progress_frame.pack(fill=tk.X)
    progress_frame.pack_propagate(False)

    bar = tk.Frame(progress_frame, bg="#2563eb", width=0)
    bar.pack(side=tk.LEFT, fill=tk.Y)

    progress_text = tk.StringVar(value="0% complete")
    status = tk.StringVar(value="Ready to download")
    tk.Label(shell, textvariable=progress_text, font=("Sans", 12, "bold"), fg="#e2e8f0", bg=DARK_BG).pack(anchor="w", pady=(12, 2))
    tk.Label(shell, textvariable=status, font=("Sans", 10), fg="#94a3b8", bg=DARK_BG).pack(anchor="w")

    controls = tk.Frame(shell, bg=DARK_BG)
    controls.pack(fill=tk.X, pady=(18, 0))

    progress = [0]
    paused = [False]
    task: list[str | None] = [None]

    def sync_controls() -> None:
        start.set_state("disabled" if task[0] is not None or progress[0] >= 100 else "normal")
        pause.set_state("normal" if task[0] is not None else "disabled")
        resume.set_state("normal" if paused[0] and progress[0] < 100 else "disabled")
        cancel.set_state("normal" if progress[0] > 0 and progress[0] < 100 else "disabled")

    def redraw() -> None:
        width = int(460 * progress[0] / 100)
        bar.configure(width=width)
        progress_text.set(f"{progress[0]}% complete")

    def finish_download() -> None:
        task[0] = None
        paused[0] = False
        progress[0] = 100
        redraw()
        status.set("Download complete")
        start.configure_style(style="success")
        start.text = "Done"
        start.pulse(count=1, ms=260)
        sync_controls()

    def tick() -> None:
        task[0] = None
        if paused[0]:
            sync_controls()
            return
        progress[0] = min(progress[0] + 4, 100)
        redraw()
        status.set("Downloading archive...")
        if progress[0] >= 100:
            finish_download()
            return
        task[0] = root.after(120, tick)
        sync_controls()

    def start_download() -> None:
        if progress[0] >= 100:
            progress[0] = 0
            start.configure_style(style="primary")
            start.text = "Start"
            redraw()
        paused[0] = False
        status.set("Connecting to edge cache...")
        if task[0] is None:
            task[0] = root.after(120, tick)
        sync_controls()

    def pause_download() -> None:
        paused[0] = True
        if task[0] is not None:
            root.after_cancel(task[0])
            task[0] = None
        status.set("Paused")
        pause.configure_style(style="warning")
        pause.pulse(count=1, ms=200)
        sync_controls()

    def resume_download() -> None:
        paused[0] = False
        status.set("Resuming download...")
        resume.configure_style(style="success")
        task[0] = root.after(120, tick)
        sync_controls()

    def cancel_download() -> None:
        if task[0] is not None:
            root.after_cancel(task[0])
            task[0] = None
        paused[0] = False
        progress[0] = 0
        redraw()
        status.set("Download canceled")
        cancel.shake()
        start.configure_style(style="primary")
        start.text = "Start"
        sync_controls()

    start = StyledButton(controls, "Start", style="primary", command=start_download)
    start.pack(side=tk.LEFT)
    pause = StyledButton(controls, "Pause", style="warning", command=pause_download)
    pause.pack(side=tk.LEFT, padx=8)
    resume = StyledButton(controls, "Resume", style="success", command=resume_download)
    resume.pack(side=tk.LEFT)
    cancel = StyledButton(controls, "Cancel", style="danger", command=cancel_download)
    cancel.pack(side=tk.LEFT, padx=(8, 0))

    sync_controls()
    root.mainloop()


if __name__ == "__main__":
    main()
