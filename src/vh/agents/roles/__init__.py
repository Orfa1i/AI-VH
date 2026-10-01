"""
Specialized clinical agent roles and permission-enforced tool interfaces for AI-VH.
"""

from .base import BaseAgent, ToolPermissionError, load_permissions_for_role
from .doctor import DoctorAgent
from .icu import ICUAgent
from .nurse import NurseAgent
from .lab import LabAgent
from .radiology import RadiologyAgent
from .pharmacy import PharmacyAgent

__all__ = [
    "BaseAgent",
    "DoctorAgent",
    "ICUAgent",
    "LabAgent",
    "NurseAgent",
    "PharmacyAgent",
    "RadiologyAgent",
    "ToolPermissionError",
    "load_permissions_for_role",
]
