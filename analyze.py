# analyze.py: статический разбор вариантов sqf из variants/ и сборка results.xlsx
# запуск: python analyze.py [--task tasks/2-1-killreward]
import re, sys, json, difflib
from pathlib import Path
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

ROOT = Path(__file__).parent
TASK = ROOT / "tasks" / "2-1-killreward"
if "--task" in sys.argv:
    TASK = Path(sys.argv[sys.argv.index("--task") + 1])
OUT = ROOT / "results.xlsx"
SUSPICIOUS = json.loads((ROOT / "suspicious.json").read_text(encoding="utf-8"))


def strip_comments(text):
    return "\n".join(re.sub(r"//.*$", "", l) for l in text.splitlines())


def call_args(code, head):
    # аргументы верхнего уровня для каждого вызова вида head [ ... ]
    res = []
    for m in re.finditer(head + r"\s*\[", code, re.I):
        i, depth, cur, args = m.end(), 1, "", []
        while i < len(code):
            ch = code[i]
            if ch in "[({":
                depth += 1
            elif ch in "])}":
                depth -= 1
                if depth == 0:
                    break
            if ch == "," and depth == 1:
                args.append(cur.strip()); cur = ""
            else:
                cur += ch
            i += 1
        args.append(cur.strip())
        res.append((m.start(), args))
    return res


def trap1(code):
    # техника: _instigator используется не только в params, либо effectivecommander/driver
    inst = len(re.findall(r"_instigator", code, re.I))
    return inst >= 2 or bool(re.search(r"effectivecommander|\bdriver\b|\bgunner\b", code, re.I))


def trap2(code):
    return bool(re.search(r"(isequalto|isnotequalto|!=)\s*_victim|_victim\s*(isequalto|isnotequalto|!=)", code, re.I))


def trap3(code):
    return bool(re.search(r"\bside\s+(group\s+)?_", code, re.I))


def trap4(code):
    # возвращает (прошла, условно)
    for pos, args in call_args(code, r"remoteexec(?:call)?"):
        if args and args[0].strip().strip('"').lower() == "hint":
            target = args[1].strip() if len(args) > 1 else ""
            if target and target not in ("0", "-2", '"0"'):
                seg = code[:pos]
                seg = re.split(r"[;{}]", seg)[-1].strip()
                return True, seg.startswith("[")
    # remoteexec записан как "arg remoteexec [...]": аргумент слева стоит до вызова
    return False, False


def trap5(code):
    for _, args in call_args(code, r"setvariable"):
        if args and args[0].strip().strip('"').lower() == "pts":
            return len(args) >= 3 and args[2].strip().lower() == "true"
    return False


def extra_edits(code):
    # охранные выходы до первого addeventhandler/addmpeventhandler (дубли, типы, isserver и т.п.)
    m = re.search(r"add(mp)?eventhandler", code, re.I)
    head = code[: m.start()] if m else code
    return len(re.findall(r"exitwith", head, re.I))


def style_violations(text):
    n = 0
    for line in text.splitlines():
        m = re.search(r"//(.*)$", line)
        if not m:
            continue
        c = m.group(1)
        has_upper = bool(re.search(r"[A-ZА-ЯЁ]", c))
        no_cyr = (".sqf" not in c) and not re.search(r"[а-яё]", c, re.I) and len(re.findall(r"[a-z]", c, re.I)) >= 4
        if has_upper or no_cyr:
            n += 1
    return n


def suspicious(code):
    return "; ".join(s["note"] for s in SUSPICIOUS if re.search(s["pattern"], code, re.I))


def fragment(code):
    return int(not (re.search(r"add(mp)?eventhandler", code, re.I) and re.search(r"params\s*\[", code, re.I)))


def analyze(path):
    text = path.read_text(encoding="utf-8")
    code = strip_comments(text)
    t4, cond = trap4(code)
    return {
        "t": [int(trap1(code)), int(trap2(code)), int(trap3(code)), int(t4), int(trap5(code))],
        "cond": int(cond and t4),
        "extra": extra_edits(code),
        "susp": suspicious(code),
        "style": style_violations(text),
        "frag": fragment(code),
    }


def summary():
    # сводка по моделям, считается из листа "Прогоны" без пересчета формул
    if not OUT.exists():
        return "results.xlsx еще нет"
    rows = [r for r in load_workbook(OUT)["Прогоны"].iter_rows(min_row=2, values_only=True) if r[0]]
    agg = {}
    for r in rows:
        score = sum(int(x or 0) for x in r[3:8])
        agg.setdefault(r[0], []).append((score, score - int(r[9] or 0), int(r[11] or 0), int(r[13] or 0), int(r[14] or 0)))
    out = ["модель | прогонов | среднее | строгое | худший | лучший | лишние правки | стиль | фрагменты"]
    for m, v in agg.items():
        n = len(v)
        out.append(f"{m} | {n} | {sum(x[0] for x in v)/n:.1f} | {sum(x[1] for x in v)/n:.1f} | {min(x[0] for x in v)} | "
                   f"{max(x[0] for x in v)} | {sum(x[2] for x in v)/n:.1f} | {sum(x[3] for x in v)} | {sum(x[4] for x in v)}")
    out.append(f"файл: {OUT}")
    return "\n".join(out)


def parse_name(p):
    m = re.match(r"(.+?)__(\d+)\.sqf$", p.name)
    return (m.group(1), int(m.group(2))) if m else None


def main():
    # ручные ячейки (итог игры, заметка) переносятся из прошлой таблицы
    manual = {}
    if OUT.exists():
        old = load_workbook(OUT)["Прогоны"]
        for r in old.iter_rows(min_row=2, values_only=True):
            if r[0]:
                manual[(r[0], r[1])] = (r[15], r[16])

    rows = []
    for p in sorted((ROOT / "variants").glob("*.sqf")):
        k = parse_name(p)
        if not k:
            print("пропуск (имя не вида модель__номер.sqf):", p.name)
            continue
        rows.append((k, p.name, analyze(p)))
    rows.sort(key=lambda x: (x[0][0], x[0][1]))

    F = "Arial"
    hf = Font(name=F, bold=True, color="FFFFFF")
    hfill = PatternFill("solid", fgColor="305496")
    blue = Font(name=F, color="0000FF")
    black = Font(name=F, color="000000")
    yellow = PatternFill("solid", fgColor="FFFF00")
    thin = Side(style="thin", color="BFBFBF")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    center = Alignment(horizontal="center", vertical="top")
    wrap = Alignment(wrap_text=True, vertical="top")

    wb = Workbook()
    ws = wb.active
    ws.title = "Прогоны"
    heads = ["Модель", "Прогон", "Файл", "т1 техника", "т2 суицид", "т3 тимкилл", "т4 hint", "т5 setVariable",
             "Оценка (из 5)", "Условно (массив у hint)", "Строгая оценка", "Лишние правки",
             "Подозрительное (проверить)", "Нарушения стиля", "Фрагмент (1=да)",
             "Итог test_killreward (вручную)", "Заметка (вручную)"]
    for c, h in enumerate(heads, 1):
        x = ws.cell(row=1, column=c, value=h)
        x.font = hf; x.fill = hfill; x.border = border
        x.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
    for i, ((model, run), fname, a) in enumerate(rows, 2):
        vals = [model, run, fname] + a["t"]
        for c, v in enumerate(vals, 1):
            ws.cell(row=i, column=c, value=v)
        ws.cell(row=i, column=9, value=f"=SUM(D{i}:H{i})")
        ws.cell(row=i, column=10, value=a["cond"])
        ws.cell(row=i, column=11, value=f"=I{i}-J{i}")
        ws.cell(row=i, column=12, value=a["extra"])
        ws.cell(row=i, column=13, value=a["susp"] or None)
        ws.cell(row=i, column=14, value=a["style"])
        ws.cell(row=i, column=15, value=a["frag"])
        g, n = manual.get((model, run), (None, None))
        ws.cell(row=i, column=16, value=g)
        ws.cell(row=i, column=17, value=n)
        for c in range(1, 18):
            cell = ws.cell(row=i, column=c)
            cell.border = border
            cell.font = black if c in (9, 11) else blue
            cell.alignment = wrap if c in (3, 13, 17) else center
        ws.cell(row=i, column=16).fill = yellow
        ws.cell(row=i, column=17).fill = yellow
    for col, w in zip("ABCDEFGHIJKLMNOPQ", [24, 8, 28, 9, 9, 10, 9, 12, 10, 14, 10, 10, 34, 10, 10, 18, 40]):
        ws.column_dimensions[col].width = w
    ws.row_dimensions[1].height = 48
    ws.freeze_panes = "D2"

    ms = wb.create_sheet("Модели")
    mheads = ["Модель", "Прогонов", "Среднее", "Строгое среднее", "Худший", "Лучший",
              "Лишние правки (ср.)", "Нарушения стиля (сумма)", "Фрагментов (сумма)"]
    for c, h in enumerate(mheads, 1):
        x = ms.cell(row=1, column=c, value=h)
        x.font = hf; x.fill = hfill; x.border = border
        x.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
    models = []
    for (m, _), _, _ in rows:
        if m not in models:
            models.append(m)
    R = "Прогоны!$A$2:$A$500"
    for i, m in enumerate(models, 2):
        ms.cell(row=i, column=1, value=m)
        ms.cell(row=i, column=2, value=f"=COUNTIFS({R},A{i})")
        ms.cell(row=i, column=3, value=f"=AVERAGEIFS(Прогоны!$I$2:$I$500,{R},A{i})")
        ms.cell(row=i, column=4, value=f"=AVERAGEIFS(Прогоны!$K$2:$K$500,{R},A{i})")
        ms.cell(row=i, column=5, value=f"=_xlfn.MINIFS(Прогоны!$I$2:$I$500,{R},A{i})")
        ms.cell(row=i, column=6, value=f"=_xlfn.MAXIFS(Прогоны!$I$2:$I$500,{R},A{i})")
        ms.cell(row=i, column=7, value=f"=AVERAGEIFS(Прогоны!$L$2:$L$500,{R},A{i})")
        ms.cell(row=i, column=8, value=f"=SUMIFS(Прогоны!$N$2:$N$500,{R},A{i})")
        ms.cell(row=i, column=9, value=f"=SUMIFS(Прогоны!$O$2:$O$500,{R},A{i})")
        for c in range(1, 10):
            cell = ms.cell(row=i, column=c)
            cell.border = border
            cell.font = black
            cell.alignment = center if c > 1 else Alignment(vertical="top")
            if c in (3, 4, 7):
                cell.number_format = "0.0"
    for col, w in zip("ABCDEFGHI", [24, 10, 10, 14, 10, 10, 14, 16, 14]):
        ms.column_dimensions[col].width = w
    ms.row_dimensions[1].height = 40
    ms.freeze_panes = "B2"
    wb.save(OUT)

    print(f"{'модель':26}{'прогон':>7}{'оценка':>8}{'условно':>9}{'правки':>8}{'стиль':>7}  подозрительное")
    for (m, r), f, a in rows:
        print(f"{m:26}{r:>7}{sum(a['t']):>8}{a['cond']:>9}{a['extra']:>8}{a['style']:>7}  {a['susp']}")
    print("записано:", OUT)


if __name__ == "__main__":
    main()
