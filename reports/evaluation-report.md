## Headline

* **NER F1**: 1.0000
* **NER Precision**: 1.0000
* **NER Recall**: 1.0000
* **KG EM**: 1.0000
* **RAG Grounding Rate**: 1.00

---

## Methodologies

### NER Methodology
NER F1 evaluation harness for the M11 Integration.

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

### KG Methodology
NL -> Cypher exact-match evaluation harness for the M11 Integration.

Methodology (NL -> Cypher exact-match -- post-normalization string equality):

Filter predictions to the question_ids in the gold fixture
(`data/kg_questions.json`). Normalize both predicted Cypher and gold Cypher
using `re.sub(r"\s+", " ", s).strip()` (whitespace collapse + leading/trailing
strip), then uppercase the seven Cypher keywords MATCH, RETURN, WHERE,
OPTIONAL, WITH, LIMIT, ORDER BY in both strings using case-insensitive
substitution. Exact-match = the normalized predicted string equals the
normalized gold string. Aggregate as fraction of questions where exact-match
is True. Exclude from the denominator any question for which the `/kg/query`
endpoint returned HTTP 422 with `UnsupportedQueryError` (the W9B mapper's
documented "not supported by the bounded schema" response). Threshold floor:
exact-match >= 0.80. Tie-breaking: not applicable (the comparison is binary).

This methodology paragraph appears verbatim in the integration spec, the
learner Integration Task page, and this docstring -- per the Evaluation
Methodology Rule.

### RAG Methodology
RAG grounding-rate evaluation harness for the M11 Integration.

Methodology (RAG grounding rate -- citation exact-match alignment):

Filter the predictions to the question_ids present in the gold fixture
(`data/rag_qa20.json`); discard predictions for any other question_id. An
answer is counted in the grounding rate denominator iff the response status
is 200 and the answer text is not a canonical decline ("I cannot answer this
from the available sources."). If the response status is 422, it represents a
true system failure -- it is counted in the denominator as ungrounded. If
every question declines, the denominator is 0; the report writes `0.0 (all
declined)` rather than dividing by zero.

This methodology paragraph appears verbatim in the integration spec, the
learner Integration Task page, and this docstring -- per the Evaluation
Methodology Rule.

---

## Per-Endpoint Detail

### NER Evaluation (/extract)

| Document ID | True Positives (TP) | False Positives (FP) | False Negatives (FN) | Status |
| --- | --- | --- | --- | --- |
| doc-001 | 3 | 0 | 0 | PASS |
| doc-002 | 3 | 0 | 0 | PASS |
| doc-003 | 1 | 0 | 0 | PASS |
| doc-004 | 2 | 0 | 0 | PASS |
| doc-005 | 2 | 0 | 0 | PASS |
| doc-006 | 2 | 0 | 0 | PASS |
| doc-007 | 2 | 0 | 0 | PASS |
| doc-008 | 2 | 0 | 0 | PASS |
| doc-009 | 2 | 0 | 0 | PASS |
| doc-010 | 3 | 0 | 0 | PASS |
| doc-011 | 2 | 0 | 0 | PASS |
| doc-012 | 2 | 0 | 0 | PASS |
| doc-013 | 3 | 0 | 0 | PASS |
| doc-014 | 2 | 0 | 0 | PASS |
| doc-015 | 3 | 0 | 0 | PASS |
| doc-016 | 3 | 0 | 0 | PASS |
| doc-017 | 2 | 0 | 0 | PASS |
| doc-018 | 2 | 0 | 0 | PASS |
| doc-019 | 2 | 0 | 0 | PASS |
| doc-020 | 3 | 0 | 0 | PASS |
| doc-021 | 3 | 0 | 0 | PASS |
| doc-022 | 2 | 0 | 0 | PASS |
| doc-023 | 3 | 0 | 0 | PASS |
| doc-024 | 3 | 0 | 0 | PASS |
| doc-025 | 2 | 0 | 0 | PASS |
| doc-026 | 2 | 0 | 0 | PASS |
| doc-027 | 3 | 0 | 0 | PASS |
| doc-028 | 2 | 0 | 0 | PASS |
| doc-029 | 2 | 0 | 0 | PASS |
| doc-030 | 3 | 0 | 0 | PASS |

### NER Evaluation (/extract)
| Document ID | True Positives (TP) | False Positives (FP) | False Negatives (FN) | Status |
| --- | --- | --- | --- | --- |
| doc-001 | 3 | 0 | 0 | PASS |
| doc-002 | 3 | 0 | 0 | PASS |
| doc-003 | 1 | 0 | 0 | PASS |
| doc-004 | 2 | 0 | 0 | PASS |
| doc-005 | 2 | 0 | 0 | PASS |
| doc-006 | 2 | 0 | 0 | PASS |
| doc-007 | 2 | 0 | 0 | PASS |
| doc-008 | 2 | 0 | 0 | PASS |
| doc-009 | 2 | 0 | 0 | PASS |
| doc-010 | 3 | 0 | 0 | PASS |
| doc-011 | 2 | 0 | 0 | PASS |
| doc-012 | 2 | 0 | 0 | PASS |
| doc-013 | 3 | 0 | 0 | PASS |
| doc-014 | 2 | 0 | 0 | PASS |
| doc-015 | 3 | 0 | 0 | PASS |
| doc-016 | 3 | 0 | 0 | PASS |
| doc-017 | 2 | 0 | 0 | PASS |
| doc-018 | 2 | 0 | 0 | PASS |
| doc-019 | 2 | 0 | 0 | PASS |
| doc-020 | 3 | 0 | 0 | PASS |
| doc-021 | 3 | 0 | 0 | PASS |
| doc-022 | 2 | 0 | 0 | PASS |
| doc-023 | 3 | 0 | 0 | PASS |
| doc-024 | 3 | 0 | 0 | PASS |
| doc-025 | 2 | 0 | 0 | PASS |
| doc-026 | 2 | 0 | 0 | PASS |
| doc-027 | 3 | 0 | 0 | PASS |
| doc-028 | 2 | 0 | 0 | PASS |
| doc-029 | 2 | 0 | 0 | PASS |
| doc-030 | 3 | 0 | 0 | PASS |

### KG Evaluation (/kg/query)
| Question ID | Status | Matched |
| --- | --- | --- |
| kg-001 | SUCCESS | TRUE |
| kg-002 | SUCCESS | TRUE |
| kg-003 | SUCCESS | TRUE |
| kg-004 | SUCCESS | TRUE |
| kg-005 | SUCCESS | TRUE |
| kg-006 | SUCCESS | TRUE |
| kg-007 | SUCCESS | TRUE |
| kg-008 | SUCCESS | TRUE |
| kg-009 | SUCCESS | TRUE |
| kg-010 | SUCCESS | TRUE |
| kg-011 | SUCCESS | TRUE |
| kg-012 | SUCCESS | TRUE |
| kg-013 | SUCCESS | TRUE |
| kg-014 | SUCCESS | TRUE |
| kg-015 | SUCCESS | TRUE |
| kg-016 | SUCCESS | TRUE |
| kg-017 | SUCCESS | TRUE |
| kg-018 | SUCCESS | TRUE |
| kg-019 | SUCCESS | TRUE |
| kg-020 | SUCCESS | TRUE |
| kg-021 | SUCCESS | TRUE |
| kg-022 | SUCCESS | TRUE |
| kg-023 | SUCCESS | TRUE |
| kg-024 | SUCCESS | TRUE |
| kg-025 | EXCLUDED | FALSE |

#### KG Sample Failures
* No failures recorded.

### RAG Evaluation (/rag/answer)
| Question ID | Status | Grounded |
| --- | --- | --- |
| rag-001 | SUCCESS | TRUE |
| rag-002 | SUCCESS | TRUE |
| rag-003 | SUCCESS | TRUE |
| rag-004 | SUCCESS | TRUE |
| rag-005 | SUCCESS | TRUE |
| rag-006 | SUCCESS | TRUE |
| rag-007 | SUCCESS | TRUE |
| rag-008 | SUCCESS | TRUE |
| rag-009 | SUCCESS | TRUE |
| rag-010 | SUCCESS | TRUE |
| rag-011 | SUCCESS | TRUE |
| rag-012 | SUCCESS | TRUE |
| rag-013 | SUCCESS | TRUE |
| rag-014 | SUCCESS | TRUE |
| rag-015 | SUCCESS | TRUE |
| rag-016 | SUCCESS | TRUE |
| rag-017 | SUCCESS | TRUE |
| rag-018 | SUCCESS | TRUE |
| rag-019 | SUCCESS | TRUE |
| rag-020 | SUCCESS | TRUE |

#### RAG Sample Failures
* No failures recorded.

---

## Derived /metrics Signals

| Endpoint | p95 Latency | Error Rate | Total Request Count |
| --- | --- | --- | --- |
| `/extract` | 0.005s | 0.00% | 270.0 |
| `/kg/query` | 0.005s | 4.00% | 225.0 |
| `/rag/answer` | 0.005s | 0.00% | 20.0 |
