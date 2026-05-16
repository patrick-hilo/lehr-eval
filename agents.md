# Agent Instructions

- When reading large files, check the line count first with `wc -l`.
- If a file is over 2,000 lines, read it in chunks instead of reading the whole file at once.
- For Python execution, use `uv run` rather than direct `python`, `python3`, `pip`, or `pipx` commands.
- For standalone Python scripts, use PEP 723 inline script metadata and run them with `uv run python script.py`.
- Never delete `.stfolder`, `.stversions`, or `.stignore` files or folders.
