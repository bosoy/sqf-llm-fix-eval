# sqf-llm-fix-eval

Benchmarks LLMs on fixing Arma 3 SQF bugs. The agent sees only three MCP tools: `get_task`, `submit_answer`, `get_results`. Traps, checks and the results table live on the server side — the agent never sees them.

Бенчмарк LLM-моделей на исправление SQF-багов (Arma 3). Агент видит только три инструмента: get_task, submit_answer, get_results. Ловушки, проверки и таблица живут у сервера — агент их не видит.

---

## setup / установка

1. `pip install -r requirements.txt` (python 3.10+, mcp 1.x).
2. Keep the benchmark folder OUTSIDE the agent's workspace (e.g. `C:/tools/sqf-llm-fix-eval`), otherwise the agent can read the analyzer and tailor the answer.
   Держи папку бенчмарка ВНЕ рабочей папки проекта, иначе агент прочитает анализатор и подгонит ответ.
3. Connect to the agent:
   - claude code: `claude mcp add sqf-llm-fix-eval -- python C:/tools/sqf-llm-fix-eval/mcp_server.py`
   - other clients (json): `{"mcpServers": {"sqf-llm-fix-eval": {"command": "python", "args": ["C:/tools/sqf-llm-fix-eval/mcp_server.py"]}}}`
4. Copy `SKILL.md` into the agent's skills.
5. Say in chat: "check the model on arma 3" / «проверь модель на работу с арма3».

## what it does / что делает

- **get_task** — issues a one-time ticket plus the buggy SQF source.
- **submit_answer** — takes the ticket, model name and the fixed file; writes `variants/model__N.sqf` and rebuilds the table.
- **get_results** — summary across models and the path to `results.xlsx`.

## traps / ловушки (analyze.py)

1. `_instigator` used in the wrong place
2. comparing `_victim` to other objects
3. teamkill check missing `side` + `group`
4. `remoteExec ["hint"...]` with a non-local target
5. `setVariable` without the 3rd argument `true`

Score = sum of t1..t5 (0 = clean, 5 = all bugs caught). This is a text heuristic, not an in-game test.

## protection / защита

Each ticket is one-shot; the score is never returned to the agent. Does not protect against reading server files from disk (hence step 2) or running all runs in one context.

## files / файлы

- `mcp_server.py` — MCP server (three tools)
- `analyze.py` — parses `variants/` into `results.xlsx`
- `tasks/2-1-killreward/` — task, buggy source, in-game test
- `suspicious.json` — suspicious-construct templates
- `variants/`, `results.xlsx`, `backup/` — ignored, these are run results

MIT License.
