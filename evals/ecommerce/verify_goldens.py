#!/usr/bin/env python3
"""Moved. The golden verifier is now shared by every set:

  ms2data/agent-skills  skills/eval-answer/scripts/verify_goldens.py
  python3 <agent-skills>/skills/eval-answer/scripts/verify_goldens.py \
      --set evals/ecommerce --publisher http://localhost:4811 --environment samples \
      --model ecommerce/ecommerce.malloy

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
