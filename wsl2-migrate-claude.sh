#!/bin/bash
# Canvas Learning System - Migrate Claude Code Config from Windows to WSL2
#
# Copies: CLAUDE.md, commands, skills, plugins, settings, project memory
# Adapts: PowerShell hooks → bash hooks, Windows paths → Linux paths
#
# Usage (run inside WSL2):
#   bash wsl2-migrate-claude.sh
#
# Prerequisites:
#   - WSL2 Ubuntu with Claude Code installed
#   - Windows Claude Code config at /mnt/c/Users/Heishing/.claude/

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# Guard: must run inside WSL2
if ! grep -qi microsoft /proc/version 2>/dev/null; then
    error "This script must run inside WSL2."
fi

WIN_CLAUDE="/mnt/c/Users/Heishing/.claude"
WSL_CLAUDE="$HOME/.claude"
WIN_PROJECT_KEY="C--Users-Heishing-Desktop-canvas-canvas-learning-system"

if [ ! -d "$WIN_CLAUDE" ]; then
    error "Windows Claude config not found at $WIN_CLAUDE"
fi

info "=== Step 1: Create WSL2 ~/.claude directory structure ==="
mkdir -p "$WSL_CLAUDE"/{commands,skills,plugins,scripts}

info "=== Step 2: Copy CLAUDE.md (global instructions) ==="
if [ -f "$WIN_CLAUDE/CLAUDE.md" ]; then
    cp "$WIN_CLAUDE/CLAUDE.md" "$WSL_CLAUDE/CLAUDE.md"
    info "Copied CLAUDE.md"
fi

info "=== Step 3: Copy commands (93 files) ==="
if [ -d "$WIN_CLAUDE/commands" ]; then
    cp -r "$WIN_CLAUDE/commands/"*.md "$WSL_CLAUDE/commands/" 2>/dev/null || true
    COUNT=$(ls "$WSL_CLAUDE/commands/"*.md 2>/dev/null | wc -l)
    info "Copied $COUNT command files"
fi

info "=== Step 4: Copy skills (9 directories) ==="
if [ -d "$WIN_CLAUDE/skills" ]; then
    cp -r "$WIN_CLAUDE/skills/"* "$WSL_CLAUDE/skills/" 2>/dev/null || true
    COUNT=$(ls -d "$WSL_CLAUDE/skills/"*/ 2>/dev/null | wc -l)
    info "Copied $COUNT skill directories"
fi

info "=== Step 5: Copy plugins config ==="
for f in installed_plugins.json known_marketplaces.json blocklist.json install-counts-cache.json; do
    if [ -f "$WIN_CLAUDE/plugins/$f" ]; then
        cp "$WIN_CLAUDE/plugins/$f" "$WSL_CLAUDE/plugins/$f"
    fi
done
if [ -d "$WIN_CLAUDE/plugins/marketplaces" ]; then
    cp -r "$WIN_CLAUDE/plugins/marketplaces" "$WSL_CLAUDE/plugins/" 2>/dev/null || true
fi
info "Copied plugins config"

info "=== Step 6: Create Linux guard-hook.sh (from PowerShell) ==="
cat > "$WSL_CLAUDE/guard-hook.sh" << 'GUARDHOOK'
#!/bin/bash
# Claude Code Guard Hook - PreToolUse Bash Command Interceptor (Linux version)
# Converted from guard-hook.ps1 for WSL2
# Exit 0 = allow | Exit 2 = block

PAYLOAD=$(cat)
COMMAND=$(echo "$PAYLOAD" | jq -r '.tool_input.command // empty' 2>/dev/null)
[ -z "$COMMAND" ] && exit 0

# Dangerous command patterns (PCRE-style, checked with grep -P)
PATTERNS=(
    # File/Directory Deletion
    '(?:^|[;&|`]|\$\()\s*rm\s+'
    '(?:^|[;&|`]|\$\()\s*rmdir\s+'
    '(?:^|[;&|`]|\$\()\s*shred\s+'
    '(?:^|[;&|`]|\$\()\s*truncate\s+'
    '\bfind\b.*(?:-delete|-exec\s+rm)'
    '\bxargs\s+rm\b'
    # Git Destructive
    '\bgit\s+reset\s+--(?:hard|merge)'
    '\bgit\s+push\s.*(?:-f\b|--force)'
    '\bgit\s+clean\s+-[a-z]*f'
    '\bgit\s+checkout\s+--\s'
    '\bgit\s+restore\b'
    '\bgit\s+branch\s+-D\b'
    '\bgit\s+stash\s+(?:drop|clear)\b'
    '\bgit\s+reflog\s+expire\b'
    '\bgit\s+tag\s+(?:-d|--delete)\b'
    # Docker Destructive
    '\bdocker\s+(?:rm|rmi|stop)\b'
    '\bdocker\s+(?:container|volume|image|network)\s+rm\b'
    '\bdocker\s+(?:volume|system)\s+prune\b'
    '\bdocker\s+compose\s+(?:down|rm)\b'
    # Process Killing
    '\bkill\s+(?:-9|-SIGKILL|-KILL)'
    '(?:^|[;&|`]|\$\()\s*pkill\b'
    '(?:^|[;&|`]|\$\()\s*killall\b'
    # System/Disk
    '(?:^|[;&|`]|\$\()\s*(?:shutdown|reboot|halt|poweroff)\b'
    '(?:^|[;&|`]|\$\()\s*dd\s+'
    '\b(?:mkfs|fdisk)\b'
    # Database Destructive
    '\b(?:DROP|TRUNCATE)\s+(?:TABLE|DATABASE|SCHEMA)\b'
    '\bdropdb\b'
    '\bredis-cli\s+FLUSH'
    '\bcypher-shell\b.*\b(?:DROP|DELETE)\b'
    # Cloud Destructive
    '\bkubectl\s+delete\b'
    '\bterraform\s+destroy\b'
    '\bhelm\s+uninstall\b'
    '\baws\s+s3\s+rm\b.*--recursive'
    '\bgcloud\b.*\bdelete\b'
    # Remote Code Execution
    '\bcurl\b.*\|\s*(?:ba)?sh'
    '\bwget\b.*\|\s*(?:ba)?sh'
    # Package Manager
    '\bnpm\s+unpublish\b'
    '\bpip\s+uninstall\b'
)

for pattern in "${PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qPi "$pattern" 2>/dev/null; then
        echo "{\"hookResponse\":{\"decision\":\"block\",\"reason\":\"[GUARD] BLOCKED: $pattern | Command: $COMMAND\"}}"
        exit 2
    fi
done

exit 0
GUARDHOOK
chmod +x "$WSL_CLAUDE/guard-hook.sh"
info "Created guard-hook.sh"

info "=== Step 7: Create Linux notification hook ==="
cat > "$WSL_CLAUDE/claude-hook-notify.sh" << 'NOTIFYHOOK'
#!/bin/bash
# Claude Code Notification Hook (Linux/WSL2 version)
# Uses notify-send for desktop notifications via WSLg

PAYLOAD=$(cat)
EVENT=$(echo "$PAYLOAD" | jq -r '.hook_event_name // empty' 2>/dev/null)
MSG=$(echo "$PAYLOAD" | jq -r '.message // empty' 2>/dev/null)

case "$EVENT" in
    Stop)          BODY="Response finished" ;;
    Notification)  BODY="$MSG" ;;
    *)             BODY="$EVENT: $MSG" ;;
esac

# Try notify-send (WSLg native), fallback to powershell.exe toast
if command -v notify-send &>/dev/null; then
    notify-send "Claude Code" "$BODY" 2>/dev/null || true
elif command -v powershell.exe &>/dev/null; then
    powershell.exe -Command "[console]::beep(800,200)" 2>/dev/null || true
fi

exit 0
NOTIFYHOOK
chmod +x "$WSL_CLAUDE/claude-hook-notify.sh"
info "Created claude-hook-notify.sh"

info "=== Step 8: Create WSL2-adapted settings.json ==="
cat > "$WSL_CLAUDE/settings.json" << 'SETTINGS'
{
  "permissions": {
    "allow": [
      "Bash",
      "Read",
      "Glob",
      "Grep",
      "Agent",
      "Edit",
      "Write",
      "WebFetch",
      "WebSearch",
      "NotebookEdit",
      "Skill",
      "EnterPlanMode",
      "ExitPlanMode",
      "mcp__pencil"
    ],
    "deny": [
      "Bash(docker compose down *)",
      "Bash(docker compose rm *)",
      "Bash(docker rm *)",
      "Bash(rm -rf *)",
      "Bash(rm -fr *)",
      "Bash(rm -r *)",
      "Bash(rm .env*)",
      "Bash(rm .git *)",
      "Bash(rm .claude *)",
      "Bash(rm CLAUDE.md*)",
      "Bash(git reset --hard *)",
      "Bash(git push --force *)",
      "Bash(git push -f *)",
      "Bash(git clean -f*)",
      "Bash(git checkout -- .)",
      "Bash(git branch -D *)",
      "Bash(git stash drop *)",
      "Bash(git stash clear *)",
      "Bash(kill -9 *)",
      "Bash(pkill *)",
      "Bash(killall *)",
      "Bash(dd *)",
      "Bash(mkfs*)",
      "Bash(curl * | bash *)",
      "Bash(curl * | sh *)",
      "Bash(pip uninstall *)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$HOME/.claude/guard-hook.sh\"",
            "timeout": 10
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$HOME/.claude/claude-hook-notify.sh\"",
            "timeout": 15
          }
        ]
      }
    ],
    "Notification": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$HOME/.claude/claude-hook-notify.sh\"",
            "timeout": 15
          }
        ]
      }
    ]
  },
  "enabledPlugins": {
    "hookify@claude-plugins-official": false,
    "notify-toast@claude-plugins-official": false,
    "typescript-lsp@claude-plugins-official": true,
    "pyright-lsp@claude-plugins-official": true,
    "rust-analyzer-lsp@claude-plugins-official": true,
    "superpowers@claude-plugins-official": true
  },
  "language": "中文",
  "effortLevel": "high",
  "autoUpdatesChannel": "latest",
  "terminalBellOnComplete": true,
  "showClearContextOnPlanAccept": true
}
SETTINGS
info "Created settings.json (hooks adapted for Linux)"

info "=== Step 9: Copy settings.local.json ==="
if [ -f "$WIN_CLAUDE/settings.local.json" ]; then
    # Copy and remove Windows-specific entries
    jq 'del(.permissions.allow[] | select(test("powershell|cmd\\.exe")))' \
        "$WIN_CLAUDE/settings.local.json" > "$WSL_CLAUDE/settings.local.json" 2>/dev/null \
        || cp "$WIN_CLAUDE/settings.local.json" "$WSL_CLAUDE/settings.local.json"
    info "Copied settings.local.json (cleaned Windows-specific entries)"
fi

info "=== Step 10: Migrate project memory ==="
# Claude Code maps project paths to directory names by replacing separators with dashes.
# Windows: C:\Users\...\canvas-learning-system → C--Users-Heishing-Desktop-canvas-canvas-learning-system
# WSL2 needs to determine the key after first run.
#
# Strategy: copy memory to a staging area, then create a helper to link it
# after Claude Code creates the project directory on first run.

WIN_MEMORY="$WIN_CLAUDE/projects/$WIN_PROJECT_KEY/memory"
STAGING="$WSL_CLAUDE/memory-staging"

if [ -d "$WIN_MEMORY" ]; then
    mkdir -p "$STAGING"
    cp "$WIN_MEMORY/"*.md "$STAGING/" 2>/dev/null || true
    COUNT=$(ls "$STAGING/"*.md 2>/dev/null | wc -l)
    info "Staged $COUNT memory files to $STAGING"
fi

# Create helper script to finalize memory migration after first Claude run
cat > "$WSL_CLAUDE/finalize-memory.sh" << 'FINALIZE'
#!/bin/bash
# Run this AFTER your first Claude Code session in the canvas project.
# It copies staged memory files to the correct project directory.

CLAUDE_DIR="$HOME/.claude"
STAGING="$CLAUDE_DIR/memory-staging"
PROJECT_DIR="$HOME/canvas/canvas-learning-system"

if [ ! -d "$STAGING" ]; then
    echo "No staged memory found. Nothing to do."
    exit 0
fi

# Find the project key Claude Code created
PROJECT_KEY=$(ls -d "$CLAUDE_DIR/projects/"*canvas-learning-system* 2>/dev/null | head -1)

if [ -z "$PROJECT_KEY" ]; then
    echo "Project directory not found yet. Run 'claude' once in $PROJECT_DIR first."
    exit 1
fi

MEMORY_DIR="$PROJECT_KEY/memory"
mkdir -p "$MEMORY_DIR"

cp "$STAGING/"*.md "$MEMORY_DIR/" 2>/dev/null
COUNT=$(ls "$MEMORY_DIR/"*.md 2>/dev/null | wc -l)
echo "Copied $COUNT memory files to $MEMORY_DIR"
echo "You can now remove staging: rm -rf $STAGING"
FINALIZE
chmod +x "$WSL_CLAUDE/finalize-memory.sh"
info "Created finalize-memory.sh (run after first Claude session)"

echo ""
info "=== Migration complete! ==="
echo ""
echo "Summary:"
echo "  CLAUDE.md      → copied"
echo "  commands/      → $(ls "$WSL_CLAUDE/commands/"*.md 2>/dev/null | wc -l) files"
echo "  skills/        → $(ls -d "$WSL_CLAUDE/skills/"*/ 2>/dev/null | wc -l) directories"
echo "  settings.json  → adapted (powershell → bash hooks)"
echo "  guard-hook     → .ps1 → .sh conversion"
echo "  notification   → .ps1 → notify-send"
echo "  memory         → staged (run finalize-memory.sh after first session)"
echo ""
echo "Next steps:"
echo "  1. cd ~/canvas/canvas-learning-system"
echo "  2. claude                              # first session (creates project dir)"
echo "  3. bash ~/.claude/finalize-memory.sh   # copy memory to project dir"
echo "  4. Verify: claude /help                # check skills/commands load"
