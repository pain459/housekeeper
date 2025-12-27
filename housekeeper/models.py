from __future__ import annotations
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

Risk = Literal["low", "medium", "high"]
ActionRisk = Literal["safe", "disruptive"]

class ProposedAction(BaseModel):
    id: str
    title: str
    rationale: str
    risk: ActionRisk
    commands: List[List[str]] = Field(description="Commands as argv arrays, e.g. ['sudo','apt','autoremove','-y']")
    rollback: Optional[str] = None

class HousekeeperPlan(BaseModel):
    summary: str
    findings: List[str]
    overall_risk: Risk
    actions: List[ProposedAction]
    notes: List[str] = []
