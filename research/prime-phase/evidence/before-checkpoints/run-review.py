import os
import pathlib
import subprocess
import sys

provider = sys.argv[1]
prompt_file = pathlib.Path(sys.argv[2])
base = pathlib.Path(__file__).resolve().parent
project = base.parent.parent
workspace = base / provider
workspace.mkdir(exist_ok=True)
scope = (base / "graph.primes.phase.contract.current.md").read_text(encoding="utf-8-sig")
watch = pathlib.Path(os.environ["USERPROFILE"]) / ".cargo" / "bin" / "recur-watch.exe"
notifications = subprocess.run([
    str(watch), "topic", "drain", "graph.primes.phase",
    "--id", provider, "--confirm", "-d", str(project), "--json"
], capture_output=True, encoding="utf-8", check=True)
(workspace / "received-traces.json").write_text(notifications.stdout, encoding="utf-8")
role = {
    "carbon": "Review the analytic derivation, the domains, and the relation to RH.",
    "copilot": "Review the proposed numerical tests, error accounting, and rendering failure cases."
}[provider]
prompt = (
    f"{role}\nYou are the {provider} reviewer for graph.primes.phase. "
    "Review in at most 350 words. Use the supplied information only and use no tools. Return a review with "
    "VERDICT, REASONING and TESTS headings. Do not modify files or run commands.\n\n"
    + scope + "\n\nWarp assignment metadata\n"
    + prompt_file.read_text(encoding="utf-8-sig")
)
if provider == "carbon":
    command = [
        r"C:\ProgramData\chocolatey\bin\agy.exe",
        "--model", "gemini-4-carbon", "--effort", "low", "--sandbox",
        "--disable-slash-commands", "--print-timeout", "120s", "--print", prompt
    ]
else:
    command = [
        os.path.join(os.environ["LOCALAPPDATA"],
        r"Microsoft\WinGet\Packages\GitHub.Copilot_Microsoft.Winget.Source_8wekyb3d8bbwe\copilot.exe"),
        "--trust-folder", "--silent", "--no-ask-user", "--disable-builtin-mcps",
        "--deny-tool", "shell", "--deny-tool", "write", "--prompt", prompt
    ]
try:
    result = subprocess.run(command, cwd=workspace, capture_output=True,
                            encoding="utf-8", errors="replace", timeout=210)
except subprocess.TimeoutExpired:
    print("Worker review timed out", file=sys.stderr)
    sys.exit(2)

(workspace / "stderr.txt").write_text(result.stderr, encoding="utf-8")
(workspace / "response.txt").write_text(result.stdout, encoding="utf-8")
if result.returncode:
    print(result.stderr, file=sys.stderr)
    print(result.stdout)
    sys.exit(result.returncode)

report = f"publish: graph.primes.phase.{provider}.response\n\n" + result.stdout
(workspace / "review.md").write_text(report, encoding="utf-8")
event = base / "events" / f"graph.primes.phase.{provider}.response.md"
publication = (
    f"publish: graph.primes.phase.{provider}.response\n"
    f'artifact.refs = ["research/prime-phase/{provider}/review.md"]\n\n'
    f"{provider} review returned. Coordinator acceptance is pending.\n"
)
temporary = workspace / "event.tmp"
temporary.write_text(publication, encoding="utf-8")
temporary.replace(event)
print(report)
