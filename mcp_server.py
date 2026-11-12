# mcp_server.py: mcp-сервер бенчмарка sqf-llm-fix-eval. ловушки, проверки и таблица живут тут, агент их не видит
# инструменты: get_task, submit_answer, get_results
# запуск (stdio): python mcp_server.py
# ставь папку бенчмарка вне рабочей папки проекта, иначе агент сможет прочитать analyze.py
import io, re, json, uuid, contextlib
from pathlib import Path
from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).parent
TASK_DIR = ROOT / "tasks" / "2-1-killreward"
mcp = FastMCP("sqf-llm-fix-eval")
_tickets = set()  # выданные и еще не сданные талоны: один талон на один зачетный прогон


@mcp.tool()
def get_task() -> str:
    """Начать зачетный прогон проверки модели на работу с Arma 3 (SQF).
    Возвращает талон (ticket) и задачу: промпт и исходный файл. Реши задачу как обычную рабочую,
    без поиска чек-листов и без чтения файлов бенчмарка. Затем сдай полный исправленный файл через submit_answer
    с этим талоном. Для нового прогона вызови get_task снова, лучше в чистом контексте."""
    t = json.loads((TASK_DIR / "task.json").read_text(encoding="utf-8"))
    src = (TASK_DIR / t["source"]).read_text(encoding="utf-8")
    ticket = uuid.uuid4().hex[:12]
    _tickets.add(ticket)
    return f"ticket: {ticket}\n\n{t['prompt']}\n\n```sqf\n{src}\n```"


@mcp.tool()
def submit_answer(ticket: str, model: str, answer: str) -> str:
    """Сдать ответ на зачетный прогон. ticket: талон из get_task (используется один раз).
    model: точное имя той модели, которая сейчас подключена к чату; если не знаешь наверняка, спроси пользователя,
    не угадывай. answer: полный исправленный файл SQF (блок кода или чистый текст).
    Оценка не возвращается, результат попадает в таблицу."""
    if ticket not in _tickets:
        return "ошибка: талон неизвестен или уже использован, вызови get_task"
    model = (model or "").strip()
    slug = re.sub(r"[^a-z0-9.\-]+", "-", model.lower()).strip("-")
    if not slug or len(slug) > 60:
        return "ошибка: нужно непустое имя модели до 60 символов"
    _tickets.discard(ticket)
    m = re.search(r"```(?:sqf)?\n(.*?)```", answer, re.S)
    code = m.group(1) if m else answer
    vd = ROOT / "variants"
    vd.mkdir(exist_ok=True)
    n = 1
    while (vd / f"{slug}__{n}.sqf").exists():
        n += 1
    (vd / f"{slug}__{n}.sqf").write_text(code, encoding="utf-8")
    import analyze
    with contextlib.redirect_stdout(io.StringIO()):  # stdout занят протоколом mcp
        analyze.main()
    return f"принято: {slug}, прогон {n}. результат записан в таблицу"


@mcp.tool()
def get_results() -> str:
    """Показать сводку по всем проверенным моделям (среднее, худший, лучший, лишние правки) и путь к results.xlsx."""
    import analyze
    return analyze.summary()


if __name__ == "__main__":
    mcp.run()
