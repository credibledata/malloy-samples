# The ecommerce golden set

An eval set anyone can run: 49 questions against the `ecommerce` package, each with the answer we
are prepared to defend and the query that proves it. Use it to try the eval loop in
[ms2data/agent-skills](https://github.com/ms2data/agent-skills) (`skills/eval-loop`) before pointing
the loop at a model of your own.

```
set.json                 what this set is and is not good for; datasetVersion; the truth package
cases.jsonl              49 cases, 35 dev / 14 holdout: question, golden, rubric, expected entities
judge-regressions.jsonl  12 predictions pinned to human verdicts — the only check on the judge
verify_goldens.py        pointer: the verifier lives in agent-skills and runs before every arm
../../ecommerce-truth/   the truth package every golden is computed from
```

Run output goes under `runs/` and is not committed here. In your own repository, commit the run
record (`run.json`, `events.jsonl`) beside the set so one commit pins model and ledger together;
that is the loop's design, and this samples repo is the one place it does not apply.

## The rule that shapes everything else

A golden is scored **against** the semantic model, so it must never be **derived from** the semantic
model. Otherwise a modelling bug certifies its own golden and the eval reports that everything is
fine.

Every `canonicalQuery` therefore runs against `ecommerce-truth`, a sibling package exposing the same
parquet files as raw sources — no measures, no docs, no joins, no filters. It is a **separate
package** on purpose: it once lived inside the served tree, where `get_context` could retrieve the
raw sources right beside the model and quietly change what was under test. The answerer's Publisher
serves `ecommerce`; a second Publisher the answerer has no route to serves `ecommerce-truth`.

Every golden was derived two ways before it was written, and the check earned its keep: the model's
own reference answers were wrong more than once. What authoring found wrong in the model went into
the model (see `ecommerce/ecommerce.malloy`'s history), not into a file beside the goldens.

## Running it

You need a Publisher build (`packages/server/dist/server.mjs`), a checkout of `ms2data/agent-skills`,
and the `claude` CLI logged in. Everything below is run from the agent-skills checkout;
`<samples>` is this repository.

```bash
S=<agent-skills>/skills

# 1. Two servers, each in its own session so a closed shell cannot take it down.
#    The answerer's serves ONLY the model under test; the truth server serves ONLY the truth.
python3 $S/eval-loop/scripts/serve.py --publisher-dir <publisher>/packages/server \
  --server-root /tmp/evalroot  --port 4811 --mcp-port 4040 --trace-retrieval
python3 $S/eval-loop/scripts/serve.py --publisher-dir <publisher>/packages/server \
  --server-root /tmp/truthroot --port 4812 --mcp-port 4041
#    (each server root needs a publisher.config.json naming its one package by absolute path:
#     {"frozenConfig": false, "environments": [{"name": "samples",
#       "packages": [{"name": "ecommerce", "location": "<samples>/ecommerce"}]}]}  — and likewise
#     "ecommerce-truth" for the truth root)

# 2. Smoke one case (about $0.15), then the arm (a few dollars, a few minutes).
#    Goldens are re-derived from the truth server first; a drifted set refuses to run.
python3 $S/eval-loop/scripts/run_baseline.py --set <samples>/evals/ecommerce \
  --out <samples>/evals/ecommerce/runs/smoke --only ecom_profit --no-judge \
  --environment samples --package ecommerce \
  --mcp-url http://localhost:4040/mcp --publisher http://localhost:4811 \
  --truth-publisher http://localhost:4812
python3 $S/eval-loop/scripts/run_baseline.py --set <samples>/evals/ecommerce \
  --out <samples>/evals/ecommerce/runs/baseline --label baseline --parallel 4 \
  --environment samples --package ecommerce \
  --mcp-url http://localhost:4040/mcp --publisher http://localhost:4811 \
  --truth-publisher http://localhost:4812

# 3. Diagnose what failed, then browse the run.
python3 $S/eval-diagnose/scripts/diagnose.py --run <samples>/evals/ecommerce/runs/baseline \
  --set <samples>/evals/ecommerce --model-dir <samples>/ecommerce \
  --environment samples --package ecommerce --mcp-url http://localhost:4040/mcp
python3 $S/eval-loop/scripts/build_run_package.py --run <samples>/evals/ecommerce/runs/baseline \
  --set <samples>/evals/ecommerce --out <samples>/evals/ecommerce/runs/pkg-baseline
#    serve runs/pkg-baseline with Publisher and open its public/index.html
```

`skill:eval-loop` in agent-skills is the full procedure — noise band, A/B, the golden side door,
what the improve step may and may not touch. Start there before reading a number off one run: a
single arm's flip against another is inside judge noise about one case in twenty.

## What the set is designed to measure

**Coverage.** Every case carries a `coverage` level: `covered` (a measure or view names the concept),
`derivable` (the columns exist, no entity does; the agent builds it), or `absent` (the data does not
exist). Only `absent` makes a refusal correct; a `derivable` question is answerable and declining it
is a failure. The `coverageNote` on each derivable row names the entity that would close it — that
column is the model-improvement backlog. Of the 45 answerable cases, 21 are `covered` and 24
`derivable` — over half have no entity for their concept, nearly all traceable to one absence: the
model has counts, sums, an average and a share-of-total, and no way to express one population as a
share of another. The set does not reach eleven of the model's measures and views (`sales_by_state`,
`top_brands`, `by_year`, `percent_of_sales`, `average_gross_margin`, `recent_purchases`,
`frequent_returners`, the four dashboards); a retrieval number read off this set does not cover them.

**Refusal, in both directions.** Four cases ask for data the model does not carry (ad spend, cart
funnel, stock-on-hand history, support tickets) and declining is the pass. Four more sound exactly
like those and are answerable, and declining is the failure. The two arms are deliberately adjacent:
`ecom_stockout_revenue_loss` and `ecom_unsold_stock_value` resolve to the same figure, inadmissible as
revenue lost to demand that never existed and correct as the cost of stock on hand. No policy passes
both; the agent has to read the question.

**Expected entities.** Every answerable case names the entities the answer depends on
(`expectedEntities.required`, `requiredAnyOf` where the model offers more than one route,
`acceptable`), derived from a `modelQuery` that reproduces the golden through the model — so a rename
breaks the query loudly instead of rotting the list silently. That is what makes a failure
attributable: retrieval delivered everything and the answer is wrong → the query; an entity was never
delivered → coverage says whether search or the model is at fault.

**Two kinds of wrong.** A business question almost never has one defensible reading. Every entry in a
golden's `alternates[]` carries `accept`: `true` is a definitional divergence — the agent computed a
different but defensible reading correctly, which is a finding against the model's docs, not the
agent; `false` is structural — a fan-out, a wrong grain, a double count — wrong under every reading,
and the class the pass rate is about.

## Checking the judge, not the model

```bash
python3 $S/eval-loop/scripts/check_judge.py --set <samples>/evals/ecommerce [--repeat 3]
```

`judge-regressions.jsonl` holds predictions pinned to verdicts a human settled; this re-judges them
through the same code path a run uses. It is the only thing here that asserts the judge is
**correct** — a noise band only shows it is repeatable, and a judge that always said `no_match`
would post a perfect band. Run it after any edit to the judge or a rubric. Do not delete an entry;
each earned its place by being contested.

## Verifying the goldens by hand

`run_baseline.py` does this before every arm. To do it alone, after a repair or a data change:

```bash
python3 $S/eval-answer/scripts/verify_goldens.py --set <samples>/evals/ecommerce \
  --publisher http://localhost:4812 --environment samples --model <samples>/ecommerce/ecommerce.malloy
```

It re-derives every golden from the truth package and exits non-zero if one no longer holds. It is
**not** an answer oracle — whether an agent's answer is right is the judge's call — and it cannot
tell you the `canonicalQuery` is the right query for the question; a query encoding a wrong reading
re-derives green forever. Neither check substitutes for reading the question against its query.
