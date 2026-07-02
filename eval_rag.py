"""RAG grounding-rate evaluation harness for the M11 Integration.

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
"""

import json
import httpx

API_URL = "http://localhost:8000"


import os

def load_fixture():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "data", "rag_questions.json")
    with open(file_path, "r") as fh:
        return json.load(fh)


def run():
    fixture = load_fixture()
    per_question_results = []

    grounded_count = 0
    answered_count = 0

    for row in fixture:
        qid = row["question_id"]
        q_text = row["question"]
        k_val = row["k"]
        gold_cids = row["gold_citation_chunk_ids"]

        res_obj = {"question_id": qid, "status": "unknown", "grounded": False}

        try:
            resp = httpx.post(
                f"{API_URL}/rag/answer", json={"question": q_text, "k": k_val}
            )
            if resp.status_code == 422:
                res_obj["status"] = "error"
                answered_count += 1
                per_question_results.append(res_obj)
                continue

            if resp.status_code != 200:
                res_obj["status"] = f"http_{resp.status_code}"
                per_question_results.append(res_obj)
                continue

            body = resp.json()
            ans = body.get("answer", "")
            if ans == "I cannot answer this from the available sources.":
                res_obj["status"] = "declined"
                per_question_results.append(res_obj)
                continue

            res_obj["status"] = "success"
            answered_count += 1

            # Check grounding
            citations = body.get("citations", [])
            pred_cids = [c["chunk_id"] for c in citations if "chunk_id" in c]

            if pred_cids and all(cid in gold_cids for cid in pred_cids):
                res_obj["grounded"] = True
                grounded_count += 1

            per_question_results.append(res_obj)

        except Exception as e:
            res_obj["status"] = "exception"
            per_question_results.append(res_obj)

    grounding_rate = 0.0
    if answered_count > 0:
        grounding_rate = float(grounded_count) / answered_count

    return grounding_rate, per_question_results