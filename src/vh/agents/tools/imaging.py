"""
Deterministic reference imaging tools for AI-VH (STEP 51 / P9.1).

Scope honesty: no trained fracture/KOA weights and no licensed image datasets
exist in this repository, and repo rules forbid fetching patient-derived data.
These are REFERENCE implementations validated against procedural synthetic
phantoms with known ground truth (`generate_*_phantom`). Every output is
labeled `interpretation: "model-output"` and carries its reference version.
Integrating real trained weights remains explicitly future work.

Conventions: 64x64 float32 phantoms in [0, 1]; bone ~0.75, soft tissue ~0.30,
fracture lines dark (~0.15). All randomness is seed-driven (numpy default_rng).
"""

import hashlib
from typing import Any, Dict, Tuple

import numpy as np

from . import ImagingToolOutput, ToolName

SIZE = 64
BONE_BAND = (0.40, 0.60)
DARK_THRESHOLD = 0.40
MIN_FRACTURE_AREA = 8
NEGATIVE_CONFIDENCE = 0.90

FRACTURE_VERSION = "fracture-loc-ref/v1.0.0"
KOA_VERSION = "knee-oa-grade-ref/v1.0.0"

KNEE_GAP_BASE = 20
KNEE_GAP_STEP = 4
KNEE_GRADE_EDGES = (18.0, 14.0, 10.0, 6.0)


def _output_id(prefix: str, pixels: np.ndarray, version: str) -> str:
    digest = hashlib.sha256(pixels.tobytes() + version.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}-{digest}"


def generate_fracture_phantom(
    seed: int, size: int = SIZE, fracture: bool = True
) -> Dict[str, Any]:
    """Procedural long-bone phantom; optional dark transverse fracture line."""
    rng = np.random.default_rng(seed)
    pixels = 0.30 + rng.normal(0.0, 0.02, (size, size))
    band_lo, band_hi = int(size * BONE_BAND[0]), int(size * BONE_BAND[1])
    pixels[:, band_lo:band_hi] = 0.75 + rng.normal(0.0, 0.01, (size, band_hi - band_lo))
    ground_truth: Dict[str, Any] = {"present": False, "bbox": None}
    if fracture:
        y_center = int(rng.integers(int(size * 0.30), int(size * 0.70)))
        slope = float(rng.uniform(-0.15, 0.15))
        for x in range(band_lo, band_hi):
            y = int(round(y_center + slope * (x - (band_lo + band_hi) / 2)))
            for dy in (-1, 0, 1):
                yy = min(max(y + dy, 0), size - 1)
                pixels[yy, x] = 0.15
        ground_truth = {
            "present": True,
            "bbox": [band_lo, y_center - 2, band_hi - 1, y_center + 2],
        }
    pixels = np.clip(pixels, 0.0, 1.0).astype(np.float32)
    return {
        "pixels": pixels,
        "ground_truth": ground_truth,
        "modality": "synthetic-xray-phantom",
        "seed": seed,
    }


def _measure_fracture_bbox(pixels: np.ndarray) -> Tuple[bool, Dict[str, int], int]:
    """Independent measurement: dark-pixel bounding box inside the bone band."""
    size = pixels.shape[0]
    band_lo, band_hi = int(size * BONE_BAND[0]), int(size * BONE_BAND[1])
    band = np.asarray(pixels, dtype=float)[:, band_lo:band_hi]
    rows, cols = np.nonzero(band < DARK_THRESHOLD)
    if rows.size < MIN_FRACTURE_AREA:
        return False, {}, int(rows.size)
    return (
        True,
        {
            "xmin": int(band_lo + cols.min()),
            "ymin": int(rows.min()),
            "xmax": int(band_lo + cols.max()),
            "ymax": int(rows.max()),
        },
        int(rows.size),
    )


class FractureLocalizationTool:
    """Reference fracture localizer. Deterministic; no learned weights."""

    tool_name: ToolName = "fracture-localization"
    model_version = FRACTURE_VERSION

    def analyze(self, pixels: np.ndarray) -> ImagingToolOutput:
        arr = np.asarray(pixels, dtype=float)
        present, bbox, mass = _measure_fracture_bbox(arr)
        confidence = round(min(0.99, 0.60 + mass / 400.0), 3) if present else NEGATIVE_CONFIDENCE
        return ImagingToolOutput(
            output_id=_output_id("IMG-FX", np.asarray(pixels), self.model_version),
            tool=self.tool_name,
            model_version=self.model_version,
            finding="fracture_detected" if present else "no_fracture",
            location=bbox or None,
            grade=None,
            confidence=confidence,
            interpretation="model-output",
        )


def generate_knee_phantom(seed: int, severity: int, size: int = SIZE) -> Dict[str, Any]:
    """Procedural knee phantom: joint gap narrows with severity (0-4)."""
    if severity not in (0, 1, 2, 3, 4):
        raise ValueError(f"Severity must be 0-4, got {severity!r}.")
    rng = np.random.default_rng(seed)
    pixels = 0.30 + rng.normal(0.0, 0.02, (size, size))
    femur_end = 22 + severity * 2
    tibia_start = 42 - severity * 2
    pixels[0:femur_end, :] = 0.80 + rng.normal(0.0, 0.01, (femur_end, size))
    pixels[tibia_start:size, :] = 0.80 + rng.normal(0.0, 0.01, (size - tibia_start, size))
    if severity >= 2:
        for cx in (size // 4, 3 * size // 4):
            for dy in range(3):
                for dx in range(-2, 3):
                    pixels[femur_end + dy - 1, cx + dx] = 0.85
                    pixels[tibia_start - dy, cx + dx] = 0.85
    pixels = np.clip(pixels, 0.0, 1.0).astype(np.float32)
    return {
        "pixels": pixels,
        "ground_truth": {"severity": severity, "gap_px": int(tibia_start - femur_end)},
        "modality": "synthetic-xray-phantom",
        "seed": seed,
    }


def _measure_joint_gap(pixels: np.ndarray) -> float:
    """Independent measurement: median vertical bone-to-bone gap, central third."""
    arr = np.asarray(pixels, dtype=float)
    size = arr.shape[0]
    columns = range(size // 3, 2 * size // 3)
    gaps = []
    for x in columns:
        column = arr[:, x]
        femur_rows = np.nonzero(column[: size // 2] > 0.60)[0]
        tibia_rows = np.nonzero(column[size // 2 :] > 0.60)[0]
        if femur_rows.size == 0 or tibia_rows.size == 0:
            continue
        gaps.append(float((size // 2 + tibia_rows.min()) - femur_rows.max()))
    if not gaps:
        return 0.0
    return float(np.median(gaps))


class KneeOAGradingTool:
    """Reference KOA grader from measured joint space. Deterministic."""

    tool_name: ToolName = "knee-oa-grading"
    model_version = KOA_VERSION

    def analyze(self, pixels: np.ndarray) -> ImagingToolOutput:
        gap = _measure_joint_gap(np.asarray(pixels, dtype=float))
        edges = KNEE_GRADE_EDGES
        if gap >= edges[0]:
            grade = 0
        elif gap >= edges[1]:
            grade = 1
        elif gap >= edges[2]:
            grade = 2
        elif gap >= edges[3]:
            grade = 3
        else:
            grade = 4
        boundary = min(abs(gap - edge) for edge in (*edges, 0.0))
        confidence = round(min(0.99, 0.70 + boundary / 4.0), 3)
        return ImagingToolOutput(
            output_id=_output_id("IMG-KOA", np.asarray(pixels), self.model_version),
            tool=self.tool_name,
            model_version=self.model_version,
            finding="oa_graded",
            location=None,
            grade=grade,
            confidence=confidence,
            interpretation="model-output",
        )
