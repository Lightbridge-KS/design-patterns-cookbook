# Design Pattern Cookbook

## Development

Tasks run through [`just`](https://just.systems) (`just` lists them):

| Recipe | What it does |
|---|---|
| `just preview` | Live-preview the book |
| `just render` | Render the book into `_book/` |
| `just verify [chapter.qmd …]` | Type-check and run every Modern Approach example in Python, C#, TypeScript, Dart, and Rust, and check that all five print the same output; also compile and run the classic Rust examples |
| `just check` | `verify` all chapters, then `render` |

Requirements: [Quarto](https://quarto.org) for `preview` / `render`; for `verify`, [uv](https://docs.astral.sh/uv/) (installs Python 3.13+ and the pinned mypy), the .NET 10 SDK, Node.js 23.6+, TypeScript (`tsc`), the Dart SDK, and Rust 1.85+ with clippy (`rustup component add clippy`).
