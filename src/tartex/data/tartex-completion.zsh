#compdef tartex
# ------------------------------------------------------------------------------
# MIT License
# 
# Copyright (c) 2024-present Atri Bhattacharya <atrib@duck.com>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ------------------------------------------------------------------------------
# Description
# -----------
# 
#  Completion script for tartex (https://github.com/badshah400/tartex).
# 
# ------------------------------------------------------------------------------
# Authors
# -------
# 
# * Atri B <atrib@duck.com>
# 
# ------------------------------------------------------------------------------
#
typeset -A opt_args
tar_ext="*.tar.(bz2|gz|xz)"
_arguments -s -S \
  '(- *)'{-h,--help}'[show this help message and exit]' \
  '(-a --add)'{-a,--add=}'[Include additional file names matching glob-style PATTERNS]:PATTERNS:_files' \
  '(-b --bib)'{-b,--bib}'[find and add bib file to tarball]' \
  '(-l --list)'{-l,--list}'[Print a list of files to include and quit (no tarball generated)]' \
  '(-o --output)'{-o,--output=}'[Name of output tar]:FILENAME:_files -g "$tar_ext"' \
  '(-s --summary)'{-s,--summary}'[Print a summary at the end]' \
  '(-v --verbose)'{-v,--verbose}'[Print file names added to tarball]' \
  '(-x --excl)'{-x,--excl=}'[Exclude file names matching PATTERNS]:PATTERNS:_files' \
  '(-j --bzip2)'{-j,--bzip2}'[bzip2 (.tar.bz2) compression (overrides other compression settings)]' \
  '(-J --xz)'{-J,--xz}'[lzma (.tar.xz) compression (overrides other compression settings)]' \
  '(-z --gzip)'{-z,--gzip}'[gzip (.tar.gz) compression (overrides other compression settings)]' \
  '(- *)'{-V,--version}'[Print tartex version]' \
  '--latexmk-tex=[Force TeX processing mode used by latexmk]:TEXMODE:(dvi luatex lualatex pdf pdflua ps xdv xelatex)' \
  '(-F --force-recompile)'{-F,--force-recompile}'[Force recompilation even if .fls exists]' \
  '--completion[Print bash completion for tartex]' \
  '--bash-completion[Install bash completions for tartex]' \
  '--fish-completion[Install fish completions for tartex]' \
  '--zsh-completion[Install zsh completions for tartex]' \
  '*:INPUT_FILE:_files -g "*.(fls|tex)"' && ret=0
return ret
