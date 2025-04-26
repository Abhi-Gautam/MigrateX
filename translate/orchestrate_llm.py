# orchestrate_llm.py
import os
import openai                                            # OpenAI Python SDK :contentReference[oaicite:14]{index=14}

openai.api_key = os.getenv("OPENAI_API_KEY")

def call_model(prompt, model="gpt-4", temp=0):
    res = openai.ChatCompletion.create(
        model=model,
        messages=[{"role":"system","content":"You are a code translator."},
                  {"role":"user","content":prompt}],
        temperature=temp
    )
    return res.choices[0].message.content

if __name__=="__main__":
    import sys
    prompt = open(sys.argv[1]).read()
    # simple confidence-based model selection
    for m in ["gpt-3.5-turbo","gpt-4"]:
        out = call_model(prompt, model=m)
        print(f"=== {m} ===\n{out}\n")
        break
