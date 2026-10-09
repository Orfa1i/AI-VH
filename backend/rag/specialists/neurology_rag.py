"""
Neurology Specialist RAG Agent & Knowledge Base
Provides deep domain-specific knowledge ingestion, query expansion, and evidence retrieval
from Adams and Victor's Principles of Neurology (8th Edition).
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..vector_index import MedicalKnowledgeIndex
from .internal_medicine_rag import EvidenceBrief

logger = logging.getLogger("NeurologyRAG")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
NEURO_COLLECTION_PATH = REPO_ROOT / "data" / "knowledge" / "neurology_collection.json"
NEURO_EMBEDDINGS_PATH = REPO_ROOT / "data" / "knowledge" / "neurology_embeddings.npy"

NEUROLOGY_SYNONYM_MAP: Dict[str, List[str]] = {
    "acute ischemic stroke": ["stroke", "cva", "tpa", "thrombectomy", "nihss", "middle cerebral artery", "mca infarct", "penumbra", "ct perfusion", "tenecteplase", "tissue plasminogen activator"],
    "stroke": ["acute ischemic stroke", "cerebrovascular accident", "thrombolytic therapy", "alteplase", "endovascular thrombectomy", "large vessel occlusion", "lvo", "diffusion weighted imaging", "dwi"],
    "intracranial hemorrhage": ["ich", "hemorrhagic stroke", "basal ganglia bleed", "intracerebral hemorrhage", "blood pressure reduction", "nicardipine", "hematoma expansion", "cta spot sign"],
    "subarachnoid hemorrhage": ["sah", "thunderclap headache", "berry aneurysm", "hunt and hess", "fisher grade", "nimodipine", "lumbar puncture xanthochromia", "cerebral vasospasm"],
    "status epilepticus": ["seizure", "tonic-clonic", "lorazepam", "levetiracetam", "keppra", "fosphenytoin", "eeg", "nonconvulsive status", "epileptiform discharges", "refractory status"],
    "seizure": ["epilepsy", "convulsion", "focal seizure", "generalized seizure", "postictal state", "eeg monitoring", "antiseizure medication", "valproate", "carbamazepine"],
    "coma": ["altered mental status", "gcs", "glasgow coma scale", "brain death", "brainstem reflexes", "herniation", "uncial herniation", "osmotic therapy", "mannitol", "hypertonic saline"],
    "guillain-barre syndrome": ["gbs", "aidp", "acute inflammatory demyelinating polyradiculoneuropathy", "albuminocytologic dissociation", "ascending paralysis", "areflexia", "ivig", "plasmapheresis"],
    "myasthenia gravis": ["myasthenic crisis", "acetylcholine receptor antibody", "achr", "musk antibody", "pyridostigmine", "ice pack test", "plasma exchange", "ivig", "thymoma"],
    "multiple sclerosis": ["ms", "demyelinating disease", "optic neuritis", "mcdonald criteria", "oligoclonal bands", "mri periventricular white matter lesions", "methylprednisolone", "ocrelizumab"],
    "bacterial meningitis": ["acute meningitis", "lumbar puncture", "csf pleocytosis", "ceftriaxone", "vancomycin", "dexamethasone", "ampicillin", "kernig sign", "brudzinski sign"],
    "parkinson disease": ["movement disorder", "resting tremor", "cogwheel rigidity", "bradykinesia", "levodopa-carbidopa", "dopamine agonist", "substantia nigra", "postural instability"],
    "dementia": ["alzheimer disease", "cognitive impairment", "frontotemporal dementia", "vascular dementia", "lewy body dementia", "moca", "donepezil", "memantine"],
    "headache": ["migraine", "triptan", "cluster headache", "tension headache", "temporal arteritis", "giant cell arteritis", "cgrp antagonist", "intracranial hypertension"],
    "spinal cord compression": ["myelopathy", "cauda equina syndrome", "epidural compression", "epidural abscess", "metastatic cord compression", "urgent mri spine", "dexamethasone"],
}


class NeurologyRAGAgent:
    """
    Dedicated Neurology knowledge retrieval agent indexing Adams and Victor's Principles of Neurology.
    """

    def __init__(self, collection_path: Optional[Path] = None, embeddings_path: Optional[Path] = None):
        self.collection_path = collection_path or NEURO_COLLECTION_PATH
        self.embeddings_path = embeddings_path or NEURO_EMBEDDINGS_PATH
        self.chunks = self._load_collection()
        emb_p = self.embeddings_path if self.embeddings_path.exists() else None
        self.index = MedicalKnowledgeIndex(self.chunks, embeddings_path=emb_p)
        logger.info(
            f"Neurology RAG Agent initialized with {len(self.chunks)} chunks "
            f"(Dense vectors: {emb_p is not None})."
        )

    def _load_collection(self) -> List[Dict[str, Any]]:
        if self.collection_path.exists():
            try:
                with open(self.collection_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except Exception as e:
                logger.error(f"Error loading Neurology collection from {self.collection_path}: {e}")
        return []

    def expand_query(self, query: str) -> str:
        """Enriches the query with high-yield clinical synonyms from Adams and Victor's Principles of Neurology."""
        query_lower = query.lower()
        expanded_terms = []
        for key, terms in NEUROLOGY_SYNONYM_MAP.items():
            if key in query_lower:
                expanded_terms.extend(terms[:4])
        if expanded_terms:
            return f"{query} {' '.join(expanded_terms)}"
        return query

    def retrieve_evidence(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieves top-k evidence passages from Adams and Victor's Principles of Neurology using dense vector cosine similarity."""
        if not self.chunks:
            return []

        expanded = self.expand_query(query)
        results = self.index.search(expanded, top_k=top_k)

        formatted_results = []
        for r in results:
            chapter = r.get("chapter") or "Adams and Victor's Principles of Neurology"
            page = r.get("page") or r.get("page_number")
            text = r.get("text", "")
            score = r.get("score", 0.0)

            formatted_results.append({
                "book": "Adams and Victor's Principles of Neurology",
                "chapter": chapter,
                "page": page,
                "score": round(score, 3),
                "text": text,
                "source": f"Adams and Victor's Principles of Neurology, {chapter}" + (f", Page {page}" if page else ""),
            })

        return formatted_results

    def generate_evidence_brief(
        self,
        chief_complaint: str,
        hpi: str = "",
        abnormal_labs: Optional[List[str]] = None,
    ) -> EvidenceBrief:
        """Synthesizes a structured EvidenceBrief for formal neurology consultation."""
        query_parts = [chief_complaint]
        if hpi:
            query_parts.append(hpi)
        if abnormal_labs:
            query_parts.append(" ".join(abnormal_labs))

        full_query = " ".join(query_parts)
        retrieved = self.retrieve_evidence(full_query, top_k=5)

        domain = self._classify_neurology_domain(full_query)

        c_lower = full_query.lower()
        if any(w in c_lower for w in ["stroke", "ischemic", "tpa", "thrombectomy", "nihss", "weakness", "hemiparesis", "facial droop"]):
            clinical_summary = "Emergency acute ischemic stroke evaluation. Immediate non-contrast head CT to exclude hemorrhage, assess eligibility for IV thrombolysis (within 4.5 hours of last known normal) and emergent CT angiography / perfusion for endovascular thrombectomy."
            workup = [
                "STAT Non-contrast Head CT to rule out intracranial hemorrhage",
                "CT Angiography (CTA) of head and neck with CT Perfusion to evaluate large vessel occlusion (LVO) and ischemic core vs penumbra",
                "Point-of-care capillary blood glucose (rule out hypoglycemia mimic)",
                "NIH Stroke Scale (NIHSS) standardized clinical assessment",
                "Continuous cardiac rhythm monitoring, 12-lead ECG, and baseline troponin",
                "Coagulation profile (PT/INR, aPTT, platelet count) prior to thrombolysis",
            ]
            therapy = [
                "IV Tenecteplase 0.25 mg/kg (max 25 mg) or IV Alteplase 0.9 mg/kg (max 90 mg) within 4.5 hours of symptom onset if no contraindications",
                "Emergent Endovascular Mechanical Thrombectomy (EVT) within 24 hours for confirmed anterior circulation large vessel occlusion (ICA, MCA-M1)",
                "Maintain blood pressure < 185/110 mmHg prior to thrombolysis, and < 180/105 mmHg for 24 hours post-infusion using IV Nicardipine or Labetalol",
                "Initiate Aspirin 160-325 mg daily 24 hours post-thrombolysis after follow-up CT confirms absence of hemorrhage",
            ]
            contraindications = [
                "ABSOLUTELY CONTRAINDICATED: IV thrombolysis if head CT reveals acute intracranial hemorrhage or extensive hypoattenuation (>1/3 MCA territory)",
                "Do NOT administer antithrombotics, heparin, or antiplatelets within 24 hours of IV thrombolysis",
                "Do NOT aggressively lower blood pressure in ischemic stroke unless BP exceeds 220/120 mmHg (or >185/110 mmHg if candidate for tPA)",
            ]
        elif any(w in c_lower for w in ["seizure", "status epilepticus", "convulsion", "postictal"]):
            clinical_summary = "Urgent evaluation and staged escalation of status epilepticus. Secure airway, abort active seizure activity within 5 minutes with IV benzodiazepines, follow immediately with non-sedating antiseizure load, and initiate continuous EEG monitoring."
            workup = [
                "Continuous video-EEG monitoring to detect non-convulsive status epilepticus",
                "Bedside blood glucose, complete metabolic panel (sodium, calcium, magnesium), venous blood gas",
                "Serum antiseizure medication levels (phenytoin, carbamazepine, valproate)",
                "Non-contrast Head CT followed by brain MRI with contrast to evaluate structural lesion",
                "Lumbar puncture if CNS infection, meningitis, or encephalitis is suspected",
            ]
            therapy = [
                "First-line emergent (0-5 min): IV Lorazepam 0.1 mg/kg (4 mg IV push over 2 min, repeat once at 5-10 min) or IM Midazolam 10 mg",
                "Second-line urgent (5-20 min): IV Levetiracetam 60 mg/kg (max 4500 mg) or IV Fosphenytoin 20 mg PE/kg over 10 min",
                "Third-line refractory (>20 min): General anesthesia with continuous IV Propofol (1-2 mg/kg bolus, 2-10 mg/kg/h) or IV Midazolam with continuous EEG titration to burst suppression",
            ]
            contraindications = [
                "Do NOT delay second-line antiseizure medication while waiting for repeated doses of benzodiazepines",
                "Do NOT paralyze patient without concurrent EEG monitoring or ongoing anesthetic infusion",
            ]
        elif any(w in c_lower for w in ["myasthenia", "weakness", "ptosis", "diplopia", "crisis"]):
            clinical_summary = "Evaluation for Myasthenia Gravis exacerbation or impending myasthenic crisis. Assess respiratory muscle strength (negative inspiratory force, forced vital capacity), avoid depolarizing and nondepolarizing neuromuscular blocking agents, and initiate plasma exchange or IVIG."
            workup = [
                "Forced Vital Capacity (FVC) and Negative Inspiratory Force (NIF) serial monitoring q4-6h",
                "Serum Acetylcholine Receptor (AChR) binding, blocking, and modulating antibodies; Anti-MuSK antibodies",
                "Chest CT with contrast to evaluate for thymoma",
                "Single-fiber electromyography (SFEMG) or repetitive nerve stimulation showing decremental response",
            ]
            therapy = [
                "Therapeutic Plasma Exchange (PLEX) 5 exchanges every other day OR IV Immunoglobulin (IVIG) 2 g/kg divided over 5 days for crisis",
                "Pyridostigmine 60 mg PO TID-QID for symptomatic maintenance (HOLD during mechanical ventilation to reduce tracheal secretions)",
                "High-dose oral Prednisone 1 mg/kg/day or IV Methylprednisolone following stabilization with PLEX/IVIG",
            ]
            contraindications = [
                "CRITICAL CONTRAINDICATION: Fluoroquinolones, Aminoglycosides, Macrolides, Beta-blockers, Magnesium sulfate, and Procainamide (provoke fatal crisis)",
                "Do NOT rely solely on pulse oximetry to assess respiratory failure; monitor FVC and NIF strictly",
            ]
        elif any(w in c_lower for w in ["coma", "unconscious", "brain death", "herniation", "gcs"]):
            clinical_summary = "Emergent coma assessment and prevention of secondary brain injury. Evaluate brainstem reflexes (pupillary, corneal, oculocephalic, oculovestibular, gag, cough), identify signs of transtentorial herniation, and initiate neuro-critical life support."
            workup = [
                "Emergent Non-contrast Head CT to evaluate midline shift, effacement of basal cisterns, or mass effect",
                "Arterial blood gas, serum electrolytes, serum osmolality, blood alcohol, and comprehensive toxicology screen",
                "Continuous intracranial pressure (ICP) monitoring if GCS <= 8 with abnormal neuroimaging",
                "Continuous EEG monitoring to rule out subclinical nonconvulsive status epilepticus",
            ]
            therapy = [
                "Endotracheal intubation for airway protection if Glasgow Coma Scale (GCS) <= 8",
                "Osmotic therapy: Hypertonic Saline 3% (250 mL bolus) or IV Mannitol 20% (1 g/kg IV over 20 min) for acute intracranial hypertension",
                "Elevate head of bed 30 degrees, ensure neutral neck alignment, and avoid compressive cervical collars",
                "Target mild hyperventilation (PaCO2 30-35 mmHg) only as temporary temporizing bridge during active herniation",
            ]
            contraindications = [
                "Do NOT perform lumbar puncture prior to neuroimaging in patients with coma, focal deficits, or papilledema (risk of fatal tonsillar herniation)",
                "Do NOT administer hypotonic IV fluids (such as 0.45% NaCl or D5W) which exacerbate cerebral edema",
            ]
        else:
            clinical_summary = "Comprehensive neurologic diagnostic consultation combining detailed neuroanatomical localization, cranial nerve examination, motor/sensory testing, and neuroimaging."
            workup = [
                "Detailed cranial nerve, motor tone/strength, sensory modality, and reflex examination",
                "Brain or Spine Magnetic Resonance Imaging (MRI) with and without gadolinium contrast",
                "Complete blood count, comprehensive metabolic panel, vitamin B12, TSH, and ESR/CRP",
                "Diagnostic lumbar puncture with opening pressure and CSF cytology, protein, glucose, and culture if indicated",
            ]
            therapy = [
                "Targeted neuropharmacological and rehabilitation regimen based on structural neuroimaging and clinical localization",
            ]
            contraindications = [
                "Do NOT overlook anatomical localization (upper vs lower motor neuron, central vs peripheral) before ordering advanced neuroimaging",
            ]

        return EvidenceBrief(
            query=full_query,
            domain=domain,
            citations=retrieved,
            clinical_summary=clinical_summary,
            recommended_workup=workup,
            recommended_therapy=therapy,
            contraindications=contraindications,
        )

    def _classify_neurology_domain(self, query: str) -> str:
        q = query.lower()
        if any(w in q for w in ["stroke", "ischemic", "tpa", "thrombectomy", "nihss", "mca"]):
            return "Acute Ischemic Stroke & Vascular Neurology"
        if any(w in q for w in ["hemorrhage", "ich", "subarachnoid", "sah", "aneurysm"]):
            return "Intracranial Hemorrhage & Neuro-Vascular Emergencies"
        if any(w in q for w in ["seizure", "status epilepticus", "epilepsy", "convulsion"]):
            return "Epilepsy, Seizures & Status Epilepticus"
        if any(w in q for w in ["coma", "unconscious", "brain death", "herniation", "gcs"]):
            return "Coma, Stupor & Neuro-Critical Care"
        if any(w in q for w in ["myasthenia", "guillain", "gbs", "neuropathy", "neuromuscular"]):
            return "Neuromuscular Disorders & Myasthenia Gravis"
        if any(w in q for w in ["multiple sclerosis", "ms", "optic neuritis", "demyelinating"]):
            return "Multiple Sclerosis & Demyelinating Diseases"
        if any(w in q for w in ["meningitis", "encephalitis", "csf", "lumbar puncture"]):
            return "Neuro-Infectious Diseases & CSF Disturbances"
        if any(w in q for w in ["parkinson", "tremor", "dystonia", "chorea"]):
            return "Movement Disorders & Parkinson Disease"
        if any(w in q for w in ["dementia", "alzheimer", "memory", "cognitive"]):
            return "Cognitive Neurology & Dementia"
        if any(w in q for w in ["headache", "migraine", "cluster"]):
            return "Headache & Craniofacial Pain Syndromes"
        if any(w in q for w in ["spine", "spinal cord", "myelopathy", "cauda equina"]):
            return "Spinal Cord Disorders & Compressive Myelopathy"
        return "General Neurology & Clinical Neurophysiology"
