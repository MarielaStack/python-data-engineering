import json

nb = json.load(open("modulo_01_basico/01_variables.ipynb", encoding="utf-8"))
cells = nb["cells"]
print("Celdas totales:", len(cells))
for i, c in enumerate(cells[:10]):
    t   = c["cell_type"]
    src = "".join(c["source"])[:70].replace("\n", " ")
    print(f"  [{i}] {t:8s} | {src}")
