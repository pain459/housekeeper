from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

import typer
import os
from rich.console import Console
from rich.panel import Panel

from .session import SessionLogger
from .shell import ShellRunner
from .policy import CommandPolicy
from .collectors.meta import collect_meta
from .collectors.apt import collect_apt
from .collectors.disk import collect_disk
from .collectors.security import collect_security
from .collectors.systemd import collect_systemd

app = typer.Typer(no_args_is_help=True)
console = Console()


def build_audit() -> dict:
    sh = ShellRunner()
    audit = {
        "meta": collect_meta(sh),
        "apt": collect_apt(sh),
        "disk": collect_disk(sh),
        "systemd": collect_systemd(sh),
        "security": collect_security(sh),
    }
    return audit


@app.command()
def audit(and_plan: bool = typer.Option(False, "--and-plan", help="Generate plan after audit (still no execution)")):
    log = SessionLogger()
    audit_data = build_audit()
    audit_path = log.write_audit(audit_data)
    console.print(Panel.fit(f"[bold]Audit saved:[/bold] {audit_path}", title="housekeeper"))

    if and_plan:
        plan_path = _plan_from_audit_path(audit_path)
        console.print(Panel.fit(f"[bold]Plan saved:[/bold] {plan_path}", title="housekeeper"))


def _latest_file(dirpath: Path) -> Optional[Path]:
    files = sorted(dirpath.glob("*.json"))
    return files[-1] if files else None


def _plan_from_audit_path(audit_path: Path) -> Path:
    """
    v1: AI planner if OPENAI_API_KEY is set; otherwise fallback placeholder.
    """
    log = SessionLogger()
    audit = json.loads(audit_path.read_text())

    use_openai = bool(os.getenv("OPENAI_API_KEY"))

    if use_openai:
        try:
            from .planner.llm_openai import generate_plan_from_audit
            plan_model = generate_plan_from_audit(audit)
            plan_dict = plan_model.model_dump()
            return log.write_plan(plan_dict)
        except Exception as e:
            console.print(f"[yellow]AI planner failed, falling back to placeholder. Reason: {e}[/yellow]")

    # Minimal non-LLM placeholder: always propose safe defaults if upgrades exist
        actions = []
        upgradable_text = audit.get("apt", {}).get("upgradable", "")
        if upgradable_text and "upgradable" in upgradable_text:
            actions.append({
                "id": "apt_simulate",
                "title": "Simulate dist-upgrade",
                "rationale": "See what would change before upgrading packages.",
                "risk": "safe",
                "commands": [["apt-get", "-s", "dist-upgrade"]],
                "rollback": None
            })
            actions.append({
                "id": "apt_upgrade",
                "title": "Apply package upgrades",
                "rationale": "Apply available package updates after review.",
                "risk": "disruptive",
                "commands": [["sudo", "apt-get", "dist-upgrade", "-y"]],
                "rollback": "If something breaks, check /var/log/apt/history.log and consider apt install <previous-version>."
            })

        plan = {
            "summary": "Housekeeper placeholder plan (AI not configured).",
            "findings": [
                "AI not configured or failed. Set OPENAI_API_KEY to enable AI planning."
            ],
            "overall_risk": "low" if not actions else "medium",
            "actions": actions,
            "notes": [
                "Nothing is executed unless you run: housekeeper apply --plan <file>"
            ],
        }
        return log.write_plan(plan)



@app.command()
def plan(audit_path: Optional[Path] = typer.Option(None, "--audit", help="Use a specific audit file")):
    log = SessionLogger()
    if audit_path is None:
        latest = _latest_file(log.base_dir / "audits")
        if not latest:
            raise typer.BadParameter("No audits found. Run: housekeeper audit")
        audit_path = latest

    plan_path = _plan_from_audit_path(audit_path)
    console.print(Panel.fit(f"[bold]Plan saved:[/bold] {plan_path}", title="housekeeper"))


@app.command()
def apply(
    plan: Path = typer.Option(..., "--plan", exists=True, readable=True),
    yes: bool = typer.Option(False, "--yes", help="Skip interactive confirmations (still policy-gated)"),
):
    policy = CommandPolicy()
    sh = ShellRunner(default_timeout_s=120)
    log = SessionLogger()
    run_id = plan.stem.replace("plan_", "")

    plan_obj = json.loads(plan.read_text())
    actions = plan_obj.get("actions", [])

    console.print(Panel.fit(f"Loaded plan: {plan}\nActions: {len(actions)}", title="housekeeper"))
    log.append_run_event(run_id, {"event": "plan_loaded", "plan_path": str(plan)})

    for action in actions:
        title = action.get("title", "Untitled")
        risk = action.get("risk", "safe")
        commands = action.get("commands", [])

        console.print("\n" + "-" * 80)
        console.print(f"[bold]{title}[/bold]  (risk: {risk})")
        console.print(action.get("rationale", ""))

        # Show commands + policy decisions
        for argv in commands:
            decision = policy.classify(argv)
            console.print(f"  $ {' '.join(argv)}")
            console.print(f"    -> policy: [bold]{decision.risk}[/bold] ({decision.reason})")

            if decision.risk == "blocked":
                log.append_run_event(run_id, {"event": "blocked", "cmd": argv, "reason": decision.reason})
                console.print("[red]Blocked by policy. Skipping.[/red]")
                continue

            # Confirm before anything beyond read-only
            needs_confirm = decision.risk in ("safe", "disruptive")
            if needs_confirm and not yes:
                ok = typer.confirm(f"Run this command now?")
                if not ok:
                    log.append_run_event(run_id, {"event": "skipped", "cmd": argv})
                    continue

            # Execute
            log.append_run_event(run_id, {"event": "exec_start", "cmd": argv})
            res = sh.run(argv, timeout_s=180)
            log.append_run_event(run_id, {
                "event": "exec_done",
                "cmd": argv,
                "rc": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
            })

            if res.returncode != 0:
                console.print(f"[red]Command failed rc={res.returncode}[/red]")
                console.print(res.stderr[-2000:])
                # stop on error for safety
                console.print("[yellow]Stopping execution due to error.[/yellow]")
                break

    console.print(Panel.fit(f"Run log: {log.base_dir / 'runs' / f'run_{run_id}.jsonl'}", title="housekeeper"))
