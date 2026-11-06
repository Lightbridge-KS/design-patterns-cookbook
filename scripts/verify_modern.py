# /// script
# requires-python = ">=3.13"
# dependencies = ["mypy==2.4.0"]
# ///
"""Verify that the code examples in each pattern chapter really run.

The .qmd chapter is the source of truth. Two checks run per chapter:

1. Modern: the first Python, C#, TypeScript, Dart, and Rust block inside
   `## Modern Approach` is extracted, type-checked (Rust: clippy with warnings
   denied), and run. All five programs must print the same output (compared
   case-insensitively against Python's).
2. Classic Rust: all Rust blocks inside `## Problem` are joined into one
   program, and so are those inside `## Solution` (definitions, then the usage
   block with `fn main()`). Each program must compile and exit 0. The borrow
   checker makes Rust snippets break more easily than the other languages.

Requires on PATH: uv, dotnet (10+), node (23.6+, runs .ts directly), tsc, dart,
rustc + clippy-driver (Rust 1.85+, edition 2024; `rustup component add clippy`).
Run through uv so the pinned mypy is installed: `uv run scripts/verify_modern.py`.

Examples:
  just verify                                        # every chapter
  just verify contents/behavioral/08-strategy.qmd    # one chapter
  uv run scripts/verify_modern.py -v contents/structural/*.qmd

Generated programs are kept in .verify/<category>/<chapter>/ for debugging.
Exit status: 0 = all passed, 1 = a chapter failed, 2 = bad arguments or missing tools.
"""

import argparse
import difflib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENTS = ROOT / "contents"
OUT_ROOT = ROOT / ".verify"

FENCE = re.compile(r"^```(\w+)\n(.*?)^```", re.S | re.M)
USAGE_MARKER = "--- Usage ---"
ENV = os.environ | {"DOTNET_CLI_TELEMETRY_OPTOUT": "1", "DOTNET_NOLOGO": "1"}
MAX_DETAIL_LINES = 40


@dataclass(frozen=True)
class Lang:
    fence: str  # code-fence tag in the .qmd
    filename: str
    check: list[str] | None  # type-check command; None when the run step compiles
    run: list[str]
    check_builds: bool = False  # the check step produces the program; skip the run when it fails


LANGS = [
    Lang("python", "main.py", [sys.executable, "-m", "mypy", "--strict", "main.py"], [sys.executable, "main.py"]),
    Lang("csharp", "main.cs", None, ["dotnet", "run", "main.cs"]),
    Lang(
        "typescript",
        "main.ts",
        ["tsc", "--noEmit", "--strict", "--target", "esnext", "--lib", "esnext,dom", "main.ts"],
        ["node", "main.ts"],
    ),
    Lang("dart", "main.dart", ["dart", "--suppress-analytics", "analyze", "main.dart"], ["dart", "--suppress-analytics", "run", "main.dart"]),
    Lang(
        "rust",
        "main.rs",
        # `new_without_default` is allowed: an `impl Default` beside every `fn new()` is noise next to the pattern
        ["clippy-driver", "--edition", "2024", "-D", "warnings", "-A", "clippy::new_without_default", "-o", "main", "main.rs"],
        ["./main"],
        check_builds=True,
    ),
]
CLASSIC_SECTIONS = ("Problem", "Solution")  # Rust-only compile-and-run check
RUSTC_CLASSIC = ["rustc", "--edition", "2024", "-A", "unused", "-o", "main", "main.rs"]


@dataclass
class Result:
    chapter: str
    ok: bool = True
    details: list[str] = field(default_factory=list)

    def fail(self, step: str, output: str) -> None:
        self.ok = False
        lines = output.strip().splitlines()
        self.details.append(step)
        self.details += [f"    {line}" for line in lines[:MAX_DETAIL_LINES]]
        if len(lines) > MAX_DETAIL_LINES:
            self.details.append(f"    … {len(lines) - MAX_DETAIL_LINES} more lines")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("chapters", nargs="*", type=Path, help="chapter .qmd files (default: every chapter with a Modern Approach section)")
    parser.add_argument("-j", "--jobs", type=int, default=4, help="chapters verified in parallel (default: 4)")
    parser.add_argument("-v", "--verbose", action="store_true", help="also print the output of passing chapters")
    args = parser.parse_args()

    if problems := preflight():
        print("Cannot verify:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2
    chapters = [path.resolve() for path in args.chapters] or default_chapters()
    if missing := [str(path) for path in chapters if not path.is_file()]:
        print("No such chapter file: " + ", ".join(missing), file=sys.stderr)
        return 2

    results: list[Result] = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(verify_chapter, path, args.verbose) for path in chapters]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(f"{'PASS' if result.ok else 'FAIL'}  {result.chapter}", *result.details, sep="\n  " if result.details else "")

    failed = sorted(r.chapter for r in results if not r.ok)
    print(f"\n{len(results) - len(failed)}/{len(results)} chapters passed" + (f"; failed: {', '.join(failed)}" if failed else ""))
    return 1 if failed else 0


def preflight() -> list[str]:
    tools = ("dotnet", "node", "tsc", "dart", "rustc", "clippy-driver")
    problems = [f"`{tool}` not found on PATH" for tool in tools if shutil.which(tool) is None]
    if sys.version_info < (3, 13):
        problems.append("Python 3.13+ required (examples use copy.replace); run via `uv run scripts/verify_modern.py`")
    if importlib.util.find_spec("mypy") is None:
        problems.append("mypy not installed; run via `uv run scripts/verify_modern.py` (or `just verify`), which installs the pinned version")
    return problems


def default_chapters() -> list[Path]:
    return sorted(path for path in CONTENTS.rglob("*.qmd") if section(path.read_text(), "Modern Approach") is not None)


def section(text: str, title: str) -> str | None:
    """Body of the `## <title>` section, up to the next H2 (None when absent)."""
    match = re.search(rf"^## {re.escape(title)}[ \t]*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return match.group(1) if match else None


def verify_chapter(qmd: Path, verbose: bool) -> Result:
    name = str(qmd.relative_to(CONTENTS).with_suffix("")) if qmd.is_relative_to(CONTENTS) else qmd.stem
    result = Result(name)
    text = qmd.read_text()
    modern = section(text, "Modern Approach")
    if modern is None:
        result.fail("no `## Modern Approach` section", "")
        return result

    blocks: dict[str, str] = {}
    for fence, code in FENCE.findall(modern):
        blocks.setdefault(fence, code)

    out_dir = OUT_ROOT / name
    out_dir.mkdir(parents=True, exist_ok=True)
    stdouts: dict[str, str] = {}
    for lang in LANGS:
        if lang.fence not in blocks:
            result.fail(f"{lang.fence}: no ```{lang.fence} block in the section", "")
            continue
        (out_dir / lang.filename).write_text(to_runnable(lang.fence, blocks[lang.fence]))
        if lang.check:
            if lang.check_builds:
                (out_dir / "main").unlink(missing_ok=True)  # never run a stale binary
            code, output = run(lang.check, out_dir)
            if code != 0:
                result.fail(f"{lang.fence}: type check failed", output)
                if lang.check_builds:
                    continue
        code, output = run(lang.run, out_dir)
        if code != 0:
            result.fail(f"{lang.fence}: run failed (exit {code})", output)
        stdouts[lang.fence] = output

    reference = normalize(stdouts.get("python", ""))
    for fence, output in stdouts.items():
        diff = list(difflib.unified_diff(reference, normalize(output), "python", fence, lineterm="", n=0))
        if fence != "python" and diff:
            result.fail(f"{fence}: output differs from python", "\n".join(diff))

    verify_classic_rust(text, OUT_ROOT / name, result)

    if verbose and result.ok:
        result.details += [f"    {line}" for line in stdouts.get("python", "").splitlines()]
    return result


def verify_classic_rust(text: str, out_root: Path, result: Result) -> None:
    """Join each classic section's Rust blocks into one program; it must compile and exit 0."""
    for title in CLASSIC_SECTIONS:
        step = f"rust ({title.lower()})"
        body = section(text, title)
        rust_blocks = [code for fence, code in FENCE.findall(body or "") if fence == "rust"]
        if not rust_blocks:
            result.fail(f"{step}: no ```rust block in `## {title}`", "")
            continue
        out_dir = out_root / f"classic-{title.lower()}"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "main.rs").write_text("\n".join(rust_blocks))
        (out_dir / "main").unlink(missing_ok=True)
        code, output = run(RUSTC_CLASSIC, out_dir)
        if code != 0:
            result.fail(f"{step}: compile failed", output)
            continue
        code, output = run(["./main"], out_dir)
        if code != 0:
            result.fail(f"{step}: run failed (exit {code})", output)


def to_runnable(fence: str, code: str) -> str:
    """C# top-level statements must precede type declarations, so move the usage half to the top."""
    if fence != "csharp":
        return code
    lines = code.splitlines()
    marker = next((i for i, line in enumerate(lines) if USAGE_MARKER in line), None)
    if marker is None:
        return code
    header_prefixes = ("using ", "#:")  # usings + file-based-app directives stay on top
    header = [line for line in lines[:marker] if line.startswith(header_prefixes)]
    definitions = [line for line in lines[:marker] if not line.startswith(header_prefixes)]
    return "\n".join(header + lines[marker:] + [""] + definitions) + "\n"


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=300, env=ENV)
    return proc.returncode, proc.stdout + proc.stderr


def normalize(output: str) -> list[str]:
    return [line.rstrip().lower() for line in output.strip().splitlines()]


if __name__ == "__main__":
    sys.exit(main())
