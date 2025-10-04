## App features

- Basic support for zip archives?
- Option to flatten sources when adding to tarball (e.g., for [arXiv.org](https://arxiv.org/) submissions).
- A guided "wizard" `--interactive` mode.
- A `--watch` mode (using `Watchdog`?) to generate tarballs automatically upon source changes, so output tar remains in sync with TeX project.
- Handling very large working repositories: `git checkout` may be too slow in these cases.
- Summarise common errors from overly verbose LaTeX error log when compilation fails; save full log file in calling dir. 

## Documentation and miscellaneous

- ~~Add type hints for functions~~ Ongoing, mostly done
- ~~Improved doc strings~~ Ongoing, mostly done
- ~~Add man/info file~~ Initial version of man file added
- Add CONTRIBUTING.md to invite contributions.
- Snazzier README, including:
  * Visual proof of tartex in action (`asciinema rec`)
  * Slogan, badge, etc.
