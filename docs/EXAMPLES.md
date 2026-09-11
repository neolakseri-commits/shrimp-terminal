# Worked examples

Every number in Shrimp Terminal resolves to observed, checkable facts. This file
walks a few rows from the shipped fixture sample — including cases that are
**not** counted — so the grading rules are unambiguous.

A **rotation** is one wallet that sold coin A and then bought coin B inside a
chosen window (5 min / 30 min / 2 h). The grade describes only what the chain
shows about that wallet in that window. It never implies the sale funded the
buy, that the addresses share an owner, or that anything will happen next.

## Grades

| Grade | Rule |
|-------|------|
| `direct` | the sell and the buy are in the **same transaction** |
| `clean` | the wallet sold **only coin A** in the window before buying B |
| `ambiguous` | the wallet **also sold other coins** in the window (listed, never counted in the edge weight) |

---

## Example 1 — `clean`

```
wallet   0xd60c…7ab6
sell     3,640,335 Piecoin  for 22.848 USDC   PONS curve   block 59570827   17:10:09 UTC
buy      9,788,825 TruffleHog for 49.159 USDC  PONS curve   block 59579393   17:24:35 UTC
```

- gap: 866 s, inside the 30-minute window.
- the wallet sold nothing except Piecoin in the window → **clean**.
- counts as **one wallet** on the edge `Piecoin → TruffleHog`.

## Example 2 — `clean`, short gap

```
wallet   0x9f22…5f7a
sell     1,200,000 SCRAPS      for 14.02 USDC   PONS   block 59579401   17:24:41 UTC
buy      6,410,222 TruffleHog  for 31.77 USDC   PONS   block 59579418   17:25:02 UTC
```

- gap: 21 s. Still two separate transactions, so **not** `direct`.
- only SCRAPS sold in the window → **clean**.

## Example 3 — `ambiguous` (a negative-ish case)

```
wallet   0x7e0a…1c2
sell     24,000,000 MINER    for 210.55 USDC   UniV4   block 59579424   17:25:11 UTC
buy      1,750,000 INFERNET  for 198.10 USDC   UniV4   block 59579431   17:25:28 UTC
also sold in window:  PACKZ, SAGA
```

- the wallet sold MINER **and** PACKZ and SAGA before buying INFERNET.
- graded **ambiguous**: the extra sells are **listed but never counted** in the
  weight of `MINER → INFERNET`. We do not guess which sale "paid for" the buy.

## How counting works

An edge weight is a count of **distinct wallets** with a `direct` or `clean`
rotation on that route in the window — never a count of rows. A wallet that sold
once and bought nine times contributes **nine rows but one wallet** to the edge.
Ambiguous rotations are shown in context but excluded from the weight.

## What none of this means

- Not proof that coin A's sale funded coin B's purchase.
- Not proof two addresses share an owner.
- Not a prediction. The radar ranks observed inflow; it does not forecast price.
