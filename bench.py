# bench.py: интерфейс для агента. агент видит только задачу и сдает ответ, оценки ему не показываются
# команды:
#   python bench.py task                          печатает промпт и исходник задачи (без ловушек и проверок)
#   python bench.py submit --model ИМЯ --file F   сохраняет вариант, обновляет results.xlsx, оценку не печатает
#   python bench.py table                         печатает сводку по моделям из results.xlsx
import re, io, sys, json, argparse, contextlib
from pathlib import Path

ROOT = Path(__file__).parent
DEFAULT_TASK = "tasks/2-1-killreward"


def cmd_task(a):
    d = ROOT / a.task
    t = json.loads((d / "task.json").read_text(encoding="utf-8"))
    src = (d / t["source"]).read_text(encoding="utf-8")
    print(t["prompt"] + "\n\n```sqf\n" + src + "\n```")


def cmd_submit(a):
    slug = re.sub(r"[^a-z0-9.\-]+", "-", a.model.lower().strip()).strip("-")
    if not slug:
        sys.exit("нужно непустое имя модели (--model)")
    text = Path(a.file).read_text(encoding="utf-8")
    m = re.search(r"```(?:sqf)?\n(.*?)```", text, re.S)
    code = m.group(1) if m else text
    vd = ROOT / "variants"
    vd.mkdir(exist_ok=True)
    n = 1
    while (vd / f"{slug}__{n}.sqf").exists():
        n += 1
    (vd / f"{slug}__{n}.sqf").write_text(code, encoding="utf-8")
    import analyze
    with contextlib.redirect_stdout(io.StringIO()):  # оценки агенту не показываем
        analyze.main()
    print(f"принято: {slug}, прогон {n}. результат в results.xlsx")


def cmd_table(a):
    import analyze
    print(analyze.summary())


ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="cmd", required=True)
t = sub.add_parser("task"); t.add_argument("--task", default=DEFAULT_TASK); t.set_defaults(f=cmd_task)
s = sub.add_parser("submit"); s.add_argument("--model", required=True); s.add_argument("--file", required=True); s.set_defaults(f=cmd_submit)
b = sub.add_parser("table"); b.set_defaults(f=cmd_table)
a = ap.parse_args()
a.f(a)
