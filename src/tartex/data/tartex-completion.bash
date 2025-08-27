# bash completion for tartex                               -*- shell-script -*-

_tartex_completions()
{
  local cur prev split
  _init_completion -s || return

  local mainext="@(tex|fls)"
  local tarext="tar.@(bz2|gz|xz)"

  # tilde expansion
  if [[ "$cur"=="\~*" ]]
  then
    eval cur="$cur"
  fi

  case $prev in 
    --help | --version | -!(-*)[hV])
      return
      ;;

    --completion | --@(bash|fish|zsh)-completions)
      return
      ;;

    --git-rev | -!(-*)g)
      COMPREPLY=( $(compgen -W "`git tag 2>/dev/null | awk '{ printf $1\" \"; }' || true`" -- "$cur") )
      COMPREPLY+=( $(compgen -W "`git branch 2>/dev/null | sed -E 's/[*]//' | awk '{ printf $1\" \"; }' || true`" -- "$cur") )
      return
      ;;

    --output | -!(-*)o)
      _filedir "$tarext"
      return
      ;;

    --latexmk-tex)
      COMPREPLY=($(compgen -W "dvi lualatex luatex pdf pdflua ps xdv xelatex" -- "$cur"))
      return
      ;;

    --add | --excl | -!(-*)[ax])
      _filedir
      return
      ;;

  esac

  $split && return

  if [[ $cur == -* ]]; then
      COMPREPLY=($(compgen -W '$(_parse_help "$1")' -- "$cur"))
      [[ ${COMPREPLY-} == *= ]] && compopt -o nospace
  fi

  _filedir "$mainext"
} &&
  complete -F _tartex_completions tartex

# ex: filetype=sh et ts=2 sw=2:
