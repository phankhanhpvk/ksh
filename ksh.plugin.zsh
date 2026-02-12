# ------------------------------------------------------------------------------
# Helper: Resolve 'Include' directives in SSH config
# ------------------------------------------------------------------------------
function _ksh_resolve_includes() {
    local main_config="$1"
    local -a config_files
    config_files=("$main_config")

    if [[ ! -f "$main_config" ]]; then
        return
    fi
    
    local include_paths
    # Parse 'Include' lines
    include_paths=$(grep -i "^Include " "$main_config" | sed 's/^Include //I')

    if [[ -n "$include_paths" ]]; then
        setopt localoptions nullglob
        for config_path in ${(z)include_paths}; do
            # Handle tilde expansion
            config_path="${config_path/#\~/$HOME}"
            
            # Handle relative path
            if [[ "$config_path" != /* ]]; then
                config_path="${main_config:h}/$config_path"
            fi
            
            # Add matching files
            for f in $~config_path; do
                [[ -f "$f" ]] && config_files+=("$f")
            done
        done
    fi

    echo "${config_files[@]}"
}

# ------------------------------------------------------------------------------
# Helper: Extract Host and HostName from config files
# ------------------------------------------------------------------------------
function _ksh_list_hosts() {
    local -a files
    files=("$@")
    
    awk '
        function print_entry() {
            if (aliases != "") {
                if (hostname == "") hostname = "N/A"
                if (region == "") region = "unknown"
                printf "%-60s %-30s %s\n", aliases, hostname, region
            }
        }
        /^\s*# Region:/ {
            pending_region = $3
        }
        tolower($1) == "host" {
            print_entry()
            aliases = ""
            hostname = ""
            region = pending_region
            pending_region = "unknown"
            for (i=2; i<=NF; i++) {
                if ($i != "*") aliases = (aliases ? aliases " " : "") $i
            }
        }
        tolower($1) == "hostname" {
            hostname = $2
        }
        END {
            print_entry()
        }
    ' "${files[@]}" | sort -u
}

# ------------------------------------------------------------------------------
# Main Function
# ------------------------------------------------------------------------------
function ksh() {
    local jump_host=""
    local sync_mode=0
    local query=""

    # Argument Parsing
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --sync)
                sync_mode=1
                shift
                ;;
            -j|--jump)
                jump_host="${KSH_JUMP_HOST:-sb-monitor}"
                shift
                ;;
            -h|--help)
                echo "Usage: ksh [query] [--sync] [-j|--jump]"
                return 0
                ;;
            *)
                query="$1"
                shift
                ;;
        esac
    done

    # Handle Sync
    if [[ $sync_mode -eq 1 ]]; then
        _ksh_sync_ec2
        return $?
    fi

    # Check Config
    if [[ ! -f ~/.ssh/config ]]; then
        echo "Error: ~/.ssh/config not found."
        return 1
    fi

    # Resolve Config Files
    local -a config_files
    config_files=($(_ksh_resolve_includes ~/.ssh/config))

    # Get Hosts
    local hosts
    hosts=$(_ksh_list_hosts "${config_files[@]}")

    if [[ -z "$hosts" ]]; then
        echo "No hosts found in: ${config_files[*]}"
        return 1
    fi

    # Select Host (fzf or fallback)
    local selected_line
    if command -v fzf >/dev/null 2>&1; then
        # Use fzf for selection
        selected_line=$(echo "$hosts" | fzf --height 50% --layout=reverse --border --prompt="SSH > " --query="$query" --select-1 --exit-0)
    else
        # Fallback logic
        if [[ -n "$query" ]]; then
            selected_line=$(echo "$hosts" | grep -i "$query" | head -n 1)
        else
            local OLD_IFS=$IFS
            IFS=$'\n'
            echo "Select a host:"
            select h in $(echo "$hosts"); do
                if [[ -n "$h" ]]; then
                    selected_line="$h"
                    break
                fi
            done
            IFS=$OLD_IFS
        fi
    fi

    # Connect
    if [[ -n "$selected_line" ]]; then
        local host_alias
        local host_region
        # Parse output from _ksh_list_hosts: alias hostname region
        host_alias=$(echo "$selected_line" | awk '{print $1}')
        host_region=$(echo "$selected_line" | awk '{print $3}')
        
        local ssh_opts=()
        
        # Logic: If jump is enabled (jump_host is set usually to default),
        # try to find a more specific per-region jump host.
        if [[ -n "$jump_host" ]]; then
            if [[ -n "$host_region" && "$host_region" != "unknown" ]]; then
                # Convert region to env var format: us-east-1 -> US_EAST_1
                local region_key="${host_region//-/_}"
                local region_env_var="KSH_JUMP_HOST_${region_key:u}"
                
                # Zsh indirect expansion to get value
                local region_specific_jump="${(P)region_env_var}"
                
                if [[ -n "$region_specific_jump" ]]; then
                    jump_host="$region_specific_jump"
                    # echo "Using Region Jump Host: $jump_host"
                fi
            fi
            
            ssh_opts+=(-J "$jump_host")
        fi

        echo "Connecting to \033[1;32m$host_alias\033[0m..."
        if [[ -n "$jump_host" ]]; then
             echo "  via \033[1;34m$jump_host\033[0m"
        fi
        
        ssh "${ssh_opts[@]}" "$host_alias"
    fi
}

# ------------------------------------------------------------------------------
# Alias: ksh with Jump
# ------------------------------------------------------------------------------
function kshj() {
    ksh --jump "$@"
}

# ------------------------------------------------------------------------------
# Sync Function (Delegates to Python)
# ------------------------------------------------------------------------------
function _ksh_sync_ec2() {
    if ! command -v aws &> /dev/null; then
        echo "Error: 'aws' command not found. Please install AWS CLI."
        return 1
    fi

    if ! command -v python3 &> /dev/null; then
        echo "Error: 'python3' command not found. Please install Python 3."
        return 1
    fi

    # Resolve Python script location
    local plugin_dir="${${(%):-%x}:A:h}"
    local python_script="$plugin_dir/src/main.py"
    
    # Check for boto3
    python3 -c "import boto3" 2>/dev/null
    if [[ $? -ne 0 ]]; then
        echo "Error: Python library 'boto3' not found."
        echo "Please install it: pip3 install boto3"
        return 1
    fi
    
    if [[ ! -f "$python_script" ]]; then
        echo "Error: Python sync script not found at $python_script"
        return 1
    fi

    # Run Sync
    PYTHONPATH="$plugin_dir/src" python3 "$python_script"
    local ret=$?

    if [[ $ret -ne 0 ]]; then
        echo "Sync failed."
        return $ret
    fi

    # Ensure Include
    local ec2_config_file=~/.ssh/ksh_ec2_config
    local main_config=~/.ssh/config
    
    if ! grep -q "Include $ec2_config_file" "$main_config"; then
        echo "Adding 'Include $ec2_config_file' to header of $main_config"
        local temp_config=$(mktemp)
        echo "Include $ec2_config_file" > "$temp_config"
        if [[ -f "$main_config" ]]; then
            cat "$main_config" >> "$temp_config"
        fi
        mv "$temp_config" "$main_config"
    fi
}
