# Known oligomeric state of plant NLRs — curation rubric (v0.1)

Pre-registered before any PubMed query is run. Post-v0.1 changes are recorded
with a version bump and a diff note in the change log at the bottom of this
file.

## A. Question the table answers

For a given NLR, what is the experimentally determined oligomeric state of its
**activated / effector-bound form** — the form AF3 is being asked to predict
when given 6 copies?

Inactive / autoinhibited state is not the ground truth. It is recorded as an
auxiliary observation.

## B. Scope

- Plant NLRs: CNL, TNL, NL, and helper/sensor variants thereof.
- Must have ≥1 primary publication (not review) reporting direct structural
  characterisation of the activated form.
- Excluded: homology-only inferences, purely computational predictions,
  genetics-only claims (these do not set `known_state` — see §D/§E).
- A parallel metazoan calibration set is maintained in
  `data/known_oligomer_states_metazoan.csv` under the same rubric. It is not
  merged into the plant primary table.

## C. `known_state` controlled vocabulary

`monomer | dimer | trimer | tetramer | pentamer | hexamer | heptamer | octamer_plus | unknown`

No `mixed`. If multiple stoichiometries are reported, the state is called from
the higher-resolution / effector-bound / more-recent structure; the
disagreement is logged in `notes`.

## D. Evidence tiers

State-setting tiers (any one is sufficient to set `known_state`):

1. `cryo-EM_highres` — cryo-EM of the activated complex, protomer count visible, ≤ 4 Å
2. `cryo-EM_lowres`  — cryo-EM or negative-stain of the activated complex, 4–10 Å, protomer count visible
3. `crystal`         — X-ray structure of the activated oligomeric complex

Non-state-setting tiers (recorded but do **not** set `known_state`):

4. `XL-MS`           — chemical crosslinking stoichiometry
5. `functional_only` — genetics: HR dependence, dominant-negative ratios, NLR–NLR requirements
6. `homology`        — inference from a related protein's structure

Native-MS and SEC-MALS are explicitly excluded from the rubric and do not
appear as evidence tiers.

## E. State-calling rule

- Tier 1–3 evidence → `known_state` = observed stoichiometry. `evidence_tier`
  = the strongest tier available.
- Tier 4–6 evidence only → `known_state = unknown`. `evidence_tier` records
  the strongest non-setting tier; `notes` records the claim (e.g.,
  "requires NRC2 for HR; PMID xxx").

## F. Activation-state rule

- Grade the activated form.
- If only an inactive / autoinhibited structure exists → `known_state = unknown`;
  `notes` records the inactive stoichiometry and its tier.
- If both states exist → grade the activated; record inactive in `notes`.
- `activation_state_graded` ∈ `{activated, inactive, NA}` records which form
  the call is based on.

## G. Conflicts and ambiguity

- Preprints: included only if the structure is deposited (PDB or EMDB ID
  required).
- Structures disagreeing on stoichiometry: both recorded; call from the
  higher-resolution / most-recent / effector-bound structure; disagreement
  logged in `notes`.
- Every judgement call is flagged in `notes` and referred to Dan. No silent
  calls.

## H. Columns

`ID | protein_family | organism | known_state | evidence_tier | functional_call | source_pmid | source_pdb | activation_state_graded | AF3_6mer_run | in_current_18 | notes`

- `functional_call` ∈ `{helper, sensor, singleton, other, NA}`. Preserves the
  genetics-derived class independently of structural evidence.
- `AF3_6mer_run` ∈ `{TRUE, FALSE}`: whether this protein has been run through
  the AF3 6-copy pipeline in this project.
- `in_current_18` ∈ `{TRUE, FALSE}`: whether this protein is a member of the
  18-protein labelled benchmark used in notebook 002. The relationship is
  recorded for traceability only — the 002 labels are **not** modified by
  this table.

## I. Symmetric application to the 18-protein set

The 18 current proteins are graded under the same rubric:

- NRC helpers with cryo-EM of the resistosome form → tier 1/2, `known_state = hexamer`.
- NRC helpers with genome-derived sequences but no structure → `known_state = unknown`.
- Sensors whose only evidence is functional non-dependence → tier 5, `known_state = unknown`.

This may shrink the structurally-defensible labelled set. The 002
helper/sensor labels are unaffected; this table exists for a different
question (does an AF3 6mer prediction match the known oligomeric state?).

## J. Audit log

Every PubMed query committed under §K is logged in
`data/known_oligomer_states_audit.csv` with: date, query string, hit count,
per-hit disposition. Disposition reasons come from the closed set:

`included | not_plant_NLR | homology_only | no_structure | inactive_only | review | duplicate | ambiguous`

Queries run after v0.1 is locked are tagged `post_hoc` and treated with
suspicion in downstream reporting.

## K. Pre-registered PubMed queries

Locked 2026-04-23. Any query added after this date is tagged `post_hoc` in
the audit log.

### Plant primary set

**P1 — Plant NLR × structural method.** High recall for any plant NLR paper
that explicitly reports a cryo-EM or crystallographic structure.

```
(("plant"[TIAB] OR Arabidopsis[TIAB] OR tomato[TIAB] OR Solanum[TIAB]
  OR Nicotiana[TIAB] OR wheat[TIAB] OR rice[TIAB] OR "Plant Diseases"[MeSH])
 AND ("NLR"[TIAB] OR "NB-LRR"[TIAB] OR "CC-NLR"[TIAB] OR "TIR-NLR"[TIAB]
      OR "TNL"[TIAB] OR "CNL"[TIAB]
      OR "nucleotide-binding leucine-rich repeat"[TIAB])
 AND ("cryo-EM"[TIAB] OR "cryoelectron"[TIAB]
      OR "crystal structure"[TIAB] OR "X-ray structure"[TIAB]))
```

**P2 — Resistosome-centric.** "Resistosome" is plant-immunity-specific, so no
taxonomic filter is needed.

```
("resistosome"[TIAB] OR "pre-resistosome"[TIAB] OR "plant inflammasome"[TIAB])
```

**P3 — Named-gene sweep (curated list, acknowledged bias).**

```
(ZAR1[TIAB] OR Sr35[TIAB] OR RPP1[TIAB] OR Roq1[TIAB] OR ROQ1[TIAB]
 OR NRC2[TIAB] OR NRC3[TIAB] OR NRC4[TIAB]
 OR "Pik-1"[TIAB] OR "Pik-2"[TIAB] OR RGA4[TIAB] OR RGA5[TIAB] OR RPM1[TIAB])
AND ("structure"[TIAB] OR "cryo-EM"[TIAB] OR "crystal"[TIAB]
     OR "resistosome"[TIAB] OR oligomer*[TIAB])
```

### Metazoan calibration set

**M1 — Inflammasome (conservative: NAIP/NLRC4 only).**

```
(NLRC4[TIAB] OR NAIP[TIAB])
AND ("cryo-EM"[TIAB] OR "crystal structure"[TIAB]
     OR oligomer*[TIAB] OR stoichiometry[TIAB])
```

**M2 — Apoptosome family.**

```
("Apaf-1"[TIAB] OR Apaf1[TIAB] OR apoptosome[TIAB]
 OR "CED-4"[TIAB] OR "Dark apoptosome"[TIAB])
AND ("cryo-EM"[TIAB] OR "crystal structure"[TIAB] OR oligomer*[TIAB])
```

### Honesty notes

- **P3 gene list is a curation decision, not a derivation.** Names were
  chosen in conversation between Dan and the assistant as "plant NLRs we
  believe or have heard have structural data". It is not derived from a
  systematic review. Consequence: any plant NLR with a published structure
  not named here is caught only by P1 or P2. P3 therefore raises recall for
  expected hits; recall for unexpected hits is P1/P2's responsibility.
- **Rx, Gpa2, Bs2, Rpi-AMR, Rpi-NIG are deliberately absent from P3.** We
  hold no prior that they have published structural data; including them
  would conflate "names in our benchmark" with "names we expect hits for".
  If P1/P2 surface them, they surface legitimately.
- **Functional-pair names (CSA1/CHS3, RPS4/RRS1) were considered and dropped
  from P3** on Dan's call, on the grounds that their literature is
  genetics-heavy and including them would inflate P3's noise with
  functional-only hits that `evidence_tier` will reject anyway.
- **P1 was tightened from an earlier draft** by removing loose oligomer
  vocabulary (`oligomer*`, `pentamer*`, `hexamer*`, `tetramer*`) from the
  structural-method clause. A paper reporting a real structure will name its
  method; papers that only mention stoichiometry in passing are correctly
  caught — or correctly not caught — by P2 and P3.
- **M1 was restricted to NAIP/NLRC4** rather than the broader inflammasome
  literature (NLRP1, NLRP3, ASC speck) on Dan's call. NLRP3 in particular
  has a vast, messy structural literature whose oligomeric states are
  contested; including it would drag the calibration set off-axis.

---

## Change log

- **v0.1 (2026-04-23)** — initial rubric. §K queries locked same day.
