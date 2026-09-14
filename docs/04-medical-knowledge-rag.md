# 4. Medical Knowledge & RAG

## Medical Books — Ingestion Pipeline

Medical books are extremely valuable, but do NOT put a 500–1000 page book directly into the model prompt. Instead:

```
Medical Book
      ↓
PDF Processing
      ↓
Text Extraction
      ↓
Cleaning
      ↓
Chunking
      ↓
Metadata
      ↓
Embeddings
      ↓
Vector Database
      ↓
RAG
      ↓
Doctor Agent
```

Each chunk should preserve metadata such as:

```json
{
  "book": "Internal Medicine Reference",
  "chapter": "Cardiology",
  "page": 347,
  "section": "Heart Failure",
  "specialty": "Internal Medicine"
}
```

This allows the agent to retrieve relevant information when needed.

## RAG Architecture

Each specialty should have its own knowledge collection:

```
Medical Knowledge
│
├── Internal Medicine
│   ├── Books
│   ├── Guidelines
│   └── References
│
├── Radiology
│   ├── Books
│   ├── Guidelines
│   └── References
│
├── Pediatrics
│   ├── Books
│   └── Guidelines
│
└── Obstetrics
    ├── Books
    └── Guidelines
```

The doctor agent retrieves only the relevant information.
