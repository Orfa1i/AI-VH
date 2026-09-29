"""
RxNorm clinical terminology normalisation and lookup service.
Exposed strictly as a terminology service (names to RxCUI, ingredients, classes), NOT chunked text.
"""

import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

BUILTIN_FORMULARY: Dict[str, Dict[str, Any]] = {
    "1191": {
        "rxcui": "1191",
        "name": "Aspirin",
        "synonyms": ["Aspirin", "Acetylsalicylic Acid", "Bayer Aspirin", "Ecotrin", "Empirin"],
        "ingredients": ["Aspirin"],
        "drug_classes": ["Antiplatelet Agents", "Nonsteroidal Anti-inflammatory Drugs", "Cyclooxygenase Inhibitors"],
        "atc_codes": ["B01AC06", "N02BA01"],
    },
    "6809": {
        "rxcui": "6809",
        "name": "Metformin",
        "synonyms": ["Metformin", "Metformin Hydrochloride", "Glucophage", "Fortamet", "Glumetza"],
        "ingredients": ["Metformin"],
        "drug_classes": ["Biguanides", "Antihyperglycemic Agents"],
        "atc_codes": ["A10BA02"],
    },
    "29046": {
        "rxcui": "29046",
        "name": "Lisinopril",
        "synonyms": ["Lisinopril", "Prinivil", "Zestril"],
        "ingredients": ["Lisinopril"],
        "drug_classes": ["Angiotensin-Converting Enzyme Inhibitors", "Antihypertensive Agents"],
        "atc_codes": ["C09AA03"],
    },
    "5640": {
        "rxcui": "5640",
        "name": "Ibuprofen",
        "synonyms": ["Ibuprofen", "Advil", "Motrin", "Nuprin"],
        "ingredients": ["Ibuprofen"],
        "drug_classes": ["Nonsteroidal Anti-inflammatory Drugs", "Analgesics"],
        "atc_codes": ["M01AE01"],
    },
    "83367": {
        "rxcui": "83367",
        "name": "Atorvastatin",
        "synonyms": ["Atorvastatin", "Lipitor"],
        "ingredients": ["Atorvastatin"],
        "drug_classes": ["HMG-CoA Reductase Inhibitors", "Statins", "Hypolipidemic Agents"],
        "atc_codes": ["C10AA05"],
    },
    "2193": {
        "rxcui": "2193",
        "name": "Ceftriaxone",
        "synonyms": ["Ceftriaxone", "Rocephin"],
        "ingredients": ["Ceftriaxone"],
        "drug_classes": ["Cephalosporins", "Third-Generation Cephalosporins", "Antibacterial Agents"],
        "atc_codes": ["J01DD04"],
    },
    "18631": {
        "rxcui": "18631",
        "name": "Azithromycin",
        "synonyms": ["Azithromycin", "Zithromax", "Z-Pak"],
        "ingredients": ["Azithromycin"],
        "drug_classes": ["Macrolides", "Antibacterial Agents"],
        "atc_codes": ["J01FA10"],
    },
    "32968": {
        "rxcui": "32968",
        "name": "Clopidogrel",
        "synonyms": ["Clopidogrel", "Plavix"],
        "ingredients": ["Clopidogrel"],
        "drug_classes": ["Platelet Aggregation Inhibitors", "P2Y12 Inhibitors"],
        "atc_codes": ["B01AC04"],
    },
    "1114195": {
        "rxcui": "1114195",
        "name": "Ticagrelor",
        "synonyms": ["Ticagrelor", "Brilinta"],
        "ingredients": ["Ticagrelor"],
        "drug_classes": ["Platelet Aggregation Inhibitors", "P2Y12 Inhibitors"],
        "atc_codes": ["B01AC24"],
    },
    "5224": {
        "rxcui": "5224",
        "name": "Heparin",
        "synonyms": ["Heparin", "Heparin Sodium"],
        "ingredients": ["Heparin"],
        "drug_classes": ["Anticoagulants", "Antithrombotic Agents"],
        "atc_codes": ["B01AB01"],
    },
    "4917": {
        "rxcui": "4917",
        "name": "Nitroglycerin",
        "synonyms": ["Nitroglycerin", "Nitrostat", "Nitrolingual"],
        "ingredients": ["Nitroglycerin"],
        "drug_classes": ["Vasodilators", "Nitrates"],
        "atc_codes": ["C01DA02"],
    },
}

BUILTIN_INTERACTIONS: List[Dict[str, Any]] = [
    {
        "rxcui_pair": ["1191", "5640"],
        "severity": "High",
        "description": "Ibuprofen may competitively inhibit platelet COX-1 binding of aspirin, diminishing aspirin cardioprotection and compounding gastrointestinal bleeding risk.",
    },
    {
        "rxcui_pair": ["29046", "6809"],
        "severity": "Moderate",
        "description": "Lisinopril-induced acute kidney injury or hemodynamic changes may exacerbate metformin accumulation and risk of lactic acidosis.",
    },
]


class RxNormService:
    """
    Terminology service for drug name standardisation, RxCUI resolution,
    ingredient mapping, drug class categorization, and interaction screening.
    """
    def __init__(self, fixture_file: Optional[Path] = None):
        self.concepts: Dict[str, Dict[str, Any]] = {}
        self.name_to_cui: Dict[str, str] = {}
        self.interactions: List[Dict[str, Any]] = []

        if fixture_file and Path(fixture_file).exists():
            data = json.loads(Path(fixture_file).read_text(encoding="utf-8"))
            self.concepts = data.get("concepts", {})
            self.interactions = data.get("interactions", [])
        else:
            self.concepts = dict(BUILTIN_FORMULARY)
            self.interactions = list(BUILTIN_INTERACTIONS)

        # Build reverse lookup index
        self._build_index()

    def _build_index(self) -> None:
        self.name_to_cui = {}
        for cui, info in self.concepts.items():
            name = info.get("name", "")
            if name:
                self.name_to_cui[self.normalize_name(name)] = cui
            for syn in info.get("synonyms", []):
                self.name_to_cui[self.normalize_name(syn)] = cui
            for ing in info.get("ingredients", []):
                self.name_to_cui[self.normalize_name(ing)] = cui

    @staticmethod
    def normalize_name(name: str) -> str:
        """Strip punctuation, dosage numbers, and case differences for clean matching."""
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', name.lower())
        tokens = [t for t in cleaned.split() if not t.isdigit() and len(t) > 1]
        return " ".join(tokens).strip()

    def lookup_rxcui(self, drug_name: str) -> Optional[str]:
        """Resolve a drug name, brand name, or synonym to its canonical RxCUI."""
        norm = self.normalize_name(drug_name)
        if norm in self.name_to_cui:
            return self.name_to_cui[norm]

        # Token match
        for key, cui in self.name_to_cui.items():
            if norm and (norm in key or key in norm):
                return cui

        return None

    def get_concept(self, rxcui: str) -> Optional[Dict[str, Any]]:
        """Retrieve full structured concept for an RxCUI."""
        return self.concepts.get(str(rxcui))

    def get_ingredients(self, rxcui: str) -> List[str]:
        """Return active pharmaceutical ingredients for an RxCUI."""
        concept = self.get_concept(rxcui)
        return concept.get("ingredients", []) if concept else []

    def get_drug_classes(self, rxcui: str) -> List[str]:
        """Return established pharmacological classes for an RxCUI."""
        concept = self.get_concept(rxcui)
        return concept.get("drug_classes", []) if concept else []

    def get_synonyms(self, rxcui: str) -> List[str]:
        """Return brand names and synonyms for an RxCUI."""
        concept = self.get_concept(rxcui)
        return concept.get("synonyms", []) if concept else []

    def check_interaction_risk(self, rxcui_a: str, rxcui_b: str) -> Optional[Dict[str, Any]]:
        """Screen for clinically documented drug interactions between two RxCUIs."""
        pair_set = {str(rxcui_a), str(rxcui_b)}
        for item in self.interactions:
            item_set = set(item.get("rxcui_pair", []))
            if pair_set == item_set:
                return item
        return None
