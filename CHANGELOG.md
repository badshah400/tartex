# Changelog

## [0.10.2] 2025-09-21

### Fixes

- When using `--git-rev`, do not attempt to checkout revision if repository is unclean; raise error early.
- Restore original git tree when process raises error while working in repo checked out at specified revision.
- Better logs when main input file is not found.

## [0.10.1] 2025-09-20

### Fixed

- Fix extra dot in extension when using new name to resolve tar name conflict.

## [0.10.0] 2025-09-20

### Added

- Generate and use cache file to track changes to input dependencies, based on content hashes.
- Do not use or update cache when using in-project '.fls' file as input or when forcing a recompile (`-F`).
- Use `rich` as logging handler for better style and formatting of log messages.

### Fixed

- Do not raise error on miss supplementary files when using `-F`/`--force-recompile` as they will be regenerated anyway.
- Fix duplicate info-log messages when adding bib file (and related styles).
- Clearer, terser logs all around.

## [0.9.0] 2025-09-14

### Added

- Add `--check` option to check if all files needed for recompiling project will be included in tarball.
- Add `--only-check` option to print a detailed report on missing, necessary, and unnecessary files to be included, without actually generating the tar file.
- Make file pattern matching for `--add` or `--excl` options recurse into sub-directories starting at source directory.

### Fixed

- Do not exclude main tex file even if matched by `--excl` pattern.
- Improved shell completions for `--git-ref`.
- Avoid adding duplicate files when using `--git-rev`.
- Suppress unnecessary conflict dialog in `--list` mode.
- Fix incorrect setting of working dir.
- Better help messages, logging, and documentation all around.

## [0.8.0] 2025-08-26

### Added

- Option `--git-rev=REV` to process and add tracked files from git repo at revision `REV` (default: `HEAD`).
- Add initial man file built using `help2man` and ship it in wheel/source.
 
### Fixed

- Clean up tarball if latexmk compilation fails.
- Improve displayed error messages if latexmk fails.
- Flash-ier summary messages using emoji unicode characters.
- Clean up blank tarball if latexmk fails.
- Improved, re-organised help message.

## [0.7.0] 2025-08-17

### Added

- Add command line option to overwrite target output if it already exists.
- Include local bib style file (if any) when using the '-b'/'--bib' option.
- Add `--dry-run` option as alias to `--list`.
- Add `--with-pdf` option to allow adding final output PDF directly or after compilation.
- Clear out uid/gid attributes from archived files.
- Add 300 sec timeout duration when running latexmk and raise error when compilation exceeds it.

### Fixed

- Add bst filename to pkg list if necessary.
- Keep ext for local style file in pkg list.
- Fix type error when using `.as_posix()` on excluded patterns.
- Set out-of-source archived files' mtime to fls file mtime.

## [0.6.0] 2025-05-13

### Added

- Append '.fls' or '.tex' extension to input filename if it does not have one.
- Drop Python 3.8 support.
- Add Python 3.13 support.

## [0.5.0] 2024-03-15

### Added

- Option "-p/--packages": Save a `TeXPackages.json` file, listing system and
  local latex packages used, inside output tarball.
- Rich formatting for printed messages for completion options.

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
