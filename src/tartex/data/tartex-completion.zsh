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

# Helper function to get a list of git branches and tags
_tartex_get_git_refs() {
  git for-each-ref --format='%(refname:short)' refs/heads refs/tags
}

# Helper function to list only git branches and tags
_tartex_git_revs() {
  local -a refs
  refs=( $(_tartex_get_git_refs) )
  _describe 'git revisions' refs
}

typeset -A opt_args
tar_ext="*.tar.(bz2|gz|xz)"
_arguments -s -S \
  '1:input_file:_files -g "*.(fls|tex)"' \
  '(- : *)'{-h,--help}'[show this help message and exit]' \
  '(- : *)'{-V,--version}'[print tartex version and exit]' \
  '(completions -a --add)'{-a,--add=}'[include additional files matching glob PATTERN]:PATTERNS:_files' \
  '(completions -b --bib)'{-b,--bib}'[find and add bib file to tarball]' \
  '(completions -p --packages)'{-p,--packages}'[add names of used (La)TeX packages as a json file]' \
  '(completions -s --summary)'{-s,--summary}'[print a summary at the end]' \
  '*'{-v,--verbose}'[increase log verbosity (-v, -vv, etc.)]' \
  '(completions -x --excl)'{-x,--excl=}'[exclude file names matching PATTERNS]:PATTERNS:_files' \
  '(completions --latexmk-tex)'--latexmk-tex='[force latexmk processing mode]:TEXMODE:(dvi lualatex luatex pdf pdflua ps xdv xelatex)' \
  '(completions -F --force-recompile)'{-F,--force-recompile}'[force recompilation even if .fls exists]' \
  '(completions --with-pdf)'--with-pdf'[add final output PDF]' \
  + '(completions)' \
  '(- : *)--completion[print shell completion guides for tartex]' \
  '(- : *)--bash-completions[install bash completions for tartex]' \
  '(- : *)--fish-completions[install fish completions for tartex]' \
  '(- : *)--zsh-completions[install zsh completions for tartex]' \
  + '(recompression)' \
  '(completions -j --bzip2)'{-j,--bzip2}'[recompress tarball with bzip2 (.bz2)]' \
  '(completions -z --gzip)'{-z,--gzip}'[recompress tarball with gzip (.gz)]' \
  '(completions -J --xz)'{-J,--xz}'[recompress tarball with lzma (.xz)]' \
  + '(output)' \
  '(completions -l --list)'{-l,--list}'[print a list of files to include and quit]' \
  '(completions -o --output)'{-o,--output=}'[output tar filename]:FILENAME:_files -g "$tar_ext"' \
  '(completions --overwrite)'--overwrite'[overwrite existing tarfile]' \
  + '(git)' \
  '(completions -g --git-rev)'{-g,--git-rev=}'[add files at git revision]:git-revs:_tartex_git_revs' \
  && ret=0
return ret
