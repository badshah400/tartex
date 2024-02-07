# tartex

<!--- [![PyPI - Version](https://img.shields.io/pypi/v/tartex.svg)](https://pypi.org/project/tartex) --->
<!---[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tartex.svg)](https://pypi.org/project/tartex) --->

[![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)

-----

TarTeX is a command-line utility to generate a tarball including all
(non-system) source files needed to compile your LaTeX project.

**Table of Contents**

- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Installation

In the (hopefully near!) future, when it is ready for release, installing
tartex will be one `pip(x)` call away.  For now, the source code may be
compiled using [hatch](https://hatch.pypa.io/latest/) to generate a wheel,
which may be installed using `pipx` as follows:

```console
git clone https://github.com/badshah400/tartex.git
cd tartex
hatch build
pipx install ./dist/*.whl
```

__Note__: You must have `latexmk` and `pdflatex`, as well as a full LaTeX env
installed. `tartex` will not include any system-wide files, such as TeX style
files, classes, etc. in the tar file.

## Usage

Supported OS: Potentially any POSIX-like, tested _only_ on Linux.

```console
usage: tartex [-h] [-a ADD] [-b] [-l] [-o OUTPUT] [-s] [-v] [-x EXCL] fname

Build a tarball including all source files needed to compile your LaTeX project (version 0.1.0a1).

positional arguments:
  fname                 Input file name (.tex or .fls) (mandatory)

options:
  -h, --help            show this help message and exit
  -a ADD, --add ADD     Comma separated list of additional files (wildcards allowed!) to include (loc relative to main TeX file)
  -b, --bib             find and add bib file to tarball
  -l, --list            Print a list of files to include and quit (no tarball generated)
  -o OUTPUT, --output OUTPUT
                        Name of output tar.gz file (w/o the .tar.gz extension)
  -s, --summary         Print a summary at the end
  -v, --verbose         Display file names added to tarball
  -x EXCL, --excl EXCL  Comma separated list of files (wildcards allowed!) to exclude (loc relative to main TeX file)
```

## License

`tartex` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
