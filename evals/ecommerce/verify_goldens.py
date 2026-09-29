#!/usr/bin/env python3
"""Moved. The golden verifier is now shared by every set, and lives with the
skills in malloydata/publisher -- the source of truth for them, per README.md;
the ms2data/agent-skills mirror can be behind, and the scripts are the harness.

  python3 <publisher>/skills/eval-answer/scripts/verify_goldens.py \
      --set evals/ecommerce --publisher http://localhost:4812 --environment samples \
      --model ecommerce/ecommerce.malloy

`--publisher` is the TRUTH server, 4812 in README.md's layout, and it has no
default: a golden re-derived through the port the ANSWERER is on tells you
nothing. Omit it and the value check reports as not run (exit 3) instead of
guessing. The verifier also refuses a server that holds the model under test
alongside the truth package, because an answerer there can retrieve the raw
truth sources beside the model.

What this set needed that the shared script did not have is now a `set.json`
field: `truthTableRewrite: true` rewrites `duckdb.table('data/x.parquet')` in a
canonical query to the bare source name the truth model binds to the same file.
`run_baseline.py` runs the verifier before every arm and refuses to start on a
drifted set, so there is no longer a reason to run this by hand except after a
repair. This stub exists so an old command line says where to go instead of
failing on a missing file.
"""
import sys

sys.exit(__doc__)
