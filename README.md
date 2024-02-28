# tartex

[![PyPI - Version](https://img.shields.io/pypi/v/tartex.svg)](https://pypi.org/project/tartex)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tartex.svg)](https://pypi.org/project/tartex)
[![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)

-----

TarTeX is a command-line utility to generate a tarball including all required
— but no more! — (non-system) source files to (re)compile your LaTeX project
elsewhere.

**Table of Contents**

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [License](#license)
- [Similar utilities](#similar-utilities)

## Features

* Defaults to including the least number of files needed to recompile your LaTeX project in the output tar file.
* Creates tarballs compatible with arXiv (and most journal) requirements.
* Automatically determines pdf or ps processing based on source dir contents.
* Supports different compression methods for output tarball.
* Does not modify or create files inside source directory itself.
* Preserves directory structure in generated tarball, i.e. no flattening.
* Handy options to allow edge cases.
* Native TAB-completion for common interactive shells: bash, fish, and zsh (help welcome for others).

## Installation

__Note__: Unless you provide a prepared ".fls" file as `FILENAME` input, you
must have `latexmk` and `pdflatex`, as well as a full LaTeX env installed to
allow compilation of your LaTeX project. `tartex` does not include any
system-wide files, such as standard TeX style files, classes, etc. in the tar
file.

### Using pipx

This is the easy way to install tagged releases.

```console
pipx install tartex
```

### From GitHub sources:

Compile using [hatch](https://hatch.pypa.io/latest/) to generate a wheel,
which may be then installed using `pipx` as follows:

```console
git clone https://github.com/badshah400/tartex.git
cd tartex
hatch build
pipx install ./dist/*.whl
```

## Usage

Supported OS: Potentially any POSIX-like, tested _only_ on Linux.

```console
usage: tartex [OPTIONS] FILENAME

Build a tarball including all source files needed to compile your LaTeX project
(version 0.4.1).

positional arguments:
  FILENAME                 input file name (with .tex or .fls suffix)

options:
  -h, --help               show this help message and exit
  -V, --version            print tartex version and exit
  -a, --add=PATTERNS       include additional files matching glob-style
                           PATTERN; separate multiple PATTERNS using commas
  -b, --bib                find and add bib file to tarball
  -l, --list               print list of files to include and quit
  -o, --output=NAME[.SUF]  output tar file name; tar compression mode will be
                           inferred from .SUF, if possible (default 'gz')
  -s, --summary            print a summary at the end
  -v, --verbose            increase verbosity (-v, -vv, etc.)
  -x, --excl=PATTERNS      exclude file names matching PATTERNS
  -j, --bzip2              recompress with bzip2 (.bz2) (overrides .SUF in
                           '-o')
  -J, --xz                 recompress with lzma (.xz) (overrides .SUF in '-o')
  -z, --gzip               recompress with gzip (.gz) (overrides .SUF in '-o')

Options for latexmk processing:
  --latexmk-tex=TEXMODE    force TeX processing mode used by latexmk; TEXMODE
                           must be one of: dvi, luatex, lualatex, pdf, pdflua,
                           ps, xdv, xelatex
  -F, --force-recompile    force recompilation even if .fls exists

Shell completion options:
  --completion             print shell completion guides for tartex
  --bash-completions       install bash completions for tartex
  --fish-completions       install fish completions for tartex
  --zsh-completions        install zsh completions for tartex
```

__Note__: If the source dir of your LaTeX project already contains the `.fls`
file previously generated by, say `latex -record` or `latexmk`, then `tartex`
will directly use that file to determine which input files to include in the
tarball. Otherwise, `tartex` will recompile your project using `latexmk` in a
temp dir and use the `.fls` file generated there. To be precise, recompilation
will invoke:

```console
latexmk -f -<texmode> -cd -outdir=<tmpdir> -interaction=nonstopmode filename
```

`texmode` is one of `pdf` or `ps` by default, as detemined from the contents of
the source dir. It may be overridden by the `--latexmk-tex` option.


## License

`tartex` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

## Similar utilities

* [bundledoc](https://ctan.org/tex-archive/support/bundledoc) is a post-processor for the `snapshot` package that bundles together all the classes, packages and files needed to build a given LaTeX document.
