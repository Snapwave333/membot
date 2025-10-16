#!/usr/bin/env python3
"""
Validate Mermaid code blocks embedded in Markdown files by attempting to render them
with mermaid-cli (mmdc) via npx. Fails if any block cannot be rendered.

Optional: set MERMAID_RENDER=1 to output SVGs under docs/assets/mermaid/ for each
validated block. SVG filenames are derived from source file names and block index.

Requirements:
- Node.js and npx available on PATH
- mermaid-cli (will be fetched on-demand by npx, or install globally via:
  npm i -g @mermaid-js/mermaid-cli
)

Usage (pre-commit):
  python scripts/validate_mermaid.py <files...>
If no files are provided, defaults to docs/**/*.md.
"""
import os
import re
import sys
import subprocess
import tempfile
from pathlib import Path
from glob import glob

MERMAID_BLOCK_RE = re.compile(r"^```mermaid\s*$")
CODE_FENCE_RE = re.compile(r"^```\s*$")

def extract_mermaid_blocks(text: str):
    blocks = []
    lines = text.splitlines()
    in_block = False
    buf = []
    for line in lines:
        if not in_block and MERMAID_BLOCK_RE.match(line):
            in_block = True
            buf = []
            continue
        if in_block and CODE_FENCE_RE.match(line):
            blocks.append("\n".join(buf).strip()+"\n")
            in_block = False
            buf = []
            continue
        if in_block:
            buf.append(line)
    return blocks


def validate_block(mermaid_src: str, render_svg_path: Path | None) -> tuple[bool, str]:
    """Return (ok, error_message). If render_svg_path is set, write SVG output."""
    # Ensure npx is available
    npx = os.environ.get("NPX", "npx")
    try:
        # Write temp .mmd file
        with tempfile.TemporaryDirectory() as td:
            mmd = Path(td) / "diagram.mmd"
            mmd.write_text(mermaid_src, encoding="utf-8")
            cmd = [npx, "-y", "@mermaid-js/mermaid-cli", "-i", str(mmd)]
            if render_svg_path:
                render_svg_path.parent.mkdir(parents=True, exist_ok=True)
                cmd += ["-o", str(render_svg_path)]
            else:
                # Render to a temp file but discard; use --quiet to reduce noise
                tmp_svg = Path(td) / "out.svg"
                cmd += ["-o", str(tmp_svg)]
            # Run
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                return False, (proc.stderr or proc.stdout or "Unknown mermaid-cli error")
            return True, ""
    except FileNotFoundError:
        return False, (
            "npx not found on PATH. Install Node.js and ensure npx is available. "
            "You can also install mermaid-cli globally: npm i -g @mermaid-js/mermaid-cli"
        )
    except Exception as e:
        return False, f"Unexpected error: {e}"


def main():
    # Collect target files
    files = sys.argv[1:]
    if not files:
        files = glob("docs/**/*.md", recursive=True)
    if not files:
        print("No Markdown files found to validate.")
        return 0
    render = os.environ.get("MERMAID_RENDER") == "1"
    failures = []
    checked_blocks = 0
    for f in files:
        p = Path(f)
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        blocks = extract_mermaid_blocks(text)
        if not blocks:
            continue
        for idx, block in enumerate(blocks, start=1):
            render_path = None
            if render:
                # e.g., docs/assets/mermaid/diagrams.md.1.svg
                name = f"{p.name}.{idx}.svg"
                render_path = Path("docs/assets/mermaid") / name
            ok, err = validate_block(block, render_path)
            checked_blocks += 1
            if not ok:
                failures.append((f, idx, err))
    if failures:
        print("Mermaid validation failed for the following blocks:")
        for f, idx, err in failures:
            print(f"- {f} (block #{idx}): {err}")
        print("\nHint: Install Node.js and try: npx -y @mermaid-js/mermaid-cli -i <file.mmd> -o out.svg")
        return 1
    print(f"Mermaid validation OK. Checked {checked_blocks} blocks across {len(files)} files.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
