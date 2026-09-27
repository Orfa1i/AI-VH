"""
Multi-agent clinical orchestration module for AI-VH.
Coordinates specialized agents: Triage, Attending, Pharmacist, Lab, and Reviewers.
"""

try:
    from backend.simulation.orchestrator import orchestrator
except ImportError:
    orchestrator = None

__all__ = ["orchestrator"]
