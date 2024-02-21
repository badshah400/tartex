#/usr/bin/env bash
#
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

    --output | -!(-*)o)
      _filedir "$tarext"
      return
      ;;

    --latexmk_tex)
      COMPREPLY=($(compgen -W "dvi luatex lualatex pdf pdflua ps xdv xelatex" -- "$cur"))
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

# ex: filetype=sh
