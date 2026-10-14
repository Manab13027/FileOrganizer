# File Organizer

A **tool that automatically tidies messy folders** by sorting files into
subfolders by type and/or date. Available both as a command-line script and as
a modern Tkinter desktop GUI, with a preview step so you can see the plan before
anything moves.

## Features
- Sort by file type and/or creation/modification date
- **Dry-run / preview** before moving anything
- Modern dark-themed GUI (several iterations) + a CLI core
- Date detection, configurable rules (`config.yaml`)
- Simple stats & charts of what was organized (pandas/matplotlib)

## Stack
Python · Tkinter · Pillow · pandas · matplotlib

## Getting started
```bash
pip install -r requirements.txt
python FileOrganizerGuiModernV3.py     # GUI (latest)
# or, command line:
python FileOrganizer.py --help
```

## Notes
- Use dry-run first on important folders. Rules are editable in `config.yaml`.
