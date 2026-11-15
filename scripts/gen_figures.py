# -*- coding: utf-8 -*-
"""把 Mermaid 代码块 / .mmd 文件渲染成 PNG（供论文插图）。

两种来源：
    1) docs/03_系统功能结构图与核心业务流程.md 中的 ```mermaid 代码块 → fig_01..fig_NN
    2) docs/figures/*.mmd 独立文件 → <文件名>.png

用法：
    python scripts/gen_figures.py
"""
import base64
import glob
import os
import re
import sys
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(BASE_DIR, "docs", "03_系统功能结构图与核心业务流程.md")
OUT_DIR = os.path.join(BASE_DIR, "docs", "figures")

PATTERN = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)
FENCE = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)


def fetch_png(graph_text):
    encoded = base64.urlsafe_b64encode(graph_text.encode("utf-8")).decode("ascii")
    url = "https://mermaid.ink/img/{0}?type=png&bgColor=FFFFFF".format(encoded)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def save(path, graph_text, label):
    try:
        data = fetch_png(graph_text.strip())
        with open(path, "wb") as fh:
            fh.write(data)
        print("{0:<16} {1} bytes  OK".format(label, len(data)))
        return True
    except Exception as exc:  # noqa: BLE001
        print("{0:<16} 失败: {1}".format(label, exc))
        return False


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    ok = fail = 0

    # ---- 1) 文档内嵌代码块 ----
    if os.path.exists(SOURCE):
        with open(SOURCE, encoding="utf-8") as fh:
            blocks = PATTERN.findall(fh.read())
        print("文档内嵌 Mermaid 图 {0} 个".format(len(blocks)))
        for index, block in enumerate(blocks, start=1):
            label = "fig_{0:02d}.png".format(index)
            if save(os.path.join(OUT_DIR, label), block, label):
                ok += 1
            else:
                fail += 1

    # ---- 2) 独立 .mmd 文件 ----
    for mmd in sorted(glob.glob(os.path.join(OUT_DIR, "*.mmd"))):
        name = os.path.splitext(os.path.basename(mmd))[0] + ".png"
        with open(mmd, encoding="utf-8") as fh:
            text = fh.read()
        match = FENCE.search(text)
        graph = match.group(1) if match else text
        if save(os.path.join(OUT_DIR, name), graph, name):
            ok += 1
        else:
            fail += 1

    print("完成：成功 {0}，失败 {1}".format(ok, fail))
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
