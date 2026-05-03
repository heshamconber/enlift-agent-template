# src/

Put your agent's code here — scripts, helpers, API wrappers, whatever the agent needs to run.

Examples:
- `src/generate_handbook.py` — main logic for a document-generation agent
- `src/fetch_tickets.py` — pulls tickets from an external system
- `src/format_output.py` — formats results before returning to the operator

If your agent is purely prompt-driven (no custom code needed), this folder can stay empty.

Remember to add any new scripts to the allow list in `.claude/settings.json`:
```json
"Bash(python3 src/your_script.py *)"
```
