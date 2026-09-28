"""
Generic Module Framework state machine population simulator.
Simulates patient progression through custom Synthea JSON modules to measure clinical prevalence.
"""

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union


class ModuleSimulator:
    """
    Executes Generic Module Framework JSON state machines over a synthetic population.
    Evaluates branch probabilities, condition onset states, and demographic distributions.
    """

    def __init__(
        self,
        modules_dir: Union[Path, str],
        seed: int = 42
    ):
        self.modules_dir = Path(modules_dir)
        self.seed = seed
        self.modules: Dict[str, Dict[str, Any]] = self._load_modules()

    def _load_modules(self) -> Dict[str, Dict[str, Any]]:
        loaded: Dict[str, Dict[str, Any]] = {}
        if not self.modules_dir.exists():
            return loaded

        for mfile in sorted(self.modules_dir.glob("*.json")):
            key_name = mfile.stem
            try:
                data = json.loads(mfile.read_text(encoding="utf-8"))
                loaded[key_name] = data
            except Exception:
                pass
        return loaded

    def simulate_patient_module(
        self,
        module_data: Dict[str, Any],
        rng: random.Random
    ) -> bool:
        """
        Simulate a single patient traversing a module state machine.
        Returns True if the patient enters a ConditionOnset state.
        """
        states = module_data.get("states", {})
        if not states:
            return False

        # Find Initial state
        current_state_name: Optional[str] = None
        for sname, sdata in states.items():
            if sdata.get("type") == "Initial":
                current_state_name = sname
                break

        if not current_state_name:
            return False

        condition_occurred = False
        visited_count = 0
        max_steps = 100

        while current_state_name and visited_count < max_steps:
            visited_count += 1
            sdata = states.get(current_state_name)
            if not sdata:
                break

            stype = sdata.get("type")
            if stype == "ConditionOnset":
                condition_occurred = True
            elif stype == "Terminal":
                break

            # Transitions
            next_state: Optional[str] = None

            if "direct_transition" in sdata:
                next_state = sdata["direct_transition"]

            elif "distributed_transition" in sdata:
                dists = sdata["distributed_transition"]
                r = rng.random()
                cumulative = 0.0
                for d in dists:
                    prob = float(d.get("distribution", 0.0))
                    cumulative += prob
                    if r <= cumulative:
                        next_state = d.get("transition")
                        break
                if not next_state and dists:
                    next_state = dists[-1].get("transition")

            elif "conditional_transition" in sdata:
                # In simulation without full patient attributes, follow first branch
                transitions = sdata["conditional_transition"]
                if transitions:
                    next_state = transitions[0].get("transition")

            current_state_name = next_state

        return condition_occurred

    def simulate_population(self, population_size: int = 1000) -> Dict[str, Any]:
        """
        Simulate population across all loaded custom modules and measure condition prevalence.
        """
        counts: Dict[str, int] = {mkey: 0 for mkey in self.modules}
        rng = random.Random(self.seed)

        for _ in range(population_size):
            for mkey, mdata in self.modules.items():
                if self.simulate_patient_module(mdata, rng):
                    counts[mkey] += 1

        prevalence = {
            mkey: (counts[mkey] / population_size) for mkey in self.modules
        }

        return {
            "population_size": population_size,
            "counts": counts,
            "prevalence": prevalence
        }
