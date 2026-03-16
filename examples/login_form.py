#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk

from button_gen import LIGHT_BG, StyledButton


def main() -> None:
    root = tk.Tk()
    root.title("Login Form")
    root.configure(bg=LIGHT_BG)
    root.resizable(False, False)

    card = tk.Frame(root, bg="#ffffff", padx=24, pady=24)
    card.pack(padx=32, pady=32)

    tk.Label(card, text="Team Portal", font=("Sans", 18, "bold"), bg="#ffffff", fg="#0f172a").pack(anchor="w")
    tk.Label(card, text="Sign in to continue", font=("Sans", 10), bg="#ffffff", fg="#64748b").pack(anchor="w", pady=(4, 16))

    username = tk.StringVar()
    password = tk.StringVar()
    status = tk.StringVar(value="Enter your credentials")

    tk.Label(card, text="Email", bg="#ffffff", fg="#334155").pack(anchor="w")
    email_entry = tk.Entry(card, textvariable=username, width=32, relief=tk.FLAT, bg="#f8fafc", fg="#0f172a")
    email_entry.pack(fill=tk.X, pady=(4, 12), ipady=8)

    tk.Label(card, text="Password", bg="#ffffff", fg="#334155").pack(anchor="w")
    password_entry = tk.Entry(card, textvariable=password, width=32, show="*", relief=tk.FLAT, bg="#f8fafc", fg="#0f172a")
    password_entry.pack(fill=tk.X, pady=(4, 16), ipady=8)

    actions = tk.Frame(card, bg="#ffffff")
    actions.pack(fill=tk.X)

    def sync_submit_state() -> None:
        ready = bool(username.get().strip() and password.get().strip())
        submit.set_state("normal" if ready else "disabled")

    def complete_sign_in() -> None:
        submit.configure_style(style="success")
        submit.text = "Signed In"
        submit.set_state("disabled")
        clear.set_state("normal")
        status.set(f"Welcome back, {username.get().strip()}")
        clear.pulse(count=1, ms=220)

    def submit_form() -> None:
        if not username.get().strip() or not password.get().strip():
            status.set("Both fields are required")
            submit.shake()
            return
        submit.set_state("disabled")
        clear.set_state("disabled")
        submit.configure_style(style="warning")
        submit.text = "Signing In..."
        status.set("Authenticating with the identity service...")
        root.after(900, complete_sign_in)

    def clear_form() -> None:
        username.set("")
        password.set("")
        submit.configure_style(style="primary")
        submit.text = "Sign In"
        clear.configure_style(style="secondary")
        status.set("Enter your credentials")
        sync_submit_state()
        email_entry.focus_set()

    submit = StyledButton(actions, "Sign In", style="primary", command=submit_form, font_size=12)
    submit.pack(side=tk.LEFT)

    clear = StyledButton(actions, "Clear", style="secondary", command=clear_form, font_size=12)
    clear.pack(side=tk.LEFT, padx=(10, 0))
    clear.set_state("disabled")

    tk.Label(card, textvariable=status, font=("Sans", 10), bg="#ffffff", fg="#475569").pack(anchor="w", pady=(16, 0))

    def on_text_change(*_args: str) -> None:
        submit.configure_style(style="primary")
        submit.text = "Sign In"
        status.set("Enter your credentials")
        clear.set_state("normal")
        sync_submit_state()

    username.trace_add("write", on_text_change)
    password.trace_add("write", on_text_change)
    password_entry.bind("<Return>", lambda _event: submit.invoke())

    submit.set_state("disabled")
    email_entry.focus_set()
    root.mainloop()


if __name__ == "__main__":
    main()
