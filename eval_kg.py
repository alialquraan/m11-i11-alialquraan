"""NL -> Cypher exact-match evaluation harness for the M11 Integration.

Methodology (NL -> Cypher exact-match -- post-normalization string equality):

Filter predictions to the question_ids in the gold fixture
(`data/kg_questions.json`). Normalize both predicted Cypher and gold Cypher
using `re.sub(r"\\s+", " ", s).strip()` (whitespace collapse + leading/trailing
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
"""

import json
import os
from typing import Tuple

import httpx

from lib.cypher_normalizer import normalize_cypher


API_URL = os.environ.get("API_URL", "http://localhost:8000")
FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "data", "kg_questions.json")


def load_fixture():
    """Return the gold fixture as a list of {question_id, question, gold_cypher}."""
    with open(FIXTURE_PATH) as fh:
        return json.load(fh)


def run() -> Tuple[float, list]:
    """Run the harness end-to-end. Returns (exact_match_rate, per_question_results)."""
    # 1. Load the fixture.
    questions_data = load_fixture()
    
    per_question_results = []
    matched_count = 0
    supported_count = 0
    
    for item in questions_data:
        q_id = item["question_id"]
        question = item["question"]
        gold_cypher = item["gold_cypher"]
        
        result_entry = {
            "question_id": q_id,
            "question": question,
            "status": "success",
            "matched": False,
            "excluded": False
        }
        
        try:
            # 2. الاستدعاء المباشر عبر httpx.post
            url = f"{API_URL.rstrip('/')}/kg/query"
            response = httpx.post(url, json={"question": question})
            
            # 3. If the response is 422 with UnsupportedQueryError, mark the question "excluded"
            if response.status_code == 422:
                response_json = response.json()
                error_detail = response_json.get("detail", "") or response_json.get("error", "")
                if "UnsupportedQueryError" in str(error_detail):
                    result_entry["excluded"] = True
                    result_entry["status"] = "excluded"
                    per_question_results.append(result_entry)
                    continue
            
            # 5xx. Score 0 (the harness counts it as an answered failure)
            if response.status_code >= 500:
                result_entry["status"] = "failed"
                result_entry["error"] = f"HTTP {response.status_code}: {response.text}"
                supported_count += 1
                per_question_results.append(result_entry)
                continue
            
            response.raise_for_status()
            
            # 4. Otherwise, read the returned cypher field, normalize and compare.
            pred_json = response.json()
            pred_cypher = pred_json.get("cypher", "")
            
            norm_pred = normalize_cypher(pred_cypher)
            norm_gold = normalize_cypher(gold_cypher)
            
            supported_count += 1
            if norm_pred == norm_gold:
                matched_count += 1
                result_entry["matched"] = True
            else:
                result_entry["matched"] = False
                
            per_question_results.append(result_entry)
            
        except Exception as e:
            result_entry["status"] = "failed"
            result_entry["error"] = str(e)
            supported_count += 1
            per_question_results.append(result_entry)

    # 5. Aggregate exact-match rate = matched / (total - excluded) -> matched / supported_count
    exact_match_rate = 0.0
    if supported_count > 0:
        exact_match_rate = matched_count / supported_count
        
    return exact_match_rate, per_question_results