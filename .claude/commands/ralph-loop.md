# Ralph Loop - Iterative Task Execution

Run Claude in a continuous loop with the same prompt until task completion.

## Usage

```
/ralph-loop "<your task prompt>" [--max-iterations N] [--completion-promise "<promise>"]
```

## Parameters

- `prompt`: The task you want Claude to work on iteratively
- `--max-iterations N`: Maximum number of iterations (default: 10)
- `--completion-promise "<text>"`: Text that signals task completion (default: none)

## Examples

```
/ralph-loop "Fix all TypeScript errors in the project" --max-iterations 5
/ralph-loop "Implement the user authentication feature" --completion-promise "All tests passing"
```

---

$ARGUMENTS

---

## Execution

When this command is invoked, create the state file `.claude/ralph-loop.local.md` with the following format:

```markdown
---
iteration: 1
max_iterations: {max_iterations from args, default 10}
completion_promise: {completion_promise from args, or "null"}
created: {current timestamp}
---

{The user's prompt from arguments}
```

Then begin working on the task specified in the prompt.

### Iteration Rules

1. Work on the task until you reach a natural stopping point
2. If you complete the task or detect the completion promise, announce completion
3. Otherwise, the stop hook will automatically continue the next iteration
4. Each iteration increments the counter until max_iterations is reached

### State File Location

The state file MUST be created at: `.claude/ralph-loop.local.md` (relative to project root)

### Important Notes

- The stop hook reads this file to determine if iteration should continue
- If the file doesn't exist when session ends, no iteration occurs
- Delete the file manually or use `/cancel-ralph` to stop iteration
