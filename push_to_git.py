import os
import subprocess

repo_dir = r"c:\Users\SANT\OneDrive\Escritorio\Parcial 1 sistemas complejos"
os.chdir(repo_dir)

# Remove generate_report.py if present
if os.path.exists("generate_report.py"):
    os.remove("generate_report.py")

# Run git commands via subprocess
def run_git(args):
    print(f">> git {' '.join(args)}")
    res = subprocess.run(["git"] + args, capture_output=True, text=True, cwd=repo_dir)
    if res.stdout:
        print(f"[STDOUT]:\n{res.stdout}")
    if res.stderr:
        print(f"[STDERR]:\n{res.stderr}")
    return res.returncode

run_git(["init"])
run_git(["branch", "-M", "main"])
run_git(["add", "."])
run_git(["commit", "-m", "feat: agent-based model for decentralized congestion control"])

# Remote config
run_git(["remote", "remove", "origin"])
run_git(["remote", "add", "origin", "https://github.com/Porruzz/Parcial-1-SistemasComplejos.git"])
ret = run_git(["push", "-u", "origin", "main"])

if ret == 0:
    print("\n✅ PUSH EXITOSO A GITHUB!")
else:
    print("\n⚠️ Push finalizado con código:", ret)
