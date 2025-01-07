import argparse
import pathlib
import re
import subprocess

try:
    # tomllib is only available on Python >= 3.11
    import tomllib

    tomllib_available = True
except ModuleNotFoundError:
    tomllib_available = False


HEADER_NO_REQ = r'''@echo off
rem = """ {{gitversion}}
setlocal
if not defined PYTHON set PYTHON=python
%PYTHON% -X utf8 -x "%~f0" %*
exit /b %errorlevel%
"""
'''


HEADER_REQ = r'''@echo off
rem = """ {{gitversion}}
setlocal
if not defined PYTHON set PYTHON=python
if not defined UV set UV=uv

if "%NO_COLOR%" equ "1" (
    :: https://no-color.org/
    set COL_GREEN=
    set COL_RESET=
) else (
    set COL_GREEN=[92m
    set COL_RESET=[0m
)
set LOC=%~dp0
set VIRTUAL_ENV=%LOC%.venv.%~n0
set MARKER=%VIRTUAL_ENV%\.marker

:: check if uv is available (USE_PYTHON will be set to 9009 if uv does not exist)
%UV% --version >nul 2>&1
set USE_PYTHON=%errorlevel%

if not exist "%VIRTUAL_ENV%" (
    echo %COL_GREEN%batify: create venv...%COL_RESET%
    if %USE_PYTHON% gtr 0 (
        %PYTHON% -mvenv "%VIRTUAL_ENV%" || goto error
    ) else (
        %UV% venv "%VIRTUAL_ENV%" >nul 2>&1 || goto error
    )
)

if not exist "%MARKER%" (
    echo %COL_GREEN%batify: install requirements...%COL_RESET%
    if %USE_PYTHON% gtr 0 (
        "%VIRTUAL_ENV%\Scripts\python" ^
            -mpip ^
            install ^
            {{pypi-host}} ^
            {{pypi-url}} ^
            --disable-pip-version-check ^
            {{requirements}} || goto error
    ) else (
        %UV% ^
            pip ^
            install ^
            {{pypi-host}} ^
            {{pypi-url}} ^
            {{requirements}} || goto error
    )
    type NUL > "%MARKER%"
)

:: NOTE: this only provide minute resolution but it is as good as it gets without using powershell
for %%f in (%~f0) do set MTIMESCRIPT=%%~tf
for %%f in (%MARKER%) do set MTIMEMARKER=%%~tf

if "%MTIMESCRIPT%" gtr "%MTIMEMARKER%" (
    echo %COL_GREEN%batify: update requirements...%COL_RESET%
    if %USE_PYTHON% gtr 0 (
        "%VIRTUAL_ENV%\Scripts\python" ^
            -mpip ^
            install ^
            {{pypi-host}} ^
            {{pypi-url}} ^
            --disable-pip-version-check ^
            {{requirements}} || goto error
    ) else (
        %UV% ^
            pip ^
            install ^
            {{pypi-host}} ^
            {{pypi-url}} ^
            {{requirements}} || goto error
    )
    type NUL > "%MARKER%"
)

"%VIRTUAL_ENV%\Scripts\python" -X utf8 -x "%~f0" %*
exit /b %errorlevel%

:error
if exist "%MARKER%" (
    echo %COL_GREEN%batify: remove marker...%COL_RESET%
    del "%MARKER%"
)
exit /b 1
"""
'''

if tomllib_available:

    class PEP723:
        """Taken from https://peps.python.org/pep-0723/#reference-implementation"""

        @staticmethod
        def read(script: str) -> dict | None:
            REGEX = r"(?m)^# /// (?P<type>[a-zA-Z0-9-]+)$\s(?P<content>(^#(| .*)$\s)+)^# ///$"
            name = "script"
            matches = list(
                filter(lambda m: m.group("type") == name, re.finditer(REGEX, script))
            )
            if len(matches) > 1:
                raise ValueError(f"Multiple {name} blocks found")
            elif len(matches) == 1:
                content = "".join(
                    line[2:] if line.startswith("# ") else line[1:]
                    for line in matches[0].group("content").splitlines(keepends=True)
                )
                return tomllib.loads(content)
            else:
                return None


def git_version():
    try:
        cp = subprocess.run(
            [
                "git",
                "describe",
                "--abbrev=8",
                "--dirty",
                "--always",
                "--tags",
                "--long",
            ],
            capture_output=True,
        )
        return f"git version: {cp.stdout.decode('ascii').strip()}"
    except Exception:
        return ""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="batify",
        description="A basic tool for creating bat files that contains Python code.",
    )
    parser.add_argument(
        "-s",
        "--script",
        help="Python script file",
        required=True,
    )
    parser.add_argument(
        "-r",
        "--requirements",
        help="Requirements file",
    )
    parser.add_argument(
        "--pypi-host",
        default="",
        help="Hostname of pypi host (e.g. host)",
    )
    parser.add_argument(
        "--pypi-url",
        default="",
        help="E.g. http://host/pypi/simple",
    )
    parser.add_argument(
        "--outdir",
        default="dist",
        help="Output directory",
    )
    args = parser.parse_args()

    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(exist_ok=True)

    script = pathlib.Path(args.script)
    outfile = str(outdir / script.stem) + ".bat"

    with open(script, encoding="utf-8") as f:
        scriptdata = f.read()

    dependencies = []
    if args.requirements:
        with open(args.requirements, encoding="utf-8") as f:
            dependencies = f.readlines()
    elif tomllib_available:
        deps = PEP723.read(scriptdata)
        if deps:
            dependencies = deps.get("dependencies", [])
    dependencies = [x.strip().strip("'\"") for x in dependencies]

    with open(outfile, encoding="utf-8", mode="w") as f:
        if len(dependencies) == 0:
            header = HEADER_NO_REQ.replace("{{gitversion}}", git_version())
            f.write(header)
        else:
            header = HEADER_REQ
            header = header.replace(
                "{{requirements}}", " ".join('"%s"' % d for d in dependencies)
            )
            header = header.replace("{{pypi-host}}", f"--trusted-host={args.pypi_host}")
            header = header.replace("{{pypi-url}}", f"--index-url={args.pypi_url}")
            header = header.replace("{{gitversion}}", git_version())
            f.write(header)
        f.write(scriptdata)
