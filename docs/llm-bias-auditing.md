# From tabular fairness to LLM bias auditing

FairLens today audits **tabular classifiers**: you hand it `(label, prediction, sensitive_attribute)`
triples and it returns seven fairness metrics mapped to the EU AI Act, NIST AI RMF, and ISO/IEC 42001.
None of that machinery is specific to gradient-boosted trees. This note shows how the same metrics and
the same SHAP proxy-discrimination logic extend to **large language models** — auditing demographic
bias, toxicity disparities, and refusal disparities — with a thin adapter rather than a rewrite.

The point is the reduction: **a fairness audit only needs three aligned vectors.** Whatever produces
them — XGBoost or an LLM — the statistics, thresholds, and regulatory mapping are identical.

```python
# backend/app/services/fairness/metrics.py — already model-agnostic
compute_all_metrics(
    y_true,                 # ground-truth label, binarized to {0,1}
    y_pred,                 # the model's decision, binarized to {0,1}
    sensitive={"group": s}, # demographic group id per example
    positive_label=...,
    favorable_prediction=...,
)
```

The only real work in adapting to an LLM is **defining `y_pred` for a generative model.** There are
four natural framings, in increasing distance from the tabular case.

---

## 1. Decision-task LLMs — zero adaptation

When an LLM is used as a *classifier* (resume screening, content moderation, loan triage, eligibility
checks), it emits a label. That label *is* `y_pred`. The seven metrics apply unchanged:

- Build an evaluation set of prompts tagged with the relevant sensitive attribute (e.g. CVs that are
  identical except for a name signalling gender or ethnicity).
- Parse the model's verdict into `{0,1}` (`hire`/`no-hire`, `allow`/`block`).
- Call `compute_all_metrics` exactly as the tabular pipeline does.

Demographic parity, disparate impact (the EEOC 4/5ths rule), and equal-opportunity gaps are immediately
meaningful here, and the regulatory mapping in `regulatory.py` already governs "AI systems making or
informing decisions about people" — which a prompted LLM classifier is.

## 2. Token log-probability bias — counterfactual pairs

The interesting LLM-native case is bias in the model's **probabilities**, before any hard decision.
Use **counterfactual prompt pairs** that differ only in a demographic token, and read the model's
log-probabilities for a target completion:

```
P("competent" | "The {man|woman} is very ___")
P("nurse"     | "{He|She} works as a ___")
P(refusal     | "Write a reference letter for {a man|a woman} named ...")
```

Define a per-group score as the mean (log-)probability the model assigns to the target token across the
group's prompts. That continuous score slots straight into the metric definitions:

- **Demographic parity difference** → `max_g(mean P_g) − min_g(mean P_g)` over groups: the gap in how
  readily the model produces the association. This is exactly `demographic_parity_difference`'s
  `max(SR_g) − min(SR_g)` with the "selection rate" generalized from a rate to a mean probability.
- **Disparate impact ratio** → `min_g / max_g` of those means — direction-agnostic, so neither group
  has to be hard-coded as the reference.

Log-probs make the audit *sensitive*: you detect skew long before it flips a discrete decision, which
matters for early-warning evaluation.

## 3. Toxicity & refusal disparities — equalized odds on a behavior

Treat a **model behavior** as the binary prediction and ask whether error rates differ across groups:

- `y_pred = 1` if the output is flagged toxic (by a toxicity classifier), `y_true` = whether the input
  was *actually* a policy violation. Now **equalized odds** asks: at equal true-violation rates, does
  the model's false-positive rate differ across input dialects (e.g. AAVE vs. SAE)? A large
  `fpr_gap` means benign text from one group is disproportionately flagged.
- `y_pred = 1` if the model **refused**. Equalized-odds / equal-opportunity gaps then quantify
  over-refusal disparities — refusing benign requests more often for one group — which is a concrete,
  measurable over-alignment failure.

`equalized_odds_difference` already returns `max(tpr_gap, fpr_gap)` with both components broken out, so
this is a direct reuse.

## 4. Calibration of model confidence

For an LLM that emits a probability or an LLM-as-judge that scores on a scale, `calibration_difference`
generalizes to **per-group expected calibration error** — does a stated 0.9 confidence mean the same
thing for inputs about different groups? The metric's own docstring already anticipates this: *"with
probability scores, replace with expected calibration error per group."* That swap is the only code
change required.

---

## Metric-by-metric mapping

| FairLens metric (tabular) | LLM analogue | Concrete probe |
|---|---|---|
| Demographic parity difference | Gap in mean P(target token) or favorable-decision rate across groups | Counterfactual name-swap on a hiring prompt |
| Disparate impact ratio | `min/max` of those group means (4/5ths rule) | Same, reported as a ratio for EEOC framing |
| Equal opportunity difference | TPR gap on a behavior given a true-positive condition | Among genuinely toxic inputs, detection-rate gap by dialect |
| Equalized odds difference | `max(TPR gap, FPR gap)` of a behavior | Over-refusal / over-flagging of benign inputs by group |
| Predictive parity difference | PPV gap of a flag | When the model flags content, is it right equally often per group? |
| Calibration difference | Per-group expected calibration error | Does stated confidence mean the same across groups? |
| Individual fairness consistency | Counterfactual invariance | Does swapping only the demographic token leave the output (nearly) unchanged? |

The last row is the cleanest conceptual bridge: **individual fairness consistency** already measures
"similar inputs get similar predictions." For LLMs that becomes **counterfactual fairness** — the
output should be invariant to a demographic token that is causally irrelevant to the task. Same metric,
distance defined over prompt embeddings instead of standardized tabular features.

## SHAP → token attribution and proxy discrimination

FairLens's `shap_analyzer.py` does more than rank features — it flags **proxy discrimination**: a
feature whose mean `|SHAP|` differs across groups beyond a threshold is driving the prediction in a
group-dependent way (a proxy for the protected attribute even when that attribute isn't an input).

The LLM analogue is **token / span attribution** (SHAP's partition explainer over tokens, or
attention/gradient-based attribution). The proxy-discrimination check transfers directly: flag tokens or
concepts whose attribution to the model's decision is systematically larger for one demographic framing.
A moderation model whose "block" decision is disproportionately attributed to dialect markers — rather
than to the actual policy-violating content — is keying on a proxy, exactly the failure mode the tabular
version catches. The threshold logic and the "consolidated proxy suggestion" output need no change; only
the attribution backend does.

## What an LLM adapter would look like

Minimal, because the core is already model-agnostic:

```
backend/app/services/fairness/
├── metrics.py          # unchanged — consumes (y_true, y_pred, s)
├── regulatory.py       # unchanged — framework clauses are model-independent
├── shap_analyzer.py    # swap tree-SHAP for a token attribution backend
└── llm_adapter.py      # NEW: (prompt_set, model, grouping) -> (y_true, y_pred, s [, scores])
```

`llm_adapter.py` is the only new component: it runs the eval prompts through the model (label, log-prob,
or behavior flag depending on the framing above), assembles the three vectors, and hands them to the
existing `compute_all_metrics`. The regulatory mapping, scoring, risk classification, and PDF report all
come along for free — and the EU AI Act / NIST / ISO clauses FairLens cites apply just as squarely to a
deployed LLM as to a tabular model.

## Honest limitations

- **Generation isn't a single label.** Framings 1–3 require deliberate prompt design (counterfactual
  data augmentation) to isolate the demographic variable; sloppy prompts measure prompt artifacts, not
  model bias.
- **Probability access.** Framing 2 needs token log-probs. Available from open models and most
  inference APIs, but not all hosted endpoints expose them.
- **Label noise compounds.** Toxicity/refusal labels (framing 3) come from classifiers that carry their
  own bias; an audit is only as trustworthy as its `y_true`.
- **Statistical fairness ≠ alignment.** These metrics quantify *measurable group disparities*. They are
  a necessary, regulator-legible slice of model safety — not the whole of it.

See [`backend/app/services/fairness/metrics.py`](../backend/app/services/fairness/metrics.py) for the
metric implementations and [`backend/app/services/fairness/regulatory.py`](../backend/app/services/fairness/regulatory.py)
for the framework mapping these examples reuse verbatim.
