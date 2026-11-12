# sqf-llm-fix-eval

Benchmarks LLMs on fixing Arma 3 SQF bugs. The agent sees only three MCP tools: `get_task`, `submit_answer`, `get_results`. Traps, checks and the results table live on the server side — the agent never sees them.

## setup

1. `pip install -r requirements.txt` (python 3.10+, mcp 1.x).
2. Keep the benchmark folder OUTSIDE the agent's workspace (e.g. `C:/tools/sqf-llm-fix-eval`), otherwise the agent can read the analyzer and tailor the answer.
3. Connect to the agent:
   - claude code: `claude mcp add sqf-llm-fix-eval -- python C:/tools/sqf-llm-fix-eval/mcp_server.py`
   - other clients (json): `{"mcpServers": {"sqf-llm-fix-eval": {"command": "python", "args": ["C:/tools/sqf-llm-fix-eval/mcp_server.py"]}}}`
4. Copy `SKILL.md` into the agent's skills.
5. Say in chat: "check the model on arma 3".

## what it does

- **get_task** — issues a one-time ticket plus the buggy SQF source.
- **submit_answer** — takes the ticket, model name and the fixed file; writes `variants/model__N.sqf` and rebuilds the table.
- **get_results** — summary across models and the path to `results.xlsx`.

## traps (analyze.py)

1. `_instigator` used in the wrong place
2. comparing `_victim` to other objects
3. teamkill check missing `side` + `group`
4. `remoteExec ["hint"...]` with a non-local target
5. `setVariable` without the 3rd argument `true`

Score = sum of t1..t5 (0 = clean, 5 = all bugs caught). This is a text heuristic, not an in-game test.

## protection

Each ticket is one-shot; the score is never returned to the agent. Does not protect against reading server files from disk (hence step 2) or running all runs in one context.

## files

- `mcp_server.py` — MCP server (three tools)
- `analyze.py` — parses `variants/` into `results.xlsx`
- `tasks/2-1-killreward/` — task, buggy source, in-game test
- `suspicious.json` — suspicious-construct templates
- `variants/`, `results.xlsx`, `backup/` — ignored, these are run results

MIT License.

---

# sqf-llm-fix-eval

Бенчмарк LLM-моделей на исправление SQF-багов (Arma 3). Агент видит только три инструмента: `get_task`, `submit_answer`, `get_results`. Ловушки, проверки и таблица живут у сервера — агент их не видит.

## установка

1. `pip install -r requirements.txt` (python 3.10+, mcp 1.x).
2. Держи папку бенчмарка ВНЕ рабочей папки проекта (например `C:/tools/sqf-llm-fix-eval`), иначе агент прочитает анализатор и подгонит ответ.
3. Подключи к агенту:
   - claude code: `claude mcp add sqf-llm-fix-eval -- python C:/tools/sqf-llm-fix-eval/mcp_server.py`
   - другие клиенты (json): `{"mcpServers": {"sqf-llm-fix-eval": {"command": "python", "args": ["C:/tools/sqf-llm-fix-eval/mcp_server.py"]}}}`
4. Скопируй `SKILL.md` в скиллы агента.
5. В чате напиши: «проверь модель на работу с арма3».

## что делает

- **get_task** — выдаёт одноразовый талон (ticket) и задачу с исходным sqf.
- **submit_answer** — принимает талон, имя модели и исправленный файл; пишет ответ в `variants/модель__N.sqf`, перестраивает таблицу.
- **get_results** — сводка по моделям и путь к `results.xlsx`.

## ловушки (analyze.py)

1. `_instigator` используется не там, где нужно
2. сравнение `_victim` с другими объектами
3. тимкилл по `side` + `group`
4. `remoteExec ["hint"...]` с не-локальным таргетом
5. `setVariable` без 3-го аргумента `true`

Оценка = сумма т1..т5 (0 = идеально, 5 = все баги). Это эвристика по тексту, не игровой тест.

## защита

Талон одноразовый, оценка агенту не возвращается. Не защищает от чтения файлов сервера с диска (поэтому шаг 2) и от запуска всех прогонов в одном контексте.

## файлы

- `mcp_server.py` — сервер (три инструмента)
- `analyze.py` — разбирает `variants/` в `results.xlsx`
- `tasks/2-1-killreward/` — задача, исходник с багами, игровой тест
- `suspicious.json` — шаблоны подозрительных конструкций
- `variants/`, `results.xlsx`, `backup/` — игнорируются, это результаты прогонов

Лицензия MIT.
