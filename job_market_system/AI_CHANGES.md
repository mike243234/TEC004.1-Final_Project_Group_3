# AI additions — what changed and why

## Summary of the diff

**New files:**
- `ai/__init__.py`, `ai/advisor_llm.py` — LLM-generated advisor narrative
- `ai/embeddings.py` — semantic job embeddings + recommendation

**Modified files:**
- `recommender.py` — `analyze_career_ai()` now calls the LLM for the
  `ai_advice` text, falling back to the original template if Ollama
  isn't available. Nothing else in that function changed (the scoring
  logic, `role_map`, `salary_benchmarks` are all untouched).
- `api.py` — imports the new `ai.embeddings` functions, calls
  `rebuild_embeddings()` right after every scrape finishes, and adds two
  endpoints: `GET /api/ai/similar-jobs/{job_id}` and
  `POST /api/ai/match-profile`.
- `requirements.txt` — added `sentence-transformers` and `ollama`.

Nothing in `web/index.html` needed to change — the advisor tab already
renders `ai_advice`/`matched_skills`/`missing_skills` exactly the way it
did before, it's just genuinely AI-generated now instead of templated.

## Why I dropped the "LLM extraction" idea from before I'd seen your code

`extractor.py` already does thorough regex-based extraction — skill
aliases, Vietnamese/English salary parsing, negotiable-salary handling,
experience-level inference. An LLM re-extracting those same fields would
be redundant, slower, and arguably less reliable than what you already
built (it's the kind of domain-specific rule system an LLM would need
many examples to match). So the AI additions target the two places that
actually needed it: the advisor's prose, and semantic search over jobs.

## Setup

1. **Install Ollama** (free): https://ollama.com/download
2. **Pull a model**, once:
   ```
   ollama pull llama3.2
   ```
   (~2GB, 3B params, runs fine on CPU for a project demo — try
   `ollama pull qwen2.5:3b` if your machine is slower)
3. **Install the two new Python packages:**
   ```
   pip install -r requirements.txt --break-system-packages
   ```
4. **Run a scrape** (`POST /api/scrape`, or just start the app — it
   scrapes on startup) — `rebuild_embeddings()` runs automatically
   afterward and populates a new `job_embeddings` table it creates for
   itself the first time it runs. No manual schema migration needed.
5. Everything else — `/api/advisor` — works exactly as before, just with
   real generated advice instead of templates.

## Why full rebuild instead of incremental embedding updates

`JobDatabase.reset()` drops and recreates the `Jobs` table on every
scrape, so job ids restart from 1 each time. An incremental "only embed
new jobs" approach would leave stale `job_embeddings` rows pointing at
whatever job now has that reused id — silently wrong results. So
`rebuild_embeddings()` clears and recomputes everything each time. For
~500 jobs that's a few seconds on CPU, which is cheap enough not to
bother optimizing for a project this size.

## Verified against your actual data

I ran both changes against your real `data/jobs.db` (494 jobs) before
handing this back:
- `recommender.analyze_career_ai()` runs end-to-end and produces
  correctly-formatted advice (confirmed the fallback path specifically,
  since this sandbox doesn't have Ollama installed).
- `ai/embeddings.py`'s SQL joins, BLOB serialization, and ranking logic
  all run cleanly against your schema and return properly hydrated
  results (title/company/location/salary attached to every match). The
  only piece I couldn't test here is the actual model download, since
  this sandbox's network doesn't reach huggingface.co — that'll resolve
  itself the first time you run it with normal internet access.
- `api.py` imports cleanly with all 18 routes registered, including the
  two new ones.

## Plain-English glossary (for your report/defense)

- **Embedding** — a few hundred numbers representing what a piece of
  text means. Built here from `title + level + location + skills`,
  e.g. `"Backend Developer. Level: Senior. Location: Hà Nội. Skills:
  Python, Django, PostgreSQL."` — two jobs with similar meaning end up
  numerically close even without sharing exact words.
- **Cosine similarity** — the score (-1 to 1) behind "similar jobs" and
  "jobs matching your profile". Vectors are normalized, so it's just a
  dot product (`vectors @ query_vec` in the code).
- **LLM (large language model)** — running locally through Ollama, no
  API key or internet needed after the model is pulled once. Used only
  for turning already-computed facts into readable prose — the scoring
  and matching logic itself stays deterministic and inspectable.

## Talking points for your presentation / defense

- **You upgraded a real weak point, not a hypothetical one.** The
  original `analyze_career_ai()` was named "AI" but contained no model —
  that's exactly the kind of thing a grader who reads the code will
  notice. You can show the before/after directly.
- **Graceful degradation is a deliberate design choice**, not a gap —
  the advisor still works without Ollama running, it just falls back to
  the original template. Worth calling out explicitly; it shows you
  thought about failure modes, not just the happy path.
- **Add one small evaluation if you have time.** For example: pick 10
  advisor requests with different skill sets, and manually rate whether
  the LLM advice or the template advice is more specific/useful. A
  before/after comparison is a strong thing to show live.
- **Full-rebuild-on-every-scrape is a real architectural constraint you
  navigated**, not an accident — worth a sentence in your write-up on
  why embeddings are rebuilt in full rather than incrementally.
