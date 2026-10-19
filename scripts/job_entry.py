"""Entry point for running the detective suite as a Databricks job.

Databricks runs this file directly (spark_python_task). The first parameter is
the repository path in the workspace; the rest are passed unchanged to
scripts.run_detective_suite. The repository is copied to local disk first,
because imports straight from /Workspace can fail right after a git pull.
Submit it with scripts/detective_job.py rather than by hand.
"""

import os
import shutil
import sys


def main():
    if len(sys.argv) < 2:
        raise SystemExit(
            "usage: job_entry.py <repo_path> [run_detective_suite args...]"
        )
    repo, rest = sys.argv[1], sys.argv[2:]
    local = "/tmp/pci_job"
    shutil.rmtree(local, ignore_errors=True)
    shutil.copytree(repo, local, ignore=shutil.ignore_patterns(".git", "output"))
    os.chdir(local)
    sys.path.insert(0, local)
    for name in [m for m in sys.modules if m == "scripts" or m.startswith("scripts.")]:
        del sys.modules[name]
    import importlib

    module = "scripts.run_detective_suite"
    if rest[:1] == ["--module"]:
        module, rest = rest[1], rest[2:]
    mod = importlib.import_module(module)
    sys.argv = [module.rsplit(".", 1)[-1]] + rest
    print("running:", " ".join(sys.argv), flush=True)
    mod.main()


if __name__ == "__main__":
    main()
