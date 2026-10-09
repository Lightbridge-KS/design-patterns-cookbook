# Design Pattern Cookbook

## Development

Tasks run through [`just`](https://just.systems) (`just` lists them):

| Recipe | What it does |
|---|---|
| `just preview` | Live-preview the book |
| `just render` | Render the book into `_book/` |
| `just verify [chapter.qmd …]` | Type-check and run every Modern Approach example in Python, C#, TypeScript, and Dart, and check that all four print the same output |
| `just check` | `verify` all chapters, then `render` |

Requirements: [Quarto](https://quarto.org) for `preview` / `render`; for `verify`, [uv](https://docs.astral.sh/uv/) (installs Python 3.13+ and the pinned mypy), the .NET 10 SDK, Node.js 23.6+, TypeScript (`tsc`), and the Dart SDK.
