# ksh - Fast SSH Zsh Plugin

**ksh** is an Oh My Zsh plugin that helps manage and connect to SSH servers quickly. It uses Python to synchronize instances from AWS.

## Features

### 🚀 Smart Connection
- **Fuzzy Search:** Uses `fzf` to search for servers by Alias or IP extremely fast.
- **Jump Host Support:** Easily connect via a jump host with just one command.
- **Compatibility:** Automatically reads and parses existing `~/.ssh/config`.

### ☁️ AWS EC2 Sync (Ultra Fast)
- **Parallel Sync:** Scans all AWS Regions in parallel, reducing sync time from minutes to seconds.
- **Automation:** Automatically checks and generates the config file (`~/.ssh/ksh_ec2_config`) and includes it in the main config.
- **Flexibility:** Filter servers by name (Regex), exclude Spot instances, prioritize Private IPs, etc.

---

## Installation

### Requirements
- **Zsh** & **Oh My Zsh**
- **AWS CLI** (configured with `aws configure`)
- **Python 3**
- **fzf**

### Plugin Installation
1. Clone the repository into your Oh My Zsh plugins directory:
   ```bash
   git clone https://github.com/phankhanhpvk/ksh.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/ksh
   ```

2. Add `ksh` to the plugins list in `~/.zshrc`:
   ```zsh
   plugins=(... ksh)
   ```

3. Reload the shell:
   ```bash
   source ~/.zshrc
   ```

---

## Usage

### 1. SSH Connection
Use the `ksh` command to search and connect:

```bash
ksh [server-name-or-ip]
```

- If no argument is provided: Opens the `fzf` search interface.
- If an argument is provided: Connects to the exact or first matching server.

### 2. Connect via Jump Host
Use `kshj` or `ksh --jump` to connect via a Jump Host (default is `sb-monitor`):

```bash
kshj my-private-server
```

*(Note: Ensure the host `sb-monitor` is defined in your ssh config)*

### 3. Install fzf
This plugin requires `fzf` to function correctly. Please install it:

```bash
# MacOS
brew install fzf

# Ubuntu/Debian
sudo apt-get install fzf
```

### 4. Sync EC2 (Sync)
Command to coordinate server list from AWS:

```bash
ksh --sync
```

### Sync Configuration (in `~/.zshrc`)

You can customize sync behavior using the following environment variables:

| Environment Variable | Description | Example |
| :--- | :--- | :--- |
| `KSH_JUMP_HOST` | Default Jump Host (when using `--jump` or `kshj`) | `sb-monitor` |
| `KSH_JUMP_HOST_<REGION>` | Jump Host for a specific region (used when jump is enabled) | `jump-host-use1` |
| `KSH_SYNC_NO_SPOT` | Ignore Spot Instances (True/False) | `true` |
| `KSH_SYNC_PRIVATE_IP` | Always use Private IP instead of Public IP | `true` |
| `KSH_SYNC_EXCLUDE_REGEX` | Regex to exclude servers by name | `.*(test|dev).*` |
| `KSH_SYNC_USER` | Default SSH User for synced servers | `ubuntu` |
| `KSH_SYNC_PORT` | Default SSH Port | `22` |

**Configuration Example:**
```zsh
export KSH_SYNC_NO_SPOT=true
export KSH_SYNC_USER=ec2-user
export KSH_SYNC_EXCLUDE_REGEX="^eks-.*"
```

---

## Project Structure
The plugin is organized using a modern Python module model:

```
ksh/
├── ksh.plugin.zsh          # Entry point for Zsh
└── src/
    ├── main.py             # Main script
    ├── core/               # Config & Logging
    ├── providers/          # Cloud modules (AWS)
    └── utils/              # Helper utilities (SSH Config)
```
