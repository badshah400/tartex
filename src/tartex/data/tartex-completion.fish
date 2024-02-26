# Main input
complete -c tartex -r -k -f -a "(__fish_complete_suffix .tex .fls)"

# Options that take an argument
complete -c tartex -s o -l output -f -r \
	-d "Name of output tar NAME[.SUF] (.SUF may set tar compression)" \
	-k -a "(__fish_complete_suffix .tar.gz .tar.bz2 .tar.xz)"
complete -c tartex -f -l latexmk-tex -ra "dvi luatex lualatex pdf pdflua ps xdv xelatex" \
	-d "Force TeX processing mode used by latexmk"
complete -c tartex -s a -l add -F -r
complete -c tartex -s x -l excl -F -r

# Help/Version options
complete -c tartex -s h -l help -d "Display help for tartex and exit"
complete -c tartex -s V -l Version -d "Display tartex version and exit"

# Options that act as flags (no arguments)
complete -c tartex -f -s b -l bib -d "Include bibliography (.bib) file in tar"
complete -c tartex -f -s v -l verbose -d "Increase verbosity of output (may be used multiple times)"
complete -c tartex -f -s s -l summary -d "Print a summary at the end"
complete -c tartex -f -s b -l bib -d "Include bibliography (.bib) file in tar"
complete -c tartex -f -s l -l list -d "Print a list of files to include and quit (no tarball generated)"
complete -c tartex -f -s F -l force-recompile -d "Force recompilation even if .fls exists"

# Compression options
complete -c tartex -f -s j -l bzip2 -d "Re-compress output tar with bzip2"
complete -c tartex -f -s z -l gzip -d "Re-compress output tar with gzip"
complete -c tartex -f -s J -l xz -d "Re-compress output tar with xz"

# Completions
complete -c tartex -f -l bash-completion -d "Install bash completions for tartex"
complete -c tartex -f -l fish-completion -d "Install fish completions for tartex"
complete -c tartex -f -l zsh-completion -d "Install zsh completions for tartex"
