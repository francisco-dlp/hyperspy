"""Package-local widget defaults."""

from dataclasses import dataclass, field


@dataclass
class PlotConfig:
    pick_tolerance: float = 7.5


@dataclass
class Preferences:
    Plot: PlotConfig = field(default_factory=PlotConfig)


preferences = Preferences()
