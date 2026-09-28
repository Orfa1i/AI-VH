"""
Configuration schema for reproducible Synthea patient population generation.
"""

from typing import List, Optional, Tuple
from pydantic import BaseModel, Field


class SyntheaGenerationConfig(BaseModel):
    """
    Configuration parameters for a deterministic Synthea FHIR generation run.
    Contains all parameters required to reproduce a patient population exactly.
    """
    seed: int = Field(default=42, description="Random seed for patient generation")
    clinician_seed: int = Field(default=101, description="Random seed for clinician assignment")
    reference_date: str = Field(default="2026-01-01", description="Reference simulation date (YYYY-MM-DD)")
    population: int = Field(default=1, ge=1, description="Number of synthetic patients to generate")
    state: str = Field(default="Massachusetts", description="US State for geographic demographics")
    city: Optional[str] = Field(default=None, description="Optional city within state")
    gender: Optional[str] = Field(default=None, description="Optional gender filter (M or F)")
    age_range: Optional[Tuple[int, int]] = Field(default=None, description="Optional age range (min, max)")
    modules: Optional[List[str]] = Field(default=None, description="List of Synthea sub-modules to include")
    synthea_version: str = Field(default="v3.3.0", description="Pinned official Synthea release version")
    exporter_fhir: bool = Field(default=True, description="Enable FHIR R4 transaction bundle export")

    def to_command_args(self) -> List[str]:
        """Convert configuration into standard Synthea CLI command-line arguments."""
        args: List[str] = [
            "-s", str(self.seed),
            "-cs", str(self.clinician_seed),
            "-p", str(self.population),
        ]

        if self.gender:
            args.extend(["-g", self.gender])

        if self.age_range:
            args.extend(["-a", f"{self.age_range[0]}-{self.age_range[1]}"])

        if self.modules:
            for mod in self.modules:
                args.extend(["-m", mod])

        # State is positional argument for Synthea
        args.append(self.state)

        if self.city:
            args.append(self.city)

        return args
