# RMPrayer

A minimal desktop application scaffold for RMPrayer. The project uses PyQt6 for the GUI layer and is structured so it can be extended with reporting, offline storage, and SSH-based automation in later milestones.

## Features

- **PyQt6 placeholder UI** that opens a window and confirms that the runtime stack works.
- **Centralised settings module** with environment-variable overrides and a per-user data directory.
- **Reusable logging configuration** that writes to both stdout and a rotating log file.
- **PyInstaller configuration** for generating a single-file `RMPrayer.exe` on Windows together with a helper build script.

## Requirements

- Python 3.10 or later
- Pip 23+ (for editable installs)
- Windows builds require PyInstaller (installed automatically via the optional `build` dependency group)

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e .
```

To install the tooling required for packaging an executable:

```bash
pip install .[build]
```

## Running the App

After installing the project in editable mode, launch the GUI with:

```bash
python -m rmprayer.main
```

A titled window should appear letting you know that the desktop client is under construction. Closing the window stops the process.

## Building the Windows Executable

The repository ships with:

- `RMPrayer.spec` – the PyInstaller configuration describing how to bundle the app.
- `build_exe.bat` – a helper script that prepares/updates a local virtual environment, installs dependencies (including PyInstaller), and executes the spec file to produce a single-file build.

To build `RMPrayer.exe` on Windows:

1. Open *Developer Command Prompt for VS* or *PowerShell*.
2. Navigate to the repository root.
3. Run `build_exe.bat`.

The resulting binary will be placed in `dist/RMPrayer.exe` without external runtime dependencies. Launching it should show the same placeholder UI as running the module directly.

## Project Layout

```
.
├── README.md
├── RMPrayer.spec
├── build_exe.bat
├── pyproject.toml
└── src
    └── rmprayer
        ├── __init__.py
        ├── logging_config.py
        ├── main.py
        └── settings.py
```

## Settings

`rmprayer.settings` defines an `AppSettings` dataclass. The loader allows overriding defaults with the following environment variables:

| Environment Variable | Purpose |
| -------------------- | ------- |
| `RMP_APP_NAME`       | Custom window/application title |
| `RMP_APP_VERSION`    | Overrides the version shown in the UI |
| `RMP_DATA_DIR`       | Custom directory for persistent data and logs |

The settings module eagerly creates the data directory to ensure later components can rely on it being present.

## Logging

`rmprayer.logging_config.configure_logging()` configures a standard library logging setup with:

- Console output for quick debugging
- Daily rotating log files stored inside `<data_dir>/logs`

Call it once at startup (see `rmprayer.main`) to receive consistent structured logs across the app.
