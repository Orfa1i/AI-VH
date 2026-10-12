"""
Ingestion & Vector Embedding Script for Adams and Victor's Principles of Neurology (8th Edition)
Extracts text from Adams and Victor's Principles of Neurology,
chunks into structured clinical passages, computes 384-dimensional dense vectors
with all-MiniLM-L6-v2 on NVIDIA RTX 4060 GPU with CUDA acceleration, and stores vectors into
data/knowledge/neurology_collection.json, data/knowledge/neurology_embeddings.npy,
and SQLite knowledge_chunks table in data/aivh.db under department = 'NEUROLOGY'.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.rag.specialty_book_embedder import SpecialtyBookEmbedder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("NeurologyIngestion")

PDF_PATH = PROJECT_ROOT / "Medical Books/Agent for (Neurology)/Adams_and_Victors_Principles_of_Neurology.pdf"
if not PDF_PATH.exists():
    ALT_PATH = Path(r"C:\Users\PCD\Desktop\Med-books\adams-and-victors-principles-of-neurology-8th.pdf")
    if ALT_PATH.exists():
        PDF_PATH = ALT_PATH

BOOK_TITLE = "Adams and Victor's Principles of Neurology (8th Edition)"
SPECIALTY = "Neurology"
COLLECTION_PATH = PROJECT_ROOT / "data/knowledge/neurology_collection.json"
EMBEDDINGS_PATH = PROJECT_ROOT / "data/knowledge/neurology_embeddings.npy"
CHECKPOINT_PATH = PROJECT_ROOT / "data/knowledge/neurology_checkpoint.json"

ADAMS_PAGE_MAP = [
    # Part 1: The Clinical Method of Neurology
    (13, 1, "Part 1: The Clinical Method of Neurology"),
    (15, 2, "Chapter 1: Approach to the Patient with Neurologic Disease"),
    (23, 2, "Chapter 2: Special Techniques for Neurologic Diagnosis"),
    # Part 2: Cardinal Manifestations of Neurologic Disease
    (51, 1, "Part 2: Cardinal Manifestations of Neurologic Disease"),
    (51, 2, "Chapter 3: Motor Paralysis"),
    (67, 2, "Chapter 4: Abnormalities of Movement and Posture due to Disease of the Basal Ganglia"),
    (83, 2, "Chapter 5: Incoordination and Other Disorders of Cerebellar Function"),
    (92, 2, "Chapter 6: Tremor, Myoclonus, Focal Dystonias, and Tics"),
    (112, 2, "Chapter 7: Disorders of Stance and Gait"),
    (123, 2, "Chapter 8: Pain"),
    (141, 2, "Chapter 9: Other Somatic Sensation"),
    (156, 2, "Chapter 10: Headache and Other Craniofacial Pains"),
    (180, 2, "Chapter 11: Pain in the Back, Neck, and Extremities"),
    (207, 2, "Chapter 12: Disorders of Smell and Taste"),
    (215, 2, "Chapter 13: Disturbances of Vision"),
    (234, 2, "Chapter 14: Disorders of Ocular Movement and Pupillary Function"),
    (258, 2, "Chapter 15: Deafness, Dizziness, and Disorders of Equilibrium"),
    (283, 2, "Chapter 16: Epilepsy and Other Seizure Disorders"),
    (314, 2, "Chapter 17: Coma and Related Disorders of Consciousness"),
    (334, 2, "Chapter 18: Faintness and Syncope"),
    (345, 2, "Chapter 19: Sleep and Its Abnormalities"),
    (367, 2, "Chapter 20: Delirium and Other Acute Confusional States"),
    (379, 2, "Chapter 21: Dementia and the Amnesic (Korsakoff) Syndrome"),
    (397, 2, "Chapter 22: Neurologic Disorders Caused by Lesions in Particular Parts of the Cerebrum"),
    (425, 2, "Chapter 23: Disorders of Speech and Language"),
    (445, 2, "Chapter 24: Fatigue, Asthenia, Anxiety, and Depressive Reactions"),
    (454, 2, "Chapter 25: The Limbic Lobes and the Neurology of Emotion"),
    (464, 2, "Chapter 26: Disorders of the Autonomic Nervous System, Respiration, and Swallowing"),
    (492, 2, "Chapter 27: The Hypothalamus and Neuroendocrine Disorders"),
    # Part 3: Growth and Development of the Nervous System and the Neurology of Aging
    (505, 1, "Part 3: Growth and Development of the Nervous System and the Neurology of Aging"),
    (505, 2, "Chapter 28: Normal Development and Neurologic Problems of the Newborn and Infant"),
    (531, 2, "Chapter 29: The Neurology of Aging"),
    # Part 4: Major Categories of Neurologic Disease
    (541, 1, "Part 4: Major Categories of Neurologic Disease"),
    (541, 2, "Chapter 30: Disturbances of Cerebrospinal Fluid and Its Circulation"),
    (558, 2, "Chapter 31: Intracranial Neoplasms and Paraneoplastic Disorders"),
    (604, 2, "Chapter 32: Infections of the Nervous System (Bacterial, Fungal, Spirochetal, Parasitic) and Sarcoidosis"),
    (643, 2, "Chapter 33: Viral Infections of the Nervous System, Chronic Meningitis, and Prion Diseases"),
    (672, 2, "Chapter 34: Cerebrovascular Diseases"),
    (759, 2, "Chapter 35: Craniocerebral Trauma"),
    (783, 2, "Chapter 36: Multiple Sclerosis and Allied Demyelinative Diseases"),
    (809, 2, "Chapter 37: The Inherited Metabolic Diseases of the Nervous System"),
    (862, 2, "Chapter 38: Developmental Diseases of the Nervous System"),
    (907, 2, "Chapter 39: Degenerative Diseases of the Nervous System"),
    (971, 2, "Chapter 40: The Acquired Metabolic Disorders of the Nervous System"),
    (995, 2, "Chapter 41: Diseases of the Nervous System due to Nutritional Deficiency"),
    (1016, 2, "Chapter 42: Alcohol and Alcoholism"),
    (1028, 2, "Chapter 43: Disorders of the Nervous System due to Drugs, Toxins, and Other Chemical Agents"),
    # Part 5: Diseases of Spinal Cord, Peripheral Nerve, and Muscle
    (1061, 1, "Part 5: Diseases of Spinal Cord, Peripheral Nerve, and Muscle"),
    (1061, 2, "Chapter 44: Diseases of the Spinal Cord"),
    (1104, 2, "Chapter 45: Electrophysiologic and Laboratory Aids in the Diagnosis of Neuromuscular Disease"),
    (1122, 2, "Chapter 46: Diseases of the Peripheral Nerves"),
    (1190, 2, "Chapter 47: Diseases of the Cranial Nerves"),
    (1203, 2, "Chapter 48: Principles of Clinical Myology"),
    (1214, 2, "Chapter 49: The Inflammatory Myopathies"),
    (1225, 2, "Chapter 50: The Muscular Dystrophies"),
    (1242, 2, "Chapter 51: The Metabolic and Toxic Myopathies"),
    (1256, 2, "Chapter 52: The Congenital Neuromuscular Disorders"),
    (1262, 2, "Chapter 53: Myasthenia Gravis and Related Disorders of the Neuromuscular Junction"),
    (1277, 2, "Chapter 54: The Periodic Paralyses and Hereditary, Nondystrophic Myotonias"),
    (1288, 2, "Chapter 55: Disorders of Muscle Characterized by Cramps, Spasms, Pain, and Localized Abnormalities"),
    # Part 6: Psychiatric Disorders
    (1303, 1, "Part 6: Psychiatric Disorders"),
    (1303, 2, "Chapter 56: The Neuroses and Personality Disorders"),
    (1320, 2, "Chapter 57: Reactive Depression, Endogenous Depression, and Manic-Depressive Disease"),
    (1330, 2, "Chapter 58: The Schizophrenias and Paranoid States"),
    (1345, 1, "Index"),
    (1345, 2, "Subject Index"),
]


def run_neurology_ingestion(resume: bool = True, limit_pages: int = None):
    logger.info("Initializing SpecialtyBookEmbedder for Adams and Victor's Principles of Neurology...")
    embedder = SpecialtyBookEmbedder(
        pdf_path=PDF_PATH,
        book_title=BOOK_TITLE,
        specialty=SPECIALTY,
        collection_path=COLLECTION_PATH,
        embeddings_path=EMBEDDINGS_PATH,
        checkpoint_path=CHECKPOINT_PATH,
        custom_page_map=ADAMS_PAGE_MAP,
    )
    if limit_pages is not None and limit_pages > 0:
        embedder.total_pages = min(embedder.total_pages, limit_pages)
        logger.info(f"Limiting ingestion to {embedder.total_pages} pages for test run.")

    embedder.run_ingestion(resume=resume)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest & embed Adams and Victor's Principles of Neurology")
    parser.add_argument("--fresh", action="store_true", help="Start ingestion from scratch, ignoring checkpoint")
    parser.add_argument("--limit-pages", type=int, default=None, help="Optional page limit for test run")
    args = parser.parse_args()

    run_neurology_ingestion(resume=not args.fresh, limit_pages=args.limit_pages)
