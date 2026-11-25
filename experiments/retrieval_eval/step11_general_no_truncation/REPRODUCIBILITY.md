# Step 11 Reproducibility

## Command

```bash
source .venv/bin/activate
PYTHONPATH=backend:. python -m experiments.retrieval_eval.step11_general_no_truncation.run_step11_eval
```

Optional:

```bash
PYTHONPATH=backend:. python -m experiments.retrieval_eval.step11_general_no_truncation.run_step11_eval \
  --seeds 101,202,303,404,505 \
  --out-dir experiments/retrieval_eval/step11_general_no_truncation/results
```

Unit tests (no LLM):

```bash
PYTHONPATH=backend:. pytest -q experiments/retrieval_eval/step11_general_no_truncation/test_step11.py
```

## Fixed settings

| Setting | Value |
|---|---|
| Seeds | 101, 202, 303, 404, 505 |
| top_k | 5 |
| min_similarity | 0.5 |
| Temperature | from `settings.rag_temperature` (typically 0.2) |
| Model | from `settings.llm_model` (typically `llama3.2`) |
| Embedding | from `settings.embedding_model` (typically `nomic-embed-text`) |
| Execution order | question → config → seeds |
| Frozen guard SHA-256 | `4ab51eb2ad25a7ece5062878ae713c4537df54368ee9324139b891fbaf11eae6` |

## Isolation

- Experimental code only under `experiments/retrieval_eval/step11_general_no_truncation/`
- Does not modify production RAG, prompts, DB, embeddings, or `evidence_guard.py`
- Does not overwrite Step 8/9/10 artifacts

## Outputs

- `results/step11_results.json` — raw per-question / per-seed scores
- `../GENERAL_TRUNCATION_ABLATION_REPORT.md` — final report
