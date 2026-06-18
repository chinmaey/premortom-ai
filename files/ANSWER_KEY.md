# ANSWER KEY — planted risks (ground truth for evaluation)

This is YOUR ground truth. Each proposal was written with a known set of risks.
Validation = did PreMortem catch these (recall) without inventing extras
(false alarms), and did it reach the right decision direction?

NOTE: scores/exposure are not ground-truth-able — only check the DECISION
direction and the RISKS FOUND.

---

## proposal_01_medical_nogo.md  — expected decision: NO-GO
Planted risks:
1. Excessive advance — 70% on PO vs ~30% norm (financial exposure).
2. Warranty starts on delivery, not commissioning — burns during 16-week
   install + site delay (contract).
3. Site not ready — civil 60%, RF shielding not started, power/chiller pending
   (infrastructure / readiness).
4. No trained staff — 0 of 2 technologists hired (workforce).
5. No acceptance-testing / performance-qualification clause (contract).
6. Vendor reliability flag — prior supply disruption + terminated contract
   (vendor / historical).
7. Single-source, no price benchmarking (financial / contract).
Expected: HIGH score, NO-GO, conditions covering advance %, warranty start,
site readiness, staffing.

---

## proposal_02_acoustic_hats.md  — expected decision: NO-GO or GO-WITH-CONDITIONS
Planted risks:
1. Excessive advance — 80% via LC (financial).
2. Warranty starts on delivery, not commissioning (contract).
3. Lab/chamber not ready; environmental controls not installed
   (infrastructure / readiness).
4. No accredited calibration clause; no recalibration interval (contract /
   fitness-for-use).
5. No trained operator; training not included (workforce).
6. Sole-source / single-vendor lock-in (vendor concentration).
7. FX + customs exposure not quantified (financial).
Expected: HIGH score; NO-GO or GO-WITH-CONDITIONS; proves the tool works on a
NON-MEDICAL case.

---

## proposal_03_clean_go.md  — expected decision: GO
Planted risks: NONE material.
- Low value, reversible, ready site, standard terms (20/80), vetted GeM vendor,
  benchmarked price, 3-week delivery.
Expected: LOW score, GO. This is the FALSE-ALARM test — if PreMortem flags
serious risks here, that is a precision failure to fix.
