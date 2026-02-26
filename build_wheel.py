import argparse
import os
import subprocess
import sys
import tempfile

from go_to_wheel import PLATFORM_MAPPINGS, build_wheel


def compile_go_binary(
    go_dir: str,
    output_path: str,
    goos: str,
    goarch: str,
) -> None:
    env = os.environ.copy()
    env["GOOS"] = goos
    env["GOARCH"] = goarch
    print(f"Compiling {goos}/{goarch} CGO_ENABLED={env['CGO_ENABLED']}", file=sys.stderr)

    result = subprocess.run(
        ["go", "build", "-ldflags=-s -w", "-o", output_path, "."],
        cwd=go_dir, env=env, capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"Go compilation failed for {goos}/{goarch}:\n{result.stderr}")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")


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

    goos, goarch, platform_tag = PLATFORM_MAPPINGS[args.platform]
    is_windows = goos == "windows"

    os.makedirs(args.output_dir, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        binary_path = os.path.join(tmp_dir, f"{args.entry_point}{'.exe' if is_windows else ''}")
        compile_go_binary(args.go_dir, binary_path, goos, goarch)

        wheel_path = build_wheel(
            binary_path,
            args.output_dir,
            args.name,
            args.version,
            platform_tag,
            args.entry_point,
            is_windows=is_windows,
        )
        print(f"  -> {wheel_path}")


if __name__ == "__main__":
    main()
