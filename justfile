# Design Patterns Cookbook — run `just` to list recipes

# List recipes
default:
    @just --list

# Live-preview the book in a browser
preview:
    quarto preview

# Render the whole book into _book/
render:
    quarto render

# Type-check and run the Modern Approach examples: all chapters, or the given ones (-h for options)
verify *args:
    uv run scripts/verify_modern.py {{args}}

# Dry gate: verify every example, then render the book
check: verify render
