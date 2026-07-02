"""NER F1 evaluation harness for the M11 Integration.

Methodology (NER F1 -- token-level entity exact-match):

Filter the predictions to the document_ids present in the gold fixture
(`data/ner_conll30.json`); discard predictions for any other document_id. An
entity is a true positive (TP) iff a gold entity with the same `entity_text`
AND the same `entity_label` exists in the same `document_id` (string-equality
on `entity_text`; string-equality on `entity_label`; whitespace is not
normalized -- the M6 NER pipeline already returns trimmed entity text). An
entity in predictions with no matching gold entity is a false positive (FP).
A gold entity with no matching prediction is a false negative (FN). Compute
precision = TP / (TP + FP), recall = TP / (TP + FN), F1 = 2*P*R / (P + R).
Aggregate micro-averaged across documents -- sum TPs / FPs / FNs across all 30
documents, then compute. Threshold floor: F1 >= 0.65. NaN handling: if
TP + FP = 0, precision is 0; if TP + FN = 0, recall is 0; if both are 0, F1
is 0 (not NaN -- the report writes `0.0`, not `nan`).

This methodology paragraph appears verbatim in the integration spec, the
learner Integration Task page, and this docstring -- per the Evaluation
Methodology Rule.
"""

import json
import os
from typing import Tuple

import httpx

from lib.ner_scorer import compute_micro_f1, score_document


API_URL = os.environ.get("API_URL", "http://localhost:8000")
FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "data", "ner_conll30.json")


def load_fixture():
    """Return the gold fixture as a list of {document_id, text, gold_entities}."""
    with open(FIXTURE_PATH) as fh:
        return json.load(fh)


def run() -> Tuple[float, float, float, list]:
    """Run the harness end-to-end. Returns (precision, recall, f1, per_doc_results)."""
    # 1. Load the gold fixture.
    gold_data = load_fixture()
    
    predictions_by_doc = {}
    gold_by_doc = {}
    per_doc_results = []
    
    for doc in gold_data:
        doc_id = doc["document_id"]
        text = doc["text"]
        gold_entities = doc["gold_entities"]
        
        # 2. POST /extract المباشر لتسهيل الـ monkeypatch الخاص بـ pytest
        url = f"{API_URL.rstrip('/')}/extract"
        response = httpx.post(url, json={"text": text})
        response.raise_for_status()
        
        pred_entities = response.json()
        if isinstance(pred_entities, dict) and "entities" in pred_entities:
            pred_entities = pred_entities["entities"]

        # 3. Build per-document prediction and gold mappings keyed by document_id.
        predictions_by_doc[doc_id] = pred_entities
        gold_by_doc[doc_id] = gold_entities
        
        tp, fp, fn = score_document(pred_entities, gold_entities)
        
        per_doc_results.append({
            "document_id": doc_id,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "predicted_count": len(pred_entities),
            "gold_count": len(gold_entities)
        })
            
    # 4. Compute micro-averaged F1 across all documents.
    precision, recall, f1 = compute_micro_f1(predictions_by_doc, gold_by_doc)
    
    return precision, recall, f1, per_doc_results