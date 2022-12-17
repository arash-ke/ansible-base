#compdef run-playbook

# 
# Description
# -----------
# Completion script for ansible-playbook wraper
#
# Author
# ------
# Arash Kesahvarzi
#
__ai_targetlist()
{
    local cache_policy targetlist_cachename

    zstyle -s ":completion:${curcontext}:" cache-policy cache_policy
    if [[ -z "$cache_policy" ]]; then
        zstyle ":completion:${curcontext}:" cache-policy __ansible_caching_policy
    fi

    targetlist_cachename="_${ANSIBLE_L_ENV}_${ANSIBLE_L_INV}_targets"
    if [[ ${(P)+DISABLE_COMP_CACHE} -eq 1 ]] || [[ ${(P)+targetlist_cachename} -eq 0 ]] || _cache_invalid ${targetlist_cachename#_} || ! _retrieve_cache ${targetlist_cachename#_}
    then
        zle -R "Getting targets..."
        set -A $targetlist_cachename ${(@f)"$(
            eval "ansible-inventory $ANSIBLE_L_INVENTORY $ANSIBLE_L_VAULT --graph" 2>/dev/null | \
            sed -e 's/[@:| ]//g' -e 's/^--//g'
        )"}
        _store_cache ${targetlist_cachename#_} $targetlist_cachename
    fi

    _sequence compadd -a $targetlist_cachename -q
}

__ai_tasklist()
{
    local cache_policy cmd tasklist_cachename roleName cmdExtra
    declare -a cmd
    for i in $words; do
        if [[ "$i" == "-t" ]]; then
            break;
        fi
        cmd+=($i);
    done
    playbook_name=$(__get_playbook_name)
    zstyle -s ":completion:${curcontext}:" cache-policy cache_policy
    if [[ -z "$cache_policy" ]]; then
        zstyle ":completion:${curcontext}:" cache-policy __ansible_caching_policy
    fi

    tasklist_cachename="_${ANSIBLE_L_ENV}_${ANSIBLE_L_INV}_${playbook_name}_tasks"

    case $playbook_name in
    (applyRole)
        roleName=$(__get_role_name)
        tasklist_cachename="${tasklist_cachename}_${roleName}"
    ;;
    (sysAdmin)
        cmdExtra="-t get_tags"
    ;;
    esac
    if  [[ ${DISABLE_COMP_CACHE} -eq 1 ]] || [[ ${(P)+tasklist_cachename} -eq 0 ]] || _cache_invalid ${tasklist_cachename#_} || ! _retrieve_cache ${tasklist_cachename#_}
    then
        zle -R "Getting tasks..."
        set -A $tasklist_cachename ${(f)"$(
            eval "$cmd $cmdExtra -T all --list-tasks" 2> /dev/null | \
            grep ':.*\d*TAGS: \[.*\]' | \
            cut -d ":" -f 2 | \
            sed -e 's/\(.*\)TAGS$/\1/g' -e 's/^\s*//g' -e 's/\s*$//g'
        )"}
        _store_cache ${tasklist_cachename#_} $tasklist_cachename
    fi
    
    _sequence compadd -a $tasklist_cachename -q
}

__ai_taglist()
{
    local cache_policy cmd __taglist taglist_cachename roleName cmdExtra
    declare -a cmd
    for i in $words; do
        if [[ "$i" == "-t" ]]; then
            break;
        fi
        cmd+=($i);
    done
    playbook_name=$(__get_playbook_name)
    zstyle -s ":completion:${curcontext}:" cache-policy cache_policy
    if [[ -z "$cache_policy" ]]; then
        zstyle ":completion:${curcontext}:" cache-policy __ansible_caching_policy
    fi

    taglist_cachename="_${ANSIBLE_L_ENV}_${ANSIBLE_L_INV}_${playbook_name}_tags"

    case $playbook_name in
    (applyRole)
        roleName=$(__get_role_name)
        taglist_cachename="${taglist_cachename}_${roleName}"
    ;;
    (sysAdmin)
        cmdExtra="-t get_tags"
    ;;
    esac
    
    if  [[ ${DISABLE_COMP_CACHE} -eq 1 ]] || [[ ${(P)+taglist_cachename} -eq 0 ]] || _cache_invalid ${taglist_cachename#_} || ! _retrieve_cache ${taglist_cachename#_}
    then
        zle -R "Getting tags..."
        set -A $taglist_cachename ${(f)"$(
            eval "$cmd $cmdExtra -T all --tags=all,never --list-tags" 2> /dev/null | \
            grep -o 'TAGS: \[.*\]' | \
            cut -d ':' -f 2 | \
            sed -e 's/^ \[\(.*\)\]$/\1/g' -e '/^$/ d' -e 's/, /\n/g'
        )"}
        _store_cache ${taglist_cachename#_} $taglist_cachename
    fi
    _sequence compadd -a $taglist_cachename -q
}

__get_playbook_name()
{
    local index=0 next
    
    for word in ${words[@]}; do
        index=$(expr $index + 1)
        next=$(expr $index + 1)
        if [[ "$word" == "-p" ]] || [[ "$word" == "--playbook" ]]; then
            echo ${words[$next]}
            return 0
        fi
    done

    echo ""
    return 1
}

__get_role_name()
{
    local index=0 next
    
    for word in ${words[@]}; do
        index=$(expr $index + 1)
        next=$(expr $index + 1)
        if [[ "$word" == "-r" ]] || [[ "$word" == "--role" ]]; then
            echo ${words[$next]}
            return 0
        fi
    done

    echo ""
    return 1
}
__ai_playlist()
{
    local playlist
    local playpath="$ANSIBLE_PLAYS_PATH"

    # local IFS=$'\n'
    playlist=( ${(@f)"$(
        find "$playpath" -mindepth 1 -maxdepth 1 -type f -iname '*.yml' -printf '%f\n' 2> /dev/null | sed 's/\.YML\|\.yml//g'
    )"})
    compadd -a playlist
}

__ai_rolelist()
{
    local rolelist
    local rolepath="$ANSIBLE_ROLES_PATH"

    # local IFS=$'\n'
    rolelist=( ${(@f)"$(
        find "$rolepath" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2> /dev/null
    )"})
    compadd -a rolelist
}

__run-playbook() {
    local curcontext="$curcontext" context state state_descr line help="-h --help"    
    typeset -A opt_args

    _arguments -C \
        '(-p --playbook)'{-p,--playbook}'[Playbook]: :__ai_playlist' \
        '(-P --ansible-port)'{-P,--ansible-port}'[Overwrite Ansible port]' \
        '(-H --ansible-host)'{-H,--ansible-host}'[Overwrite Ansible host]' \
        '(-a --apply-role)'{-a,--apply-role}'[Apply <role>]: :__ai_rolelist' \
        \*{-t,--tags=}'[only run plays and tasks tagged with these values]: :__ai_taglist' \
        \*{-T,--target}'[Run on <target>]: :__ai_targetlist' \
        \*{-r,--role}'[Specify <role>]: :__ai_rolelist' \
        '(- *)'{-h,--help}'[show this help message and exit]' \
        '(- *)--version[show program'"'"'s version number and exit]' \
        '(--ask-pass -k)'{-k,--ask-pass}'[ask for SSH password]' \
        '(--ask-su-pass)--ask-su-pass[ask for su password]' \
        '(--ask-sudo-pass -K)'{-K,--ask-sudo-pass}'[ask for sudo password]' \
        '(--ask-vault-pass)--ask-vault-pass[ask for vault password]' \
        '(--check -C)'{-C,--check}"[don't make any changes; instead, try to predict some of the changes that may occur]" \
        '(--connection -c)'{-c,--connection=}'[connection type to use (default=smart)]' \
        '(--diff -D)'{-D,--diff}'[when changing (small) files and templates, show the differences in those files; works great with --check]' \
        '(--extra -e-vars)'{-e,--extra-vars=}'[set additional variables as key=value or YAML/JSON]' \
        '(--flush-cache)--flush-cache[clear the fact cache]' \
        '(--force-handlers)--force-handlers[run handlers even if a task fails]' \
        '(--forks -f)'{-f,--forks=}'[specify number of parallel processes to use (default=5)]' \
        '(--inventory -i-file)'{-i=,--inventory-file=}'[specify inventory host file (default=/etc/ansible/hosts)]:files:_files' \
        '(--limit -l)'{-l,--limit=}'[further limit selected hosts to an additional pattern]: :->__ai_targetlist' \
        '(--list-hosts)--list-hosts[outputs a list of matching hosts; does not execute anything else]' \
        '(--list-tasks)--list-tasks[list all tasks that would be executed]' \
        '(--list-tags)--list-tags[list all tags that would be executed]' \
        '(--module-path -M)'{-M,--module-path=}'[specify path(s) to module library (default=None)]: :_files' \
        '(--private-key)--private-key=PRIVATE_KEY_FILE[use this file to authenticate the connection]' \
        \*{-S,--skip-tags=}'[only run plays and tasks whose tags do not match these values]: :__ai_taglist' \
        '(--start-at-task)--start-at-task=[start the playbook at the task matching this name]: :__ai_tasklist' \
        '(--step)--step[one-step-at-a-time: confirm each task before running]' \
        '(--su)--su=[run operations with su]' \
        '(--su-user -R)'{-R,--su-user=}'[run operations with su as this user (default=root)]' \
        '(--sudo -U-user)'{-U,--sudo-user=}'[desired sudo user (default=root)]' \
        '(--sudo -s)'{-s,--sudo}'[run operations with sudo (nopasswd)]' \
        \*{-j,--json}'[provide variable as json format]' \
        '(--syntax-check)--syntax-check[perform a syntax check on the playbook, but do not execute it]' \
        '(--timeout=)--timeout=[override the SSH timeout in seconds (default=10)]' \
        '(--user -u)'{-u,--user=}'[connect as this user (default=logged_in_user)]' \
        '(--only-projects -o)'{-o,--only-projects}'[Only apply these projects (regex)]' \
        '(--vault-password-file=)--vault-password-file=[vault password file]' \
        '(--verbose -v)'{-v,--verbose}'[verbose mode (-vvv for more, -vvvv to enable connection debugging)]' \
        '*:files:_files'

    case $state in
        (tasklist)
        __ai_tasklist
        ;;
        (taglist)
        __ai_taglist
        ;;
        (playlist)
        __ai_playlist
        ;;
        (targetlist)
        __ai_targetlist
        ;;
        (rolelist)
        __ai_rolelist
        ;;
    esac
}

__ansible_caching_policy() {
  oldp=( "$1"(Nmh+1) )     # 1 hour
  (( $#oldp ))
}

__run-playbook "$@"
