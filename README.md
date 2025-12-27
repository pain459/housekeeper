# Housekeeper 🧹  
**AI-assisted system housekeeping for Linux (Pop!_OS / Ubuntu-based)**

Housekeeper is a **terminal-first, safety-oriented system assistant** that helps you keep your machine healthy by:

- Auditing system state (read-only)
- Generating an AI-based maintenance plan
- Executing approved actions under strict policy controls

The core design philosophy is:

> **AI proposes → policy verifies → user approves → system executes**

Nothing runs without your consent.

---

## Features

- ✅ Read-only system audits (safe by default)
- 🤖 AI-generated maintenance plans
- 🔐 Strong command policy & sudo allowlisting
- 🧾 Full audit and execution logs
- 🧩 Extensible “skills” model (add new housekeeping tasks easily)
- 🐧 Designed for Pop!_OS / Ubuntu-based systems

---

## Core Workflow

```text
audit  →  plan  →  apply
````

1. **Audit**
   Collects system signals (packages, disk, services, security, etc.)

2. **Plan**
   Uses AI to analyze the audit and propose actions

3. **Apply**
   Executes approved commands, gated by policy and user confirmation

---

## Installation & Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd housekeeper
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install in editable mode

```bash
pip install -e .
```

Verify installation:

```bash
housekeeper --help
```

---

## Environment Configuration (`.env`)

Housekeeper uses a `.env` file for configuration (recommended).

### Create `.env`

```bash
cp .env.example .env
```

### Example `.env`

```env
# OpenAI configuration
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
HK_OPENAI_MODEL=gpt-4o-mini
HK_OPENAI_TEMPERATURE=0
```

> ⚠️ Never commit `.env`
> Ensure `.env` is listed in `.gitignore`

---

## Usage

### Run a system audit

```bash
housekeeper audit
```

Output is saved to:

```text
~/.local/share/housekeeper/audits/
```

---

### Generate a plan

```bash
housekeeper plan
```

Creates a plan JSON file under:

```text
~/.local/share/housekeeper/plans/
```

---

### Apply a plan (with approval)

```bash
housekeeper apply --plan ~/.local/share/housekeeper/plans/plan_YYYYMMDD_HHMMSS.json
```

For each action:

* Command is shown
* Policy classification is displayed
* You must explicitly approve execution

---

## Safety Model (Very Important)

Housekeeper is **not a shell wrapper**. It enforces safety at multiple layers:

### 1. Command Policy

Defined in `housekeeper/policy.py`

* Blocks destructive commands (`rm -rf`, `dd`, `mkfs`, etc.)
* Restricts `sudo` to a small, audited allowlist
* Classifies commands as:

  * `read_only`
  * `safe`
  * `disruptive`
  * `blocked`

### 2. User Approval

* No command executes without confirmation
* Even `safe` commands require approval
* `disruptive` commands are clearly labeled

### 3. Full Logging

Every execution is recorded:

```text
~/.local/share/housekeeper/runs/
```

Logs include:

* Command
* Output
* Exit code
* Timestamp

---

## Code Structure

```text
housekeeper/
├── cli.py                 # CLI entry point (audit / plan / apply)
├── shell.py               # Safe subprocess execution
├── policy.py              # Command allow/deny logic
├── session.py             # Audit & run logging
├── models.py              # Pydantic models for AI plans
│
├── collectors/            # Read-only audit modules
│   ├── apt.py
│   ├── disk.py
│   ├── systemd.py
│   ├── security.py
│   ├── reboot.py
│   ├── pkg_health.py
│   └── maintenance.py
│
├── planner/
│   ├── llm_openai.py      # AI planner (Structured Outputs)
│   └── prompt.txt         # Planner rules & guardrails
│
└── normalize.py           # (Optional) safe command normalization
```

---

## Adding New Housekeeping Skills

A “skill” usually means **one new audit collector** and (optionally) **policy support**.

### Step 1: Add a collector

Create a new file under `housekeeper/collectors/`.

Example: `cpu_health.py`

```python
from __future__ import annotations
from typing import Dict
from ..shell import ShellRunner

def collect_cpu_health(sh: ShellRunner) -> Dict:
    out = sh.run(["uptime"])
    return {"uptime": out.stdout.strip()}
```

---

### Step 2: Wire it into the audit

In `cli.py`, add:

```python
from .collectors.cpu_health import collect_cpu_health
```

And inside `build_audit()`:

```python
"cpu_health": collect_cpu_health(sh),
```

---

### Step 3: Let AI use it

No extra work needed.
The AI planner automatically sees the new audit data and may propose actions.

(Optional) Add guidance to `planner/prompt.txt` if you want specific behavior.

---

### Step 4: Allow execution (if needed)

If the AI proposes new commands, update `policy.py`:

* Add minimal allow rules
* Prefer read-only first
* Require approval for anything disruptive

> **Rule of thumb:**
> Add policy support *after* seeing what the AI proposes.

---

## Development Tips

### Verify which code is running

```bash
python -c "import inspect, housekeeper.policy; print(inspect.getfile(housekeeper.policy))"
```

### Reinstall after code changes

```bash
pip install -e .
```

---

## What Housekeeper Is *Not*

* ❌ Not an autonomous agent
* ❌ Not a background daemon (yet)
* ❌ Not a replacement for understanding your system

It’s a **trusted assistant**, not an autopilot.

---

## Roadmap (Optional Ideas)

* Profiles (daily / weekly / deep)
* Audit diffs (what changed since last run)
* Rule-based pre-planning
* Desktop notifications
* systemd system-level service
* Plugin-based skills

---

## License

Choose one:

* MIT (recommended)
* Apache 2.0

---

## Final Note

Housekeeper is intentionally boring, predictable, and transparent.

That’s why it works.

If you maintain this mindset, you’ll end up with a system assistant you can trust long-term.