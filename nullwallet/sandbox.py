"""Two-bucket wallet. 'reserve' is never at risk of the strategy. 'active' is the only part the agent may expose to the market.
Positions are long/flat in the asset; the cost model charges fee + slippage + gas on every switch."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Sandbox:
    reserve: float = 8000.0
    active: float = 2000.0          # USD value of the active bucket (cash + position)
    exposure: float = 0.0           # share of the active bucket in the asset (0 or 1)
    unit_cost: float = 0.0008       # cost fraction per full switch of the active bucket
    cost_paid: float = 0.0

    @property
    def equity(self): return self.reserve + self.active

    def set_exposure(self, e: float):
        e = min(max(float(e), 0.0), 1.0); c = abs(e - self.exposure) * self.active * self.unit_cost
        self.active -= c; self.cost_paid += c; self.exposure = e; return c

    def mark(self, ret: float):
        self.active *= 1 + self.exposure * ret

    def move(self, usd: float, to_active: bool):
        usd = min(usd, self.reserve if to_active else self.active * (1 - self.exposure))
        if to_active: self.reserve -= usd; self.active += usd
        else: self.active -= usd; self.reserve += usd
        return usd
