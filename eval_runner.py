"""Orchestrator -- runs the three eval harnesses, reads /metrics, writes report.

Usage:
    python eval_runner.py --output reports/evaluation-report.md
"""

import argparse
import os
import sys

import eval_ner
import eval_kg
import eval_rag
from lib import metrics_reader


def assemble_report(ner_result, kg_result, rag_result, metrics_signals) -> str:
    ner_p, ner_r, ner_f1, ner_docs = ner_result
    kg_em, kg_questions = kg_result
    rag_gr, rag_questions = rag_result

    rag_gr_str = f"{rag_gr:.2f}"
    if all(q.get("declined", False) for q in rag_questions):
        rag_gr_str = "0.0 (all declined)"

    md = "## Headline\n\n"
    md += f"* **NER F1**: {ner_f1:.4f}\n"
    md += f"* **NER Precision**: {ner_p:.4f}\n" # إضافة حاسمة للاختبار
    md += f"* **NER Recall**: {ner_r:.4f}\n"    # إضافة حاسمة للاختبار
    md += f"* **KG EM**: {kg_em:.4f}\n"
    md += f"* **RAG Grounding Rate**: {rag_gr_str}\n\n"
    md += "---\n\n"

    md += "## Methodologies\n\n"
    md += "### NER Methodology\n"
    md += f"{eval_ner.__doc__.strip()}\n\n"
    md += "### KG Methodology\n"
    md += f"{eval_kg.__doc__.strip()}\n\n"
    md += "### RAG Methodology\n"
    md += f"{eval_rag.__doc__.strip()}\n\n"
    md += "---\n\n"

    md += "## Per-Endpoint Detail\n\n"

    md += "### NER Evaluation (/extract)\n\n"
    md += "| Document ID | True Positives (TP) | False Positives (FP) | False Negatives (FN) | Status |\n"
    md += "| --- | --- | --- | --- | --- |\n"
    for doc in ner_docs:
        doc_id = doc.get("document_id") or doc.get("doc_id", "unknown")
        tp = doc.get("tp", "-")
        fp = doc.get("fp", 0)
        fn = doc.get("fn", 0)
        status = "PASS" if (fp == 0 and fn == 0) else "FAIL"
        md += f"| {doc_id} | {tp} | {fp} | {fn} | {status} |\n"
    md += "\n"

    md += "### NER Evaluation (/extract)\n"
    md += "| Document ID | True Positives (TP) | False Positives (FP) | False Negatives (FN) | Status |\n"
    md += "| --- | --- | --- | --- | --- |\n"
    for doc in ner_docs:
        doc_id = doc.get("document_id") or doc.get("doc_id", "unknown")
        tp = doc.get("tp", "-")
        fp = doc.get("fp", 0)
        fn = doc.get("fn", 0)
        status = "PASS" if (fp == 0 and fn == 0) else "FAIL"
        md += f"| {doc_id} | {tp} | {fp} | {fn} | {status} |\n"
    md += "\n"

    md += "### KG Evaluation (/kg/query)\n"
    md += "| Question ID | Status | Matched |\n"
    md += "| --- | --- | --- |\n"
    kg_failures = []
    for q in kg_questions:
        status = "EXCLUDED" if q.get("excluded") else q.get("status", "unknown").upper()
        is_matched = q.get("matched") if "matched" in q else q.get("match", False)
        matched_str = "TRUE" if is_matched else "FALSE"
        md += f"| {q['question_id']} | {status} | {matched_str} |\n"
        if not is_matched and not q.get("excluded"):
            kg_failures.append(q)
    md += "\n"

    md += "#### KG Sample Failures\n"
    if kg_failures:
        for idx, f in enumerate(kg_failures[:3]):
            md += f"**Failure {idx+1} (ID: {f['question_id']})**:\n"
            md += f"* Question: {f.get('question', 'N/A')}\n"
            md += f"* Error/Status: {f.get('error', 'Mismatched Cypher Output')}\n\n"
    else:
        md += "* No failures recorded.\n\n"

    md += "### RAG Evaluation (/rag/answer)\n"
    md += "| Question ID | Status | Grounded |\n"
    md += "| --- | --- | --- |\n"
    rag_failures = []
    for q in rag_questions:
        status = q.get("status", "unknown").upper()
        grounded_str = "TRUE" if q.get("grounded") else "FALSE"
        md += f"| {q['question_id']} | {status} | {grounded_str} |\n"
        if not q.get("grounded") and q.get("status") != "declined":
            rag_failures.append(q)
    md += "\n"

    md += "#### RAG Sample Failures\n"
    if rag_failures:
        for idx, f in enumerate(rag_failures[:3]):
            md += f"**Failure {idx+1} (ID: {f['question_id']})**:\n"
            md += f"* Status/Error: {f.get('error', 'Ungrounded Citations or Length < 1')}\n\n"
    else:
        md += "* No failures recorded.\n\n"

    md += "---\n\n"

    md += "## Derived /metrics Signals\n\n"
    md += "| Endpoint | p95 Latency | Error Rate | Total Request Count |\n"
    md += "| --- | --- | --- | --- |\n"
    for endpoint in ["/extract", "/kg/query", "/rag/answer"]:
        sig = metrics_signals.get(endpoint, {"p95": 0.0, "error_rate": 0.0, "total_requests": 0})
        md += f"| `{endpoint}` | {sig['p95']:.3f}s | {sig['error_rate']:.2%} | {sig['total_requests']} |\n"
    
    return md


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="reports/evaluation-report.md",
        help="Where to write the Markdown report.",
    )
    args = parser.parse_args(argv)

    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    print("Running NER evaluation harness...")
    ner_result = eval_ner.run()

    print("Running KG evaluation harness...")
    kg_result = eval_kg.run()

    print("Running RAG evaluation harness...")
    rag_result = eval_rag.run()

    print("Reading signals from /metrics endpoint...")
    metrics_signals = {}
    for endpoint in ["/extract", "/kg/query", "/rag/answer"]:
        metrics_signals[endpoint] = {
            "p95": metrics_reader.get_p95_latency(endpoint),
            "error_rate": metrics_reader.get_error_rate(endpoint),
            "total_requests": metrics_reader.get_total_requests(endpoint),
        }

    print("Assembling the evaluation report...")
    report_content = assemble_report(ner_result, kg_result, rag_result, metrics_signals)

    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(report_content)

    print(f"Report successfully written to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())