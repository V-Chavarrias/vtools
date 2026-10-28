# change-cover

`change-cover` updates the first slide of PowerPoint presentations. It can
replace the title, author text, and image while writing the modified
presentations to a separate directory.

## Install

Install directly from the GitHub repository:

```powershell
python -m pip install "git+https://github.com/V-Chavarrias/vtools.git@main#subdirectory=packages/change_cover"
```

Or clone the repository and install from the checkout:

```powershell
git clone https://github.com/V-Chavarrias/vtools.git
Set-Location vtools
python -m pip install .\packages\change_cover
```

Replace `main` with a package release tag such as
`change-cover-v0.1.0` when a reproducible version is required.

## Use

### Command line

```powershell
change-cover `
  --input-dir .\day4 `
  --output-dir .\day4_modified `
  --title "A new title" `
  --author "Victor Chavarrias\nWillem Ottevanger" `
  --old-author Victor `
  --image .\cover.png
```

The `--title`, `--author`, and `--image` options are optional. `\n` in text
arguments is converted to a line break.

The module form is equivalent:

```powershell
python -m change_cover `
  --input-dir .\day4 `
  --output-dir .\day4_modified
```

### Python

The same operation is available through `update_directory()`:

```python
from pathlib import Path

from change_cover import update_directory

processed_files = update_directory(
    input_dir=Path("day4"),
    output_dir=Path("day4_modified"),
    title="A new title",
    author=r"Victor Chavarrias\nWillem Ottevanger",
    old_author="Victor",
    image_path=Path("cover.png"),
)
print(f"Updated {processed_files} presentation(s).")
```

For a single presentation, use `update_presentation()` with an input and
output path. The `title`, `author`, and `image_path` arguments are optional.
