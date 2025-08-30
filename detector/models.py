from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class Target(BaseModel):
    namespace: str
    name: Optional[str] = None
    selector: Optional[str] = None
    factor: Optional[int] = None
    max: Optional[int] = None

class ActionCfg(BaseModel):
    type: str
    target: Target

class DetectionCfg(BaseModel):
    method: str
    consecutive: int = 1
    # method-specific fields are allowed
    z_threshold: Optional[float] = None
    threshold: Optional[float] = None
    slope_threshold: Optional[float] = None
    span_seconds: Optional[int] = None
    gt: Optional[float] = None
    for_seconds: Optional[int] = None

class MetricCfg(BaseModel):
    name: str
    promql: str
    detection: DetectionCfg
    action: ActionCfg

class RootCfg(BaseModel):
    prometheus: Dict[str, Any]
    poll_interval_seconds: int
    baseline_window_seconds: int
    cooldown_seconds: int
    dry_run: bool
    budgets: Dict[str, int] = {}
    metrics: list[MetricCfg]
    actuator: Dict[str, Any] = {}
    inhibit: list[Dict[str, Any]] = []
