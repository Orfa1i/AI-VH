"""
Clinical verification, guardrails, and fault injection validation module for AI-VH.
Provides safety checks, medication interaction verification, and evaluation judges.
"""

try:
    from backend.agents.pharmacist import pharmacist_agent
except ImportError:
    pharmacist_agent = None

__all__ = ["pharmacist_agent"]
