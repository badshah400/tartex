# Changelog

## [0.4.1] 2024-02-29

### Fixed

- Improve consistency of option descriptions for completions across different shells.
- Add option grouping for zsh completions to only suggest non-conflicting options.
- Add missing option (`--completion`) for fish.

## [0.4.0] 2024-02-27

### Added

- Rich markup when displaying output or prompts.
- Show spinner when waiting on LaTeX compile.
- New options to install completions for bash, fish¹, and zsh¹ shells.
- [docs] Clearer help strings for options and more consistent formatting.

¹ Experimental support, needs more testing.

### Changed

- Use "-" for long form options (e.g. "--latexmk-tex") instead of "_" ("--latexmk_tex")

### Fixed

- Catch exception when latexmk is missing from system or not in `PATH`.


## [0.3.0] 2024-02-18

### Added

- Better logging of warnings to user as well as debugging based on `-v` or
  `-vv`.
- When `OUTPUT` points to an existing dir, create tar file in that dir with the
  main tex file name.
- Process `~` expansion in user entered name for conflict resolution.

### Changed

- Indicate existing file name in message when user enters a new name for tar
  file that conflicts with an existing name.

### Fixed

- Notify user for permission error before writing to tar and exit. 
- Don't open tmpdir if not recompiling LaTeX.
- Omit, with a warning, any missing INPUT files from tarball.
- Run latexmk on `.tex` file even if input file entered is `.fls`.
- Use `.tex` file attr for BytesIO added to tar.
- Do `.expanduser()` early when processing output arg.
- Fix last non-tar suffix, if any, in `OUTPUT` being dropped from tar file
  name.
- Correct message when LaTeX recompile is forced.


## [0.2.2] 2024-02-14

__Note__: This release fixes a major bug relating to relative paths as inputs.

- Fix main file path resolution when a relative path is passed as input for
  filename.


## [0.2.1] 2024-02-13

- Include .ind index files by default when LaTeX project involves makeindex.
- Minor formatting fix for `--list` output.
- Fix: For generated files included in tarball, set user/group attributes from
  main file.
- Add License and OS info in pyproject.toml.


## [0.2.0] 2024-02-11

- Determine compression from user specified target name if possible.
- Better prompt message for user input during conflict.
- Improved pdf vs ps TeX processing detection for latexmk, and a new option to
  allow the user to force a TeX processor.
- New option: Use `-F` to force recompile latex even if `.fls` is in srcdir.
- Extensive testing using pytest.
- Fix: Don't show full path of .bbl file for `-l`.
- Fix: Use full path if rel path cannot be resolved.
- Fix: Even if `-b` is set, ignore missing .bib.


## [0.1.1] 2024-02-09

- Fix tar dest when new tarfile name is entered.
- Expand `~` for user specified or entered dest.


## [0.1.0] 2024-02-08

_Initial release_
