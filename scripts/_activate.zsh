#compdef activate

# 
# Description
# -----------
# Completion script for activate ansible inventory
#
# Author
# ------
# Arash Kesahvarzi
#

__environment() {
    # env
    local list_items
    declare -a list_items

    list_items=( ${(@f)"$(
        find "$(realpath $PWD)/env" -mindepth 1 -maxdepth 1 -type d -printf '%f\n'  2> /dev/null | grep -Ev "^(\.|example)" 2> /dev/null
    )"})
    compadd -a list_items
}

__inventory() {
    local environment list_items
    environment=${words[2]}
    declare -a list_items

    list_items=( ${(@f)"$(
        find "$(realpath $PWD)/env/$environment" -mindepth 1 -maxdepth 1 -type d -printf '%f\n'  2> /dev/null | grep -Ev "^(\.|example)" 2> /dev/null
    )"})
    compadd -a list_items
}

__vault() {
    # vault
    local list_items
    declare -a list_items

    list_items=( ${(@f)"$(
        find "$(realpath $PWD)/vault" -mindepth 1 -maxdepth 1 -type f -name '*.pass' -printf '%f\n' | sed -e 's/.pass//'  2> /dev/null
    )"})
    
    compadd -a list_items
}

__activate() {
    local curcontext="$curcontext" context state state_descr line help="-h --help"    

    _arguments -n \
        ':environment:__environment' \
        '::inventory:__inventory' \
        '-v:vault:__vault'
}
__activate "$@"
