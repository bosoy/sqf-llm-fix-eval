# runner.py: гонит промпт задачи через openrouter и складывает ответы в variants/
# запуск: python runner.py --models models.txt --runs 3
# ключ: переменная окружения OPENROUTER_API_KEY. не проверялся в песочнице (нет доступа к openrouter)
import os, re, sys, json, time, argparse, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
ap = argparse.ArgumentParser()
ap.add_argument("--task", default="tasks/2-1-killreward")
ap.add_argument("--models", default="models.txt")
ap.add_argument("--runs", type=int, default=3)
ap.add_argument("--temperature", type=float, default=0.2)
args = ap.parse_args()

task_dir = ROOT / args.task
task = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
source = (task_dir / task["source"]).read_text(encoding="utf-8")
prompt = task["prompt"] + "\n\n```sqf\n" + source + "\n```"
key = os.environ["OPENROUTER_API_KEY"]
(ROOT / "variants").mkdir(exist_ok=True)
(ROOT / "runs").mkdir(exist_ok=True)


def ask(model):
    body = json.dumps({"model": model, "temperature": args.temperature,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=body,
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.load(r)
    return d["choices"][0]["message"]["content"], d.get("usage", {})


for line in (ROOT / args.models).read_text(encoding="utf-8").splitlines():
    model = line.split("#")[0].strip()
    if not model:
        continue
    slug = re.sub(r"[^a-z0-9.\-]+", "-", model.lower().split("/")[-1])
    for n in range(1, args.runs + 1):
        out = ROOT / "variants" / f"{slug}__{n}.sqf"
        if out.exists():
            continue  # прогон уже есть, не затираем
        try:
            text, usage = ask(model)
        except Exception as e:
            print("ошибка", model, n, e)
            continue
        (ROOT / "runs" / f"{slug}__{n}.txt").write_text(text, encoding="utf-8")
        (ROOT / "runs" / f"{slug}__{n}.usage.json").write_text(json.dumps(usage), encoding="utf-8")
        m = re.search(r"```(?:sqf)?\n(.*?)```", text, re.S)
        # нет блока кода: сохраняем как есть, analyze.py пометит как фрагмент
        out.write_text(m.group(1) if m else text, encoding="utf-8")
        print("ok", model, n)
        time.sleep(1)
