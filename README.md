# batify - Package Python scripts into standalone .bat files for easy sharing and execution

![alt text](docs/batify_128.gif "Logo")

A basic tool for creating Windows batch (.bat) files that contains Python code.

## Rationale

This tool simplifies the process of sharing Python scripts in a Windows
environment by encapsulating all necessary setup into a single, executable batch
file. It ensures that less tech-savvy users can run complex Python programs
without needing to manually set up virtual environments or install dependencies,
requiring only Python to be pre-installed.

## Features

- Everything is self-contained, only one .bat file
- Only update dependencies if needed
- Allows specifying requirements directly in the Python file using [PEP
  723](https://peps.python.org/pep-0723/) (Python 3.11+ required)
- Uses [uv](https://docs.astral.sh/uv/) if available
- Allows specifying environment variables `PYTHON` and `UV` to use Python/uv
  that is not in the path
- Allows specifying custom pypi host

## Examples

- Only standard libraries: Use this for scripts with no external dependencies.
  - [hello_world.py](examples/hello_world.py)
  - `batify -s examples/hello_world.py`
- Requirements file: Include external dependencies by specifying a requirements.txt file.
  - [hello_world.py](examples/hello_world_req.py)
  - [requirements.txt](examples/requirements.txt)
  - `batify -s examples/hello_world_req.py -r examples/requirements.txt`
- PEP 723 support: Embed dependencies directly into your Python script (requires Python 3.11 or later).
  - [hello_world_pep723.py](examples/hello_world_pep723.py)
  - `batify -s examples/hello_world_pep723.py`

Run `batify --help` for more options

## Inspiration

- [Batchography: Embedding Python scripts in your Batch file script](https://lallouslab.net/2017/06/12/batchography-embedding-python-scripts-in-your-batch-file-script/)

## Alternative

- [uvx](https://docs.astral.sh/uv/guides/tools/#running-tools): A versatile tool for running standalone Python scripts.
- [pipx](https://pipx.pypa.io/stable/): Focuses on isolated installation of Python applications.
- [PyInstaller](https://pyinstaller.org/en/stable/): Converts Python applications into standalone executables.
