# retrieve_and_prompt.py
import faiss, json
from transformers import AutoTokenizer
import numpy as np

IDX_FILE  = "/data/faiss.idx"
META_FILE = "/data/meta.json"
K = 5

# load
idx = faiss.read_index(IDX_FILE)
metas = json.load(open(META_FILE))
tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")

def embed_query(q, embed_fn):
    return embed_fn(q)

def retrieve(q_emb):
    D, I = idx.search(np.array([q_emb]), K)
    return [metas[i] for i in I[0]]

def compose_prompt(chunk_metas, user_chunk):
    shots = "\n\n".join([m["chunk"] for m in chunk_metas])
    return f"""# Translate this IR chunk to Rust:
# Examples:
{shots}
# Now translate:
{user_chunk}
"""

if __name__=="__main__":
    import sys
    q_chunk = open(sys.argv[1]).read()
    # assume embed_query uses same model as chunk_and_embed
    from chunk_and_embed import get_embedding
    q_emb = embed_query(q_chunk, get_embedding)
    top = retrieve(q_emb)
    prompt = compose_prompt(top, q_chunk)
    print(prompt)
