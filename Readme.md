# PDF Metadata Editor

A simple Windows desktop application for batch-editing PDF metadata (Title, Author, Subject, Creator, Producer, Keywords) and setting initial view defaults. Built with PySide6 and pypdf.

## Features

- **Recursive PDF scanning** — selects all `.pdf` files in the chosen folder and every subfolder
- **Batch metadata editing** — set, clear, or leave unchanged each metadata field for every file at once
- **Filename-based Title** — optionally set Title from the filename, or from the text after the first space
- **Initial view defaults** — automatically removes OpenAction and PageLayout, sets PageMode to `UseNone`
- **Preserve folder structure** — outputs files into the same relative subdirectories as the input
- **In-place or separate output** — save to a new `_processed` folder, or overwrite originals directly

## User Guide

### 1. Setup

1. Click **Select...** next to "PDF Folder (Input)" and choose the top-level folder containing your PDFs
2. Choose where to save results:
   - **Default:** the app suggests `[Input Folder]_processed` (recommended)
   - **Custom:** click **Select...** under "Output Folder" to pick another location
   - **In-place:** check "Output to Input Folder" to overwrite the originals (use with caution)

### 2. Configure Metadata Actions

For each field (Title, Author, Subject, Creator, Producer, Keywords), choose an action from the dropdown:

| Action | Behaviour |
|--------|-----------|
| Leave Unchanged | Does not modify this field in the output PDF |
| Clear … | Writes an empty string, effectively removing the metadata value |
| Set Specific … | Writes whatever you type into the text box |
| Use Filename *(Title only)* | Writes the PDF filename (without `.pdf`) as the Title |
| Use Filename (After First Space) *(Title only)* | Same, but strips everything before the first space |

**Defaults:** all fields default to their "Clear" action.

### 3. Start Processing

Click **Start Processing**.

- A progress bar shows overall completion
- The status line shows the current file and any errors
- Click **Stop** at any time to halt after the current file finishes

When complete, a summary dialog shows how many files succeeded or failed.

## Developer Guide

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or `pip`

### Run from source

```bash
uv run pdf-meta-editor-gui.py
```

Or with plain Python:

```bash
pip install pypdf PySide6
python pdf-meta-editor-gui.py
```

### Build the MSI installer

The build is configured entirely in `pyproject.toml` using `cx_Freeze`. No `setup.py` required.

```bash
uv run cxfreeze build bdist_msi
```

The installer is produced at:

```
dist/PDFBatchMetadataEditor.msi
```

For a clean rebuild:

```bash
Remove-Item -Recurse -Force build, dist
uv run cxfreeze build bdist_msi
```

### Installer configuration (pyproject.toml)

Key sections under `[tool.cxfreeze]`:

- `executables` — entry script, base (`gui` = no console window), target `.exe` name
- `build_exe.packages` / `excludes` / `bin_excludes` — what to include or omit from the frozen build
- `bdist_msi` — MSI GUID, default install path, output filename, shortcuts

### Known packaging fix

When cx_Freeze bundles the app, it places dependency DLLs (e.g. `zlib.dll`) into a `lib/` subfolder next to the executable. Windows does not search subfolders for DLLs automatically, so the app includes a startup patch that adds the `lib` directory to the DLL search path when running as a frozen build.

## Dependencies

- [pypdf](https://github.com/py-pdf/pypdf) — PDF reading and writing
- [PySide6](https://doc.qt.io/qtforpython/) — Qt GUI framework
- [cx_Freeze](https://marcelotduarte.github.io/cx_Freeze/) — freeze Python scripts into executables / MSI
