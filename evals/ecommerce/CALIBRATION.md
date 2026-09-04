# Calibration record: ecommerce

**There is no band for this set yet. Nothing may be compared against a run of
it until there is.** That is not an oversight to work around; a flip count with
no band is a number with no claim on anything.

`skill:eval-loop`'s `reference/measurement.md` defines what belongs here. One
block per configuration, written by the tool rather than by hand:

```bash
python3 <skills>/eval-loop/scripts/flip_table.py \
  --a runs/aa-1 --b runs/aa-2 --calibration >> evals/ecommerce/CALIBRATION.md
```

An A/A is the same model, the same config and this same set, run twice. Every
flip it reports is noise by construction, because nothing changed between the
arms. Budget two arms, about $18 on Sonnet at 49 cases.

## Why a band does not carry over

Each block names the pins the number is a property of: `datasetVersion`,
`datasetSha`, `judgeVersion`, `rubricSha`, `answererModel`, `judgeModel`,
`answererManifest`, `retrievalMode`. **Quote a band only for a run whose pins
all match a block.** Observed bands have moved by a factor of three across a
fortnight of ordinary work.

The band this set had, two flips, was measured at dataset v9 against judge v3
with a bare-model answerer. Every one of those has moved: the set is v13, the
judge is v4, and the loop now loads a manifest of skills into the answerer. So
that number describes a configuration nobody is running and it is recorded here
only to say it is retired.

## What the first block needs

- Two A/A arms on the current harness, which records `retrievalMode`. A run
  that cannot say which retriever answered cannot anchor a comparison, because
  local retrieval degrades to lexical silently with no embedding key.
- Both arms `semantic`, or both `lexical` with the block saying so. `flip_table.py`
  refuses a mismatched pair.
- The judge fixtures reproducing first (`check_judge.py --set . --repeat 3`).
  A band measures whether the judge is repeatable and says nothing about
  whether it is right, so a band over an unchecked judge can be perfect and
  meaningless.

## Judge fixtures

`judge-regressions.jsonl` holds 12 human-settled predictions. Two known gaps,
both reported by `check_judge.py`:

- **11 of the 12 carry no `goldenRevision`.** They were settled 2026-08-31
  against judge v3, and several goldens were revised afterwards to the rubric
  clause standard, so what each fixture asserts cannot be established from the
  record. Re-settling is a judgement per fixture, not a stamp: run
  `check_judge.py --repeat 3`, keep the pins for the ones that still reproduce,
  and re-read the ones that moved before deciding whether the judge or the
  fixture is wrong.
- **The five decision classes `check_judge.py` requires are uncovered.** The
  current `protects` labels name tracks of an earlier investigation rather than
  judge decisions. Both of the set's headline failures turned on a `REQUIRED`
  disclosure and no fixture covers that; nor refusal in either direction, nor
  `gold_status`. Seed each from a real prediction and settle it by hand. Never
  author a prediction to fill a slot.

Then break one rubric on purpose and confirm the right fixture fails
(`reference/checking-the-judge.md` has the drill). A fixture that has never
failed is not yet known to be a test.
