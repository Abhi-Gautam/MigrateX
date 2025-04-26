# repo_cloner.py
import os
from git import Repo                                 # GitPython clone API :contentReference[oaicite:0]{index=0}
import subprocess
import json

OUTPUT_INDEX = "/data/repos_index.json"

def clone_repo(url, dest):
    if not os.path.exists(dest):
        Repo.clone_from(url, dest)                    # clone_from usage :contentReference[oaicite:1]{index=1}

def detect_language(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext in {".c", ".cpp", ".h"}: return "cpp"
    if ext in {".java"}: return "java"
    if ext in {".cs"}: return "dotnet"
    return "unknown"

def walk_and_index(root_dirs):
    index = []
    for url in root_dirs:
        name = url.split("/")[-1].replace(".git","")
        path = f"/data/repos/{name}"
        clone_repo(url, path)
        for dirpath, _, files in os.walk(path):
            for f in files:
                lang = detect_language(f)
                if lang != "unknown":
                    index.append({"repo": name, "file": os.path.join(dirpath, f), "lang": lang})
    with open(OUTPUT_INDEX,"w") as o: json.dump(index, o, indent=2)

if __name__=="__main__":
    import sys
    walk_and_index(sys.argv[1:])                       # pass list of repo URLs
