# generate_ir.py
import json
from clang import cindex                                # libclang Python bindings :contentReference[oaicite:4]{index=4}
import os

INDEX_FILE = "/data/repos_index.json"
IR_OUT   = "/data/ir"

def parse_to_ast(path):
    idx = cindex.Index.create()
    tu = idx.parse(path, args=["-x", "c++", "-std=c++17"])  # ensure C++ parsing :contentReference[oaicite:5]{index=5}
    return tu

def emit_mlir(tu, out_path):
    # pseudo-code: convert clang AST → MLIR  
    with open(out_path, "w") as f:
        f.write(f"// MLIR for {tu.spelling}\n")
        for c in tu.cursor.get_children():
            f.write(str(c.kind) + "\n")

def main():
    os.makedirs(IR_OUT, exist_ok=True)
    with open(INDEX_FILE) as f: index = json.load(f)
    for entry in index:
        if entry["lang"]=="cpp":
            tu = parse_to_ast(entry["file"])
            base = os.path.basename(entry["file"]).replace(".","_") + ".mlir"
            emit_mlir(tu, os.path.join(IR_OUT, base))

if __name__=="__main__":
    main()
