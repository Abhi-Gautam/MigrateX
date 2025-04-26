# chunk_and_embed.py
import os, json
from transformers import RobertaTokenizer, RobertaModel  # CodeBERT model :contentReference[oaicite:8]{index=8}
import torch
import faiss                                             # FAISS for vector index :contentReference[oaicite:9]{index=9}
import numpy as np

IR_DIR = "/data/ir"
EMB_FILE = "/data/embeddings.npy"
META_FILE = "/data/meta.json"

tokenizer = RobertaTokenizer.from_pretrained("microsoft/codebert-base")  
model     = RobertaModel.from_pretrained("microsoft/codebert-base")

def get_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        out = model(**inputs).last_hidden_state.mean(dim=1)
    return out[0].numpy()

def chunk_ir(ir_text):
    # naive: split by "func"
    return [chunk for chunk in ir_text.split("func") if chunk.strip()]

def main():
    metas, embs = [], []
    for fn in os.listdir(IR_DIR):
        text = open(os.path.join(IR_DIR,fn)).read()
        for chunk in chunk_ir(text):
            emb = get_embedding(chunk)
            embs.append(emb)
            metas.append({"file":fn, "chunk":chunk[:30]})
    np.save(EMB_FILE, np.stack(embs))
    with open(META_FILE,"w") as f: json.dump(metas,f)

    # build FAISS index
    dim = embs[0].shape[0]
    idx = faiss.IndexFlatL2(dim)
    idx.add(np.stack(embs))
    faiss.write_index(idx, "/data/faiss.idx")

if __name__=="__main__":
    main()
