# Step 11 H2 Dataset (Q28–Q47)

Independent held-out evaluation split for the GENERAL truncation ablation.

## Independence

| Split | IDs | Prior use |
|---|---|---|
| Dev | Q1–Q7 | Steps 5–8 guard development |
| H1 | Q8–Q27 | Step 9 held-out generalization |
| **H2** | **Q28–Q47** | **Step 11 only** |

H2 was not used to design or tune the ablation logic. Ablation removes only `_chunk_truncated` from the GENERAL sufficiency check (see `general_no_truncation_guard.py`).

## Ground-truth method

1. Primary chunk labels chosen from NovaForge policy corpus already embedded in the local DB.
2. Answer-key facts verified by string presence in the cited primary chunk text (offline probe).
3. Answer keys live in `h2_answer_key.py` and are imported **only** by scoring — never by the guard or planner.
4. No question IDs are hardcoded in runtime decision logic.

## Coverage map

| Category | Example IDs | Notes |
|---|---|---|
| Procedure | Q46, Q47 | Keyword need → `procedure` |
| Requirement evidence | Q45 | Keyword need → `requirement_evidence` |
| Duration / timing | Q33, Q34 | May classify as `duration_table` |
| General policy / numerical / list / contact | Q28–Q32, Q35–Q44 | Mostly `general` |
| Neighbor may help | Q41, Q47 | Annotated `expects_neighbor_helpful=True` |
| Original evidence usually sufficient | remaining | Primary in top-5 on probe |
| Chunk-boundary / truncation | most | 500-char windows; top-5 almost always includes truncated hits |
| Distracting adjacent content | Q28, Q40, Q43 | Non-primary neighbors can enter hybrid |

## Files

- `h2_dataset.py` — questions + offline annotations
- `h2_answer_key.py` — scoring facts
- `h2_scoring.py` — 7-metric rubric (max 28)
- `DATASET.md` — this document
