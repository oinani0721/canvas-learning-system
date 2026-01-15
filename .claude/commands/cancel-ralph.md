# Cancel Ralph Loop

Stop any active ralph-loop iteration.

## Usage

```
/cancel-ralph
```

## Execution

When this command is invoked:

1. Check if `.claude/ralph-loop.local.md` exists
2. If it exists, delete the file and confirm cancellation
3. If it doesn't exist, inform user that no active loop was found

### Confirmation Message

After successful cancellation:
```
Ralph loop cancelled. The iteration state file has been removed.
```

If no active loop:
```
No active ralph loop found. Nothing to cancel.
```
