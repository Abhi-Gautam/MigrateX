# generate_tests.py
import os, json
import openai
from clang import cindex                                  # for static analysis info :contentReference[oaicite:17]{index=17}

openai.api_key = os.getenv("OPENAI_API_KEY")
IR_DIR = "/data/ir"
TEST_IR = "/data/test_ir.json"
GENERATED = "/data/tests"

def infer_tests(ir_text):
    # naive: every function → one test stub
    tests = []
    for line in ir_text.splitlines():
        if line.startswith("func"):
            fname = line.split()[1]
            tests.append({"func":fname, "test":"/* TODO */"})
    return tests

def llm_fill_tests(test_stub, chunk):
    prompt = f"""# Generate Rust unit test for this function IR:
IR:
{chunk}
Stub:
{test_stub}
"""
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":prompt}]
    )
    return resp.choices[0].message.content

def main():
    os.makedirs(GENERATED, exist_ok=True)
    all_tests = []
    for fn in os.listdir(IR_DIR):
        ir = open(os.path.join(IR_DIR,fn)).read()
        stubs = infer_tests(ir)
        for s in stubs:
            code = llm_fill_tests(s["test"], ir)
            path = os.path.join(GENERATED, f"test_{s['func']}.rs")
            open(path,"w").write(code)
            all_tests.append(path)
    print("PASS:", len(all_tests), "tests generated")

if __name__=="__main__":
    main()
