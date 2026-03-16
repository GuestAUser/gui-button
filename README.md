# button_gen

A single-file Python toolkit for generating styled GUI buttons. Works as a CLI tool for quick one-off buttons and as an embeddable tkinter widget for real applications.

No external dependencies. Just Python 3.10+ and tkinter.

## Install

Clone the repo. Make sure tkinter is available:

```
# Debian/Ubuntu
sudo apt install python3-tk

# Arch
sudo pacman -S tk

# macOS
brew install python-tk
```

## CLI Usage

Generate a button from the terminal:

```
python button_gen.py "Click Me"
```

The window opens with a styled, interactive button. Clicking it prints to stdout by default.

### Styles

Seven built-in presets:

```
python button_gen.py "Submit"  --style primary
python button_gen.py "Cancel"  --style secondary
python button_gen.py "Saved"   --style success
python button_gen.py "Delete"  --style danger
python button_gen.py "Caution" --style warning
python button_gen.py "Config"  --style dark
python button_gen.py "Info"    --style light
```

### Dark theme

```
python button_gen.py "Launch" --style danger --dark
```

### Custom colors

```
python button_gen.py "Purple" --bg "#8b5cf6" --fg white --dark
```

### Click actions

| Flag | Behavior |
|------|----------|
| `--action print` | Print button text to stdout (default) |
| `--action exit` | Close the window |
| `--action notify` | Show a popup message |
| `--action count` | Increment a counter on the button face |

### Other options

```
--font-size 24        Font size in points
--font-family "Mono"  Font family
--title "My App"      Window title
--version             Print version and exit
```

### Full example

```
python button_gen.py "Deploy" --style danger --dark --font-size 20 --action count --title "Ops Console"
```

## Library Usage

`button_gen.py` is a single file you can drop into any project. Import `StyledButton` and use it like any tkinter widget.

### Minimal example

```python
import tkinter as tk
from button_gen import StyledButton

root = tk.Tk()
root.configure(bg="#0f172a")

btn = StyledButton(root, "Click Me", command=lambda: print("clicked"))
btn.pack(padx=20, pady=20)

root.mainloop()
```

### Constructor options

```python
StyledButton(
    parent,
    "Label",
    command=callback,         # called on click
    style="primary",          # preset name or Style object
    bg="#2563eb",             # override background
    fg="#ffffff",             # override text color
    hover_bg="#1d4ed8",       # override hover color
    active_bg="#1e40af",      # override pressed color
    font_family="Sans",
    font_size=14,
    radius=12,                # corner radius
    pad_x=28,                 # horizontal padding
    pad_y=12,                 # vertical padding
    shadow=True,              # drop shadow
    animate=True,             # smooth transitions
    ripple=True,              # ripple on click
)
```

### Custom styles

```python
from button_gen import Style, StyledButton

teal = Style(bg="#14b8a6", fg="#ffffff", radius=8)
btn = StyledButton(root, "Teal", style=teal)
```

### Animations

Every button has four animation methods:

```python
btn.bounce()                     # entrance bounce
btn.shake(intensity=6, ms=400)   # horizontal shake
btn.pulse(count=2, ms=700)       # color/scale flash
btn.ripple()                     # expanding circle from center
btn.cancel_effects()             # stop all running effects
```

Animations compose. Calling `shake()` during a `bounce()` adds the offsets together instead of fighting.

### State management

Buttons have a formal state machine with four states:

```python
from button_gen import ButtonState

btn.set_state("disabled")        # grayed out, ignores input
btn.set_state("normal")          # restore interactivity
btn.set_state(ButtonState.HOVER) # force hover appearance
```

### Programmatic activation

```python
btn.invoke()  # triggers pressed state, ripple, and command callback
```

Behaves identically to a mouse click or keyboard activation.

### Runtime restyling

```python
btn.configure_style(
    style="danger",
    font_size=18,
    radius=20,
)

# clear an override to fall back to the preset
btn.configure_style(bg="", radius=0)
```

### Dynamic text

```python
btn.text = "Updated"    # resize and redraw automatically
label = btn.text        # read current text
```

## Examples

The `examples/` folder contains working applications that demonstrate the widget in realistic scenarios:

| File | What it shows |
|------|---------------|
| `login_form.py` | Form validation, disabled states, Enter-to-submit, async sign-in flow |
| `deploy_console.py` | Deploy/verify/rollback pipeline with staged logging and `invoke()` |
| `download_manager.py` | Start/pause/resume/cancel with progress bar and state coordination |
| `danger_zone.py` | Two-step destructive action with arming and guarded delete |
| `advance.py` | Full control room exercising every public API method |

Run any of them directly:

```
python examples/deploy_console.py
```

## Project structure

```
button_gen.py          Single-file library + CLI
examples/
  login_form.py        Form with validation
  deploy_console.py    Deployment pipeline
  download_manager.py  File transfer controls
  danger_zone.py       Destructive action guard
  advance.py           Full API workspace
```

## Requirements

- Python 3.10+
- tkinter (usually included with Python; see install section if missing)

## License

MIT
