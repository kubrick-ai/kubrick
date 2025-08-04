_kubrick() {
    local cur prev words cword
    
    # Manual initialization for zsh compatibility
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    case $prev in
        kubrick)
            COMPREPLY=($(compgen -W "deploy destroy --help -h" -- "$cur"))
            return
            ;;
    esac
}
complete -F _kubrick kubrick