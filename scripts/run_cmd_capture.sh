#!/usr/bin/env bash
# scripts/run_cmd_capture.sh — capture-and-tail wrapper for hook-invoked commands
#
# Replaces the "pytest ... | tail -N" pattern that silently swallows non-zero
# exit codes due to POSIX pipeline semantics. Captures full stdout+stderr to a
# tmp file, prints last N lines + the file path on failure, exits with the
# original exit code.
#
# Usage:
#   scripts/run_cmd_capture.sh --cwd <dir> --tail <N> -- <cmd> [args...]
#
# Flags:
#   --cwd <dir>   Change to <dir> before running <cmd> (default: current dir)
#   --tail <N>    On failure, show the last N lines of output (default: 120)
#   --            Stop flag parsing — everything after this is the command + args
#
# Behavior:
#   1. mktemp /tmp/run_cmd_capture_<pid>_<ts>.log
#   2. cd <cwd> && exec <cmd> [args] &> <tmp>
#   3. capture exit code RC
#   4. on RC != 0: print "[TEST FAILURE]" header + path + last N lines to stderr
#   5. exit RC
#
# The temp file is intentionally NOT cleaned up on success or failure — operators
# need to be able to `cat` it for full traceback. Periodic cleanup is the user's
# responsibility (e.g. `find /tmp -name 'run_cmd_capture_*' -mtime +7 -delete`).
#
# This script uses neither `set -o pipefail` nor pipes itself, so its own exit
# code is exactly the wrapped command's exit code with no transformation.
#
# Part of openspec change fix-test-infra-paralysis (2026-04-07).

set -u  # error on undefined vars; do NOT set -e (we want to propagate, not abort)

WRAPPER_CWD=""
TAIL_LINES=120

# Parse flags up to '--'
while [[ $# -gt 0 ]]; do
    case "$1" in
        --cwd)
            WRAPPER_CWD="$2"
            shift 2
            ;;
        --tail)
            TAIL_LINES="$2"
            shift 2
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "[run_cmd_capture] unknown flag: $1" >&2
            echo "[run_cmd_capture] usage: $0 --cwd <dir> --tail <N> -- <cmd> [args...]" >&2
            exit 64  # EX_USAGE
            ;;
    esac
done

if [[ $# -eq 0 ]]; then
    echo "[run_cmd_capture] no command given after '--'" >&2
    echo "[run_cmd_capture] usage: $0 --cwd <dir> --tail <N> -- <cmd> [args...]" >&2
    exit 64
fi

# Create the persistent log file
LOGFILE="$(mktemp -t "run_cmd_capture_$$_$(date +%s).log.XXXXXX")"

# Optional cd
if [[ -n "$WRAPPER_CWD" ]]; then
    if ! cd "$WRAPPER_CWD" 2>/dev/null; then
        echo "[run_cmd_capture] cannot cd to: $WRAPPER_CWD" >&2
        exit 65  # EX_DATAERR
    fi
fi

# Run the wrapped command, capturing combined stdout+stderr.
# Using "$@" preserves argv quoting; &> redirects both streams. We do NOT
# pipe to tee — that would re-introduce the pipefail problem we're solving.
"$@" &> "$LOGFILE"
RC=$?

if [[ $RC -ne 0 ]]; then
    {
        echo ""
        echo "[TEST FAILURE] exit code: $RC"
        echo "[TEST FAILURE] full output: $LOGFILE"
        echo "[TEST FAILURE] last $TAIL_LINES lines:"
        echo "----------------------------------------"
        tail -n "$TAIL_LINES" "$LOGFILE"
        echo "----------------------------------------"
    } >&2
fi

exit $RC
