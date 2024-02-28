# Main input
complete -c tartex -r -k -f -a "(__fish_complete_suffix .tex .fls)"

# Options that take an argument
complete -c tartex -s o -l output -f -r \
	-d "output tar file name (suffix may set tar compression)" \
	-k -a "(__fish_complete_suffix .tar.gz .tar.bz2 .tar.xz)"
complete -c tartex -f -l latexmk-tex -ra "dvi lualatex luatex pdf pdflua ps xdv xelatex" \
	-d "force TeX processing mode used by latexmk"
complete -c tartex -s a -l add -F -r -d "file names or patterns (comma separated) to include additionally"
complete -c tartex -s x -l excl -F -r -d "file names or patterns to exclude"

# Help/Version options
complete -c tartex -s h -l help -d "display help for tartex and exit"
complete -c tartex -s V -l Version -d "display tartex version and exit"

# Options that act as flags (no arguments)
complete -c tartex -f -s b -l bib -d "include bibliography (.bib) file in tar"
complete -c tartex -f -s F -l force-recompile -d "force recompilation even if .fls exists"
complete -c tartex -f -s l -l list -d "print a list of files to include and quit"
complete -c tartex -f -s s -l summary -d "print a summary at the end"
complete -c tartex -f -s v -l verbose -d "increase verbosity (-v, -vv, etc.)"

# Compression options
complete -c tartex -f -s j -l bzip2 -d "compress output with bzip2"
complete -c tartex -f -s z -l gzip -d "compress output with gzip"
complete -c tartex -f -s J -l xz -d "compress output with xz"

# Completions
complete -c tartex -f -l completion -d "print shell completion guides for tartex"
complete -c tartex -f -l bash-completions -d "install bash completions for tartex"
complete -c tartex -f -l fish-completions -d "install fish completions for tartex"
complete -c tartex -f -l zsh-completions -d "install zsh completions for tartex"
