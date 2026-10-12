"""
Gynecology Specialist RAG Agent & Knowledge Base
Provides deep domain-specific knowledge ingestion, query expansion, and evidence retrieval
from Williams Gynecology (Study Guide & Reference).
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..vector_index import MedicalKnowledgeIndex
from .internal_medicine_rag import EvidenceBrief

logger = logging.getLogger("GynecologyRAG")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GYN_COLLECTION_PATH = REPO_ROOT / "data" / "knowledge" / "gynecology_collection.json"
GYN_EMBEDDINGS_PATH = REPO_ROOT / "data" / "knowledge" / "gynecology_embeddings.npy"

GYNECOLOGY_SYNONYM_MAP: Dict[str, List[str]] = {
    "abnormal uterine bleeding": ["aub", "palm-coein", "menorrhagia", "metrorrhagia", "endometrial biopsy", "transvaginal ultrasound", "tranexamic acid"],
    "aub": ["abnormal uterine bleeding", "palm-coein classification", "endometrial hyperplasia", "pipelle biopsy", "transvaginal sonography"],
    "ectopic pregnancy": ["pregnancy of unknown location", "beta-hcg discriminatory zone", "methotrexate", "salpingostomy", "salpingectomy", "transvaginal ultrasound adnexal mass"],
    "pelvic inflammatory disease": ["pid", "tubo-ovarian abscess", "fitz-hugh-curtis syndrome", "ceftriaxone", "doxycycline", "metronidazole", "cervical motion tenderness"],
    "pid": ["pelvic inflammatory disease", "endometritis", "salpingitis", "tubo-ovarian abscess", "chlamydia trachomatis", "neisseria gonorrhoeae"],
    "endometriosis": ["dysmenorrhea", "dyspareunia", "pelvic pain", "endometrioma", "chocolate cyst", "gnrh agonist", "laparoscopic excision", "dienogest"],
    "adnexal mass": ["ovarian cyst", "ovarian torsion", "dermoid cyst", "mature cystic teratoma", "doppler ultrasound", "ca-125", "pelvic mass"],
    "ovarian torsion": ["acute pelvic pain", "ovarian ischemia", "whirlpool sign", "emergent laparoscopy", "detorsion", "adnexal torsion"],
    "fibroids": ["uterine leiomyoma", "submucosal fibroid", "intramural leiomyoma", "myomectomy", "uterine artery embolization", "hysterectomy"],
    "pcos": ["polycystic ovary syndrome", "rotterdam criteria", "hyperandrogenism", "oligomenorrhea", "insulin resistance", "metformin", "letrozole"],
    "cervical dysplasia": ["pap smear", "cervical cytology", "human papillomavirus", "hpv", "asccp guidelines", "colposcopy", "leep", "cin"],
    "menopause": ["vasomotor symptoms", "hot flashes", "hormone therapy", "estrogen progestin", "genitourinary syndrome of menopause", "gsm", "vaginal atrophy"],
}


class GynecologyRAGAgent:
    """
    Dedicated Gynecology knowledge retrieval agent indexing Williams Gynecology.
    """

    def __init__(self, collection_path: Optional[Path] = None, embeddings_path: Optional[Path] = None):
        self.collection_path = collection_path or GYN_COLLECTION_PATH
        self.embeddings_path = embeddings_path or GYN_EMBEDDINGS_PATH
        self.chunks = self._load_collection()
        emb_p = self.embeddings_path if self.embeddings_path.exists() else None
        self.index = MedicalKnowledgeIndex(self.chunks, embeddings_path=emb_p)
        logger.info(
            f"Gynecology RAG Agent initialized with {len(self.chunks)} chunks "
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
                logger.error(f"Error loading Gynecology collection from {self.collection_path}: {e}")
        return []

    def expand_query(self, query: str) -> str:
        """Enriches the query with high-yield clinical synonyms from Williams Gynecology."""
        query_lower = query.lower()
        expanded_terms = []
        for key, terms in GYNECOLOGY_SYNONYM_MAP.items():
            if key in query_lower:
                expanded_terms.extend(terms[:4])
        if expanded_terms:
            return f"{query} {' '.join(expanded_terms)}"
        return query

    def retrieve_evidence(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieves top-k evidence passages from Williams Gynecology using dense vector cosine similarity."""
        if not self.chunks:
            return []

        expanded = self.expand_query(query)
        results = self.index.search(expanded, top_k=top_k)

        formatted_results = []
        for r in results:
            chapter = r.get("chapter") or "Williams Gynecology"
            page = r.get("page_number")
            text = r.get("text", "")
            score = r.get("score", 0.0)

            formatted_results.append({
                "book": "Williams Gynecology",
                "chapter": chapter,
                "page": page,
                "score": round(score, 3),
                "text": text,
                "source": f"Williams Gynecology, {chapter}" + (f", Page {page}" if page else ""),
            })

        return formatted_results

    def generate_evidence_brief(
        self,
        chief_complaint: str,
        hpi: str = "",
        abnormal_labs: Optional[List[str]] = None,
    ) -> EvidenceBrief:
        """Synthesizes a structured EvidenceBrief for formal gynecology consultation."""
        query_parts = [chief_complaint]
        if hpi:
            query_parts.append(hpi)
        if abnormal_labs:
            query_parts.append(" ".join(abnormal_labs))

        full_query = " ".join(query_parts)
        retrieved = self.retrieve_evidence(full_query, top_k=5)

        domain = self._classify_gynecology_domain(full_query)

        c_lower = full_query.lower()
        if "ectopic" in c_lower or "pregnancy" in c_lower or "hcg" in c_lower:
            clinical_summary = "Evaluate for ectopic pregnancy using serial quantitative beta-hCG and transvaginal ultrasound; assess candidacy for medical methotrexate vs urgent surgical laparoscopy."
            workup = [
                "Quantitative serum beta-hCG with repeat at 48 hours to evaluate doubling time",
                "Transvaginal ultrasound (TVUS) to assess for adnexal mass, gestational sac, and free fluid",
                "Type and Rh antibody screen (administer RhoGAM if patient is Rh-negative)",
                "Complete blood count, baseline hepatic and renal function panels prior to methotrexate",
            ]
            therapy = [
                "Single-dose intramuscular methotrexate (50 mg/m2) if mass < 3.5 cm, no cardiac activity, and beta-hCG < 5000 mIU/mL",
                "Emergent diagnostic and therapeutic laparoscopy (salpingostomy or salpingectomy) for hemodynamic instability, ruptured ectopic, or failed medical therapy",
            ]
            contraindications = [
                "Do NOT administer methotrexate in renal/hepatic insufficiency, active peptic ulcer, or immunodeficiency",
                "Do NOT delay surgical exploration in hemodynamically unstable patients or suspected hemoperitoneum",
            ]
        elif "bleeding" in c_lower or "aub" in c_lower or "menorrhagia" in c_lower or "palm-coein" in c_lower:
            clinical_summary = "Classify abnormal uterine bleeding using FIGO PALM-COEIN criteria; rule out pregnancy and endometrial malignancy before initiating targeted medical or surgical intervention."
            workup = [
                "Urine pregnancy test / quantitative serum beta-hCG",
                "Complete blood count, serum ferritin, and coagulation profile (PT/INR, aPTT)",
                "Pelvic transvaginal ultrasound with Doppler to measure endometrial stripe thickness",
                "Pipelle endometrial sampling if age >= 45 or younger with obesity / chronic anovulation",
            ]
            therapy = [
                "High-dose oral progestins (medroxyprogesterone acetate 10-20 mg daily or norethindrone 5 mg TID)",
                "Combined oral contraceptives or IV conjugated equine estrogen for acute bleeding cessation",
                "Levonorgestrel-releasing intrauterine system (LNG-IUS) for long-term menorrhagia control",
                "Tranexamic acid 1300 mg PO TID during heavy menses as non-hormonal alternative",
            ]
            contraindications = [
                "Do NOT initiate hormonal therapy without excluding pregnancy",
                "Do NOT omit endometrial biopsy in postmenopausal bleeding or persistent perimenopausal AUB",
            ]
        elif "pid" in c_lower or "pelvic inflammatory" in c_lower or "tubo-ovarian" in c_lower:
            clinical_summary = "Initiate empiric broad-spectrum antimicrobial coverage for pelvic inflammatory disease immediately in patients with cervical motion tenderness to prevent tubal scarring and infertility."
            workup = [
                "Cervical / vaginal NAAT for Chlamydia trachomatis & Neisseria gonorrhoeae",
                "Saline wet mount and vaginal pH (evaluate for trichomoniasis and bacterial vaginosis)",
                "Pelvic transvaginal ultrasound to rule out tubo-ovarian abscess (TOA)",
                "Serum inflammatory markers (C-reactive protein and erythrocyte sedimentation rate)",
            ]
            therapy = [
                "Inpatient parenteral regimen: IV Ceftriaxone 1 g q24h + IV Doxycycline 100 mg q12h + IV Metronidazole 500 mg q12h",
                "Step-down to oral Doxycycline 100 mg BID + Metronidazole 500 mg BID to complete a 14-day total course",
            ]
            contraindications = [
                "Do NOT treat as outpatient if pregnant, clinical illness is severe, TOA is present, or appendicitis cannot be excluded",
            ]
        else:
            clinical_summary = "Comprehensive gynecologic assessment combining targeted bimanual examination, transvaginal sonography, and endocrine lab panels."
            workup = [
                "Urine pregnancy test / serum beta-hCG",
                "Complete blood count with differential",
                "Transvaginal and transabdominal pelvic ultrasound",
                "Targeted endocrine panel (TSH, prolactin, total testosterone) as indicated",
            ]
            therapy = [
                "Targeted medical or surgical gynecologic therapy based on ultrasound and biopsy pathology",
            ]
            contraindications = [
                "Do NOT omit pregnancy testing in any reproductive-aged female presenting with pelvic or bleeding symptoms",
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

    def _classify_gynecology_domain(self, query: str) -> str:
        q = query.lower()
        if "ectopic" in q or "pregnancy" in q or "beta-hcg" in q or "hcg" in q:
            return "Early Pregnancy Complications & Ectopic Pregnancy"
        if "bleeding" in q or "aub" in q or "menorrhagia" in q or "palm-coein" in q or "endometrial" in q:
            return "Abnormal Uterine Bleeding & Endometrial Pathology"
        if "pid" in q or "pelvic inflammatory" in q or "tubo-ovarian" in q or "toa" in q or "salpingitis" in q:
            return "Pelvic Inflammatory Disease & Gynecologic Infections"
        if "torsion" in q or "adnexal" in q or "ovarian cyst" in q or "dermoid" in q or "mass" in q:
            return "Adnexal Masses & Ovarian Torsion"
        if "endometriosis" in q or "dysmenorrhea" in q or "dyspareunia" in q or "pelvic pain" in q:
            return "Endometriosis & Chronic Pelvic Pain"
        if "fibroid" in q or "leiomyoma" in q or "myoma" in q:
            return "Uterine Leiomyomas (Fibroids)"
        if "pcos" in q or "polycystic" in q or "hirsutism" in q or "oligomenorrhea" in q:
            return "Polycystic Ovary Syndrome & Reproductive Endocrinology"
        if "pap" in q or "cervical" in q or "hpv" in q or "colposcopy" in q or "dysplasia" in q:
            return "Cervical Cytology & Lower Genital Tract Neoplasia"
        if "menopause" in q or "hot flash" in q or "vasomotor" in q or "hrt" in q:
            return "Menopause & Hormone Therapy"
        return "General Gynecology & Pelvic Surgery"

    def _extract_clinical_pearls(self, domain: str) -> List[str]:
        pearls = {
            "Early Pregnancy Complications & Ectopic Pregnancy": [
                "A quantitative beta-hCG exceeding the discriminatory zone (1,500-2,000 mIU/mL) without an intrauterine gestational sac on TVUS strongly suggests ectopic pregnancy.",
                "Hemodynamically stable patients with unruptured ectopic mass <3.5 cm, no embryonic cardiac activity, and baseline beta-hCG <5,000 mIU/mL are candidates for single-dose intramuscular methotrexate (50 mg/m2).",
                "Serial beta-hCG measurements must demonstrate a >15% drop between day 4 and day 7 post-methotrexate administration.",
            ],
            "Abnormal Uterine Bleeding & Endometrial Pathology": [
                "Abnormal uterine bleeding in reproductive-aged women should be systematically categorized using FIGO PALM-COEIN criteria (structural: Polyp, Adenomyosis, Leiomyoma, Malignancy; nonstructural: Coagulopathy, Ovulatory, Endometrial, Iatrogenic, Not classified).",
                "Endometrial sampling (Pipelle biopsy) is mandatory in women aged 45 and older presenting with AUB, or younger women with risk factors for endometrial carcinoma (obesity, unopposed estrogen, chronic anovulation/PCOS).",
                "Acute severe AUB without hemodynamic compromise can be managed with high-dose oral progestins, combined oral contraceptives, or intravenous conjugated equine estrogen followed by oral taper.",
            ],
            "Pelvic Inflammatory Disease & Gynecologic Infections": [
                "Empiric antimicrobial therapy for PID must be initiated promptly in sexually active young women presenting with uterine, adnexal, or cervical motion tenderness to prevent tubal scarring and infertility.",
                "Inpatient parenteral regimen consists of IV ceftriaxone 1 g q24h + IV doxycycline 100 mg q12h + IV metronidazole 500 mg q12h (or IV cefotetan/cefoxitin + doxycycline).",
                "Indications for immediate hospitalization include tubo-ovarian abscess, pregnancy, severe illness/high fever/nausea, inability to tolerate oral medications, or surgical emergency (appendicitis) not excluded.",
            ],
            "Adnexal Masses & Ovarian Torsion": [
                "Ovarian torsion is a time-critical surgical emergency; presence of Doppler blood flow does not rule out torsion due to dual ovarian blood supply.",
                "Management of ovarian torsion in reproductive-aged females favors prompt laparoscopic detorsion with cystectomy/conservation, even if the ovary appears dusky or congested.",
                "Postmenopausal adnexal masses require transvaginal ultrasound morphological assessment (size, multilocularity, solid components, papillary projections) and serum CA-125 measurement.",
            ],
            "Endometriosis & Chronic Pelvic Pain": [
                "Definitive diagnosis of endometriosis requires laparoscopic visualization and histological confirmation, though empiric first-line medical therapy (continuous oral contraceptives or progestins) is appropriate.",
                "Second-line medical options include GnRH antagonists (elagolix) or GnRH agonists with add-back hormonal therapy to prevent bone mineral density loss and hypoestrogenic symptoms.",
            ],
            "Uterine Leiomyomas (Fibroids)": [
                "Submucosal fibroids (FIGO types 0, 1, 2) cause the highest rate of menorrhagia and subfertility and are amenable to hysteroscopic resection.",
                "Uterine artery embolization (UAE) or myomectomy are uterine-preserving alternatives to hysterectomy for symptomatic intramural and subserosal leiomyomas.",
            ],
            "Polycystic Ovary Syndrome & Reproductive Endocrinology": [
                "Rotterdam criteria require at least 2 of 3 features: oligo/anovulation, clinical or biochemical hyperandrogenism, and polycystic ovarian morphology on ultrasound.",
                "Screening for metabolic syndrome, impaired glucose tolerance (2-hour OGTT), and dyslipidemia is essential in all PCOS patients regardless of BMI.",
            ],
        }
        return pearls.get(domain, [
            "Comprehensive gynecologic evaluation combines targeted bimanual pelvic examination, transvaginal sonography, and endocrine lab testing.",
            "Always rule out pregnancy with a qualitative urine or quantitative serum beta-hCG in reproductive-aged females presenting with pelvic symptoms.",
        ])
