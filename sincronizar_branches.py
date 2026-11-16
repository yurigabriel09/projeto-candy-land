import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BRANCH = "fix/Correcoes-finais"
SOURCES = ("dev", "main")


def git(root, *args, check=True):
    p = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)
    if check and p.returncode:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip() or "Comando Git falhou")
    return p


def out(root, *args):
    return git(root, *args).stdout.strip()


def counts(root, ref):
    parts = out(root, "rev-list", "--left-right", "--count", f"HEAD...{ref}").split()
    if len(parts) != 2:
        raise RuntimeError(f"Nao foi possivel comparar HEAD com {ref}")
    return int(parts[0]), int(parts[1])


def abort_merge(root):
    check = git(root, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False)
    if check.returncode == 0:
        git(root, "merge", "--abort", check=False)


def merge_source(root, ref, execute):
    local_only, remote_only = counts(root, ref)
    print(f"{ref}: {local_only} commit(s) exclusivos locais; {remote_only} exclusivos remotos.")
    if remote_only == 0:
        print("  Ja esta integrado.")
        return True
    if not execute:
        print("  DRY-RUN: seria integrado.")
        return True

    p = git(root, "merge", "--no-ff", "--no-edit", "--no-stat", ref, check=False)
    if p.returncode == 0:
        print(f"  Merge concluido: {ref}")
        return True

    conflicts = git(root, "diff", "--name-only", "--diff-filter=U", check=False).stdout.splitlines()
    abort_merge(root)
    print(f"  Merge de {ref} falhou e foi abortado.")
    if conflicts:
        print("  Arquivos com conflito:")
        for item in conflicts:
            print(f"    - {item}")
    else:
        print(p.stderr.strip() or p.stdout.strip())
    return False


def main():
    parser = argparse.ArgumentParser(description="Sincroniza fix/Correcoes-finais com dev e main.")
    parser.add_argument("repo", type=Path)
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--execute", action="store_true", help="Executa os merges; sem isso apenas simula.")
    args = parser.parse_args()

    root = args.repo.expanduser().resolve()
    top = Path(out(root, "rev-parse", "--show-toplevel")).resolve()
    if top != root:
        raise RuntimeError("Informe a raiz do repositorio CandyLand.")
    branch = out(root, "branch", "--show-current")
    if branch != BRANCH:
        raise RuntimeError(f"Branch atual: {branch}. Esperada: {BRANCH}.")

    status = out(root, "status", "--porcelain", "--untracked-files=all")
    if args.execute and status:
        raise RuntimeError("Working tree nao esta limpa. Faca commit/stash antes:\n" + status)

    print(f"Repositorio: {root}")
    print(f"Branch de destino: {BRANCH}")
    print(f"Buscando todas as branches do remote {args.remote}...")
    git(root, "fetch", "--all", "--prune")

    refs = [f"{args.remote}/{name}" for name in SOURCES]
    for ref in refs:
        if git(root, "rev-parse", "--verify", ref, check=False).returncode:
            raise RuntimeError(f"Ref remota nao encontrada: {ref}")

    if not args.execute:
        print("\nDRY-RUN: nenhuma branch ou arquivo local sera alterado.")
        for ref in refs:
            merge_source(root, ref, False)
        print("\nPara executar: adicione --execute.")
        return 0

    backup = "backup/fix-Correcoes-finais-pre-sync-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    git(root, "branch", backup, "HEAD")
    print(f"Backup local criado: {backup}")

    if not merge_source(root, refs[0], True):
        print("Sincronizacao interrompida em dev. Nenhum merge conflitante ficou aberto.")
        return 2

    if not merge_source(root, refs[1], True):
        print("Dev ficou integrado. Main nao foi integrada; seu merge foi abortado.")
        return 3

    print("\nSincronizacao local concluida.")
    print("Revise com:")
    print("  git status")
    print("  git log --oneline --graph --decorate -20")
    print(f"Depois envie com: git push {args.remote} {BRANCH}")
    print("Nenhum force-push foi utilizado.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        sys.exit(1)
