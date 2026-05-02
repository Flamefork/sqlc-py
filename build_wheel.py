import argparse
import base64
import csv
import hashlib
import io
import os
import shlex
import stat
import subprocess
import sys
import tempfile
import zipfile
from typing import NamedTuple


class Platform(NamedTuple):
    goos: str
    goarch: str
    cgo_enabled: bool


PLATFORM_MAPPINGS: dict[str, Platform] = {
    "manylinux_2_17_x86_64":  Platform("linux",   "amd64", True),
    "manylinux_2_17_aarch64": Platform("linux",   "arm64", True),
    "musllinux_1_2_x86_64":   Platform("linux",   "amd64", False),
    "musllinux_1_2_aarch64":  Platform("linux",   "arm64", False),
    "macosx_10_9_x86_64":     Platform("darwin",  "amd64", True),
    "macosx_11_0_arm64":      Platform("darwin",  "arm64", True),
    "win_amd64":              Platform("windows", "amd64", True),
    "win_arm64":              Platform("windows", "arm64", False),
}

ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
EXEC_MODE = (stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH) << 16
NON_EXEC_MODE = (stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH) << 16


def compile_go_binary(go_dir: str, output_path: str, platform: Platform) -> None:
    overrides = {
        "GOOS": platform.goos,
        "GOARCH": platform.goarch,
        "CGO_ENABLED": "1" if platform.cgo_enabled else "0",
    }
    cmd = ["go", "build", "-ldflags=-s -w", "-o", output_path, "."]
    print(
        f"cd {shlex.quote(go_dir)} && "
        + " ".join(f"{k}={shlex.quote(v)}" for k, v in overrides.items())
        + " " + shlex.join(cmd),
        file=sys.stderr,
    )

    result = subprocess.run(
        cmd, cwd=go_dir, env=os.environ | overrides, capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"Go compilation failed:\n{result.stderr}")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")


def render_init_py(version: str, binary_name: str) -> str:
    return f'''"""Go binary packaged as Python wheel."""

import os
import stat
import subprocess
import sys

__version__ = "{version}"


def get_binary_path() -> str:
    """Return the path to the bundled binary."""
    binary = os.path.join(os.path.dirname(__file__), "bin", "{binary_name}")

    if sys.platform != "win32":
        current_mode = os.stat(binary).st_mode
        if not (current_mode & stat.S_IXUSR):
            os.chmod(binary, current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return binary


def main() -> None:
    """Execute the bundled binary."""
    binary = get_binary_path()

    if sys.platform == "win32":
        sys.exit(subprocess.call([binary, *sys.argv[1:]]))
    else:
        os.execvp(binary, [binary, *sys.argv[1:]])
'''


MAIN_PY = """from . import main
main()
"""


def render_metadata(name: str, version: str) -> str:
    return (
        "Metadata-Version: 2.1\n"
        f"Name: {name}\n"
        f"Version: {version}\n"
        "Summary: Go binary packaged as Python wheel\n"
        "Requires-Python: >=3.10\n"
    )


def render_wheel(platform_tag: str) -> str:
    return (
        "Wheel-Version: 1.0\n"
        "Generator: sqlc-py build_wheel.py\n"
        "Root-Is-Purelib: false\n"
        f"Tag: py3-none-{platform_tag}\n"
    )


def render_entry_points(entry_point: str, import_name: str) -> str:
    return f"[console_scripts]\n{entry_point} = {import_name}:main\n"


def hash_record(data: bytes) -> str:
    digest = hashlib.sha256(data).digest()
    encoded = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return f"sha256={encoded}"


def render_record(files: dict[str, bytes], record_path: str) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    for path, content in files.items():
        if path == record_path:
            writer.writerow([path, "", ""])
        else:
            writer.writerow([path, hash_record(content), len(content)])
    return output.getvalue()


def add_to_wheel(whl: zipfile.ZipFile, path: str, content: bytes, *, executable: bool) -> None:
    info = zipfile.ZipInfo(path, date_time=ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = EXEC_MODE if executable else NON_EXEC_MODE
    whl.writestr(info, content)


def build_wheel(
    binary_path: str,
    output_dir: str,
    name: str,
    version: str,
    platform_tag: str,
    entry_point: str,
    binary_name: str,
) -> str:
    import_name = name.replace("-", "_").replace(".", "_").lower()

    with open(binary_path, "rb") as f:
        binary_content = f.read()

    dist_info = f"{import_name}-{version}.dist-info"
    record_path = f"{dist_info}/RECORD"
    binary_in_wheel = f"{import_name}/bin/{binary_name}"

    files: dict[str, bytes] = {
        f"{import_name}/__init__.py": render_init_py(version, binary_name).encode(),
        f"{import_name}/__main__.py": MAIN_PY.encode(),
        f"{import_name}/py.typed": b"",
        binary_in_wheel: binary_content,
        f"{dist_info}/METADATA": render_metadata(name, version).encode(),
        f"{dist_info}/WHEEL": render_wheel(platform_tag).encode(),
        f"{dist_info}/entry_points.txt": render_entry_points(entry_point, import_name).encode(),
        record_path: b"",
    }
    files[record_path] = render_record(files, record_path).encode()

    wheel_name = f"{import_name}-{version}-py3-none-{platform_tag}.whl"
    wheel_path = os.path.join(output_dir, wheel_name)

    with zipfile.ZipFile(wheel_path, "w") as whl:
        for file_path, content in files.items():
            add_to_wheel(whl, file_path, content, executable=(file_path == binary_in_wheel))

    return wheel_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("go_dir")
    parser.add_argument("--name", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--entry-point", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--output-dir", default="./dist")
    args = parser.parse_args()

    if args.platform not in PLATFORM_MAPPINGS:
        raise SystemExit(f"Unknown platform: {args.platform!r}. Supported: {', '.join(PLATFORM_MAPPINGS)}")

    platform = PLATFORM_MAPPINGS[args.platform]
    binary_name = args.entry_point + (".exe" if platform.goos == "windows" else "")

    os.makedirs(args.output_dir, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        binary_path = os.path.join(tmp_dir, binary_name)
        compile_go_binary(args.go_dir, binary_path, platform)

        wheel_path = build_wheel(
            binary_path,
            args.output_dir,
            args.name,
            args.version,
            args.platform,
            args.entry_point,
            binary_name,
        )
        print(f"  -> {wheel_path}")


if __name__ == "__main__":
    main()
