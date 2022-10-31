#/usr/bin/env bash
if [[ -z "$ANSIBLE_COMPLETION_CACHE_TIMEOUT" ]]; then
    ANSIBLE_COMPLETION_CACHE_TIMEOUT=120 # sec
fi

_inventory_completions()
{
    local cur prev targetlist playlist taglist tasklist rolelist ansible_options roleName osName pname cmd_extra

    ansible_options="-t --tags --tag -T --target -S --skip -p --playbook -r --role
                    --ask-become-pass -k --ask-pass --ask-su-pass
                    -K --ask-sudo-pass --ask-vault-pass -b --become
                    --become-method --become-user -C --check -c
                    --connection -D --diff -e --extra-vars --flush-cache
                    --force-handlers -f --forks -h --help -i
                    --inventory-file -l --limit --list-hosts
                    --list-tags --list-tasks -M --module-path
                    --private-key --skip-tags --start-at-task
                    --step -S --su -R --su-user -s --sudo -U --sudo-user
                    --syntax-check -t --tags -T --timeout -u --user
                    --vault-password-file -v --verbose --version"

    COMPREPLY=()
    cur=${COMP_WORDS[COMP_CWORD]}
    prev=${COMP_WORDS[COMP_CWORD-1]}
    
    if [[ "${prev}" == "-T" ]] || [[ "${prev}" == "--target" ]]; then
        local cache_file="/tmp/ap_${ANSIBLE_L_ENV}_${ANSIBLE_L_INV}.targets"
        if [ -f "$cache_file" ]; then
            local timestamp=$(expr $(_timestamp) - $(_timestamp_last_modified $cache_file))
            if [ "$timestamp" -gt "$ANSIBLE_COMPLETION_CACHE_TIMEOUT" ]; then
                rm -f "$cache_file" > /dev/null 2>&1
                _get_targets "$cache_file"
            fi
        else
            _get_targets "$cache_file" "$cmd_extra"
        fi
        targetlist=$(cat "$cache_file")
        COMPREPLY=( $( compgen -W "${targetlist}" -- $cur ) )
    elif [[ "${prev}" == "-p" ]] || [[ "${prev}" == "--playbook" ]]; then
        local IFS=$'\n'
        playlist=$(find "$ANSIBLE_PLAYS_PATH" -maxdepth 1 -type f -iname *.yml -printf '%f\n' 2>/dev/null| sed 's/\.YML\|\.yml//g')
        COMPREPLY=( $( compgen -W "${playlist}" -- $cur ) )
    elif [[ "${prev}" == "-r" ]] || [[ "${prev}" == "--role" ]]; then
        local IFS=$'\n'
        rolelist=$(find "$ANSIBLE_ROLES_PATH" -maxdepth 1 -type d -printf '%f\n' 2>/dev/null)
        COMPREPLY=( $( compgen -W "${rolelist}" -- $cur ) )
    elif [[ "${prev}" == "-t" ]] || [[ "${prev}" == "--tags" ]] || [[ "${prev}" == "--tag" ]] || [[ "${prev}" == "-S" ]] || [[ "${prev}" == "--skip-tags" ]]; then
        local pname=$(_get_playbook_name)
        
        local cache_file="/tmp/ap_${ANSIBLE_L_ENV}_${ANSIBLE_L_INV}_${pname}.tags"
        case $pname in
        applyRole)
            roleName=$(_get_role_name)
            cache_file="${cache_file}_${roleName}"
        ;;
        sysAdmin)
            cmd_extra="-t get_tags"
        ;;
        esac

        if [ -f "$cache_file" ]; then
          local timestamp=$(expr $(_timestamp) - $(_timestamp_last_modified $cache_file))
            if [ "$timestamp" -gt "$ANSIBLE_COMPLETION_CACHE_TIMEOUT" ]; then
                rm -f "$cache_file" > /dev/null 2>&1
                _get_playbook_tags "$cache_file" "$cmd_extra"
            fi
        else
        # We need to cache the output because ansible-doc is so fucking slow
            _get_playbook_tags "$cache_file" "$cmd_extra"
        fi
        
        local IFS=$'\n'
        taglist=$(cat "$cache_file")
        COMPREPLY=( $( compgen -W "${taglist}" -- $cur ) )
    elif [[ "${prev}" == "--start-at-task" ]]; then
        local pname=$(_get_playbook_name)

        local cache_file="/tmp/ap_${ANSIBLE_L_ENV}_${ANSIBLE_L_INV}_${pname}.tags"
        case $pname in
        applyRole)
            roleName=$(_get_role_name)
            cache_file="${cache_file}_${roleName}"
        ;;
        sysAdmin)
            cmd_extra="-t get_tags"
        ;;
        esac

        if [ -f "$cache_file" ]; then
          local timestamp=$(expr $(_timestamp) - $(_timestamp_last_modified $cache_file))
            if [ "$timestamp" -gt "$ANSIBLE_COMPLETION_CACHE_TIMEOUT" ]; then
                rm -f "$cache_file" > /dev/null 2>&1
                _get_playbook_tasks "$cache_file" "$cmd_extra"
            fi
        else
        # We need to cache the output because ansible-doc is so fucking slow
            _get_playbook_tasks "$cache_file"
        fi
        
        local IFS=$'\n'
        taglist=$(cat "$cache_file")
        COMPREPLY=( $( compgen -W "${taglist}" -- $cur ) )
    elif [[ "${cur}" == -* ]] ; then
       COMPREPLY=( $( compgen -W "${ansible_options}" -- $cur ) )
    else
        _filedir
    fi
}

complete -F _inventory_completions run-playbook

_get_playbook_name()
{
    local index=0
    
    for word in ${COMP_WORDS[@]}; do
        index=$(expr $index + 1)
        if [ "$word" != "${COMP_WORDS[COMP_CWORD]}" ]; then
            if [[ "$word" == "-p" ]] || [[ "$word" == "--playbook" ]]; then
                echo ${COMP_WORDS[$index]}
                return 0
            fi
        fi
    done

    echo ""
    return 1
}

_get_role_name()
{
    local index=0
    
    for word in ${COMP_WORDS[@]}; do
        index=$(expr $index + 1)
        if [ "$word" != "${COMP_WORDS[COMP_CWORD]}" ]; then
            if [[ "$word" == "-r" ]] || [[ "$word" == "--role" ]]; then
                echo ${COMP_WORDS[$index]}
                return 0
            fi
        fi
    done

    echo ""
    return 1
}

_get_targets()
{
    local cache_file=$1
    eval "ansible-inventory $ANSIBLE_L_INVENTORY $ANSIBLE_L_VAULT --graph" 2>/dev/null | sed -e 's/[@:| ]//g' -e 's/^--//g' > $cache_file
}

_get_playbook_tasks()
{
    local cache_file=$1 cmd_extra=$2
    cmd=("${COMP_WORDS[@]}")
    unset 'cmd[${#cmd[@]}-1]'
    unset 'cmd[${#cmd[@]}-1]'
    eval "${cmd[@]} $cmd_extra -T all --list-tasks" 2> /dev/null | \
        grep ':.*\d*TAGS: \[.*\]' | \
        cut -d ":" -f 2 | \
        sed -e 's/\(.*\)TAGS$/\1/g' -e 's/^\s*//g' -e 's/\s*$//g' > $cache_file
}
_get_playbook_tags()
{
    local cache_file=$1 cmd_extra=$2
    cmd=("${COMP_WORDS[@]}")
    unset 'cmd[${#cmd[@]}-1]'
    unset 'cmd[${#cmd[@]}-1]'
    eval "${cmd[@]} $cmd_extra -T all --list-tags" 2> /dev/null | \
        grep -o "TAGS: \[.*\]" | \
        cut -d ":" -f 2 | \
        sed -e 's/^ \[\(.*\)\]$/\1/g' -e '/^$/ d' -e 's/, /\n/g' > $cache_file
}

_timestamp() {
    echo $(date +%s)
}

_timestamp_last_modified()  {
    local timestamp=''

    if [[ "$OSTYPE" == "linux"* ]]; then
        # linux
        timestamp=$(stat -c "%Z" $1)
    else
        # freebsd/darwin
        timestamp=$(stat -f "%Sm" -t "%s" $1)
    fi

    echo $timestamp
}

_md5() {
    local to_hash=$1
    local md5_hash=''

    if hash md5 2>/dev/null; then
        # freebsd/darwin
        md5_hash=$(md5 -q -s "$to_hash")
    else
        # linux
        md5_hash=$(echo "$to_hash" | md5sum |awk {'print $1'})
    fi

    echo $md5_hash
}