# Rihai (रिहाई)

**Release eligibility of undertrial prisoners under Section 479 of the Bharatiya Nagarik Suraksha Sanhita, 2023.**
The code decides; the model narrates.

Bharat Agentic-AI Hackathon 2026 (Code for India), impact area: Timely Justice / Legal Backlog.
Built in AgentFoundry. MIT licence. Built by Sainath Gaikwad (Pune); field pilot with Pushkar.

## The problem

India's prisons held 5,34,993 people in September 2025 (NALSA UTRC report). About three in four are undertrials.
Section 479 BNSS (in force 1 July 2024) says an undertrial must be released on bail after serving half the maximum
sentence for the offence charged, and a first-time offender on bond after one-third; nobody may be held beyond the
maximum term at all. The Supreme Court ordered every state to apply it proactively (*In Re: Inhuman Conditions in
1382 Prisons*, 23 Aug and 22 Oct 2024).

It is not happening at scale. Between July 2024 and April 2025 only 951 undertrials were identified as eligible and
334 released nationally (Rajya Sabha, 3 Apr 2025). In the whole of Q3 2025: 591 identified, 393 released (NALSA).
The bottleneck is identification. A jail superintendent compiles a roster by hand, a DLSA secretary prepares an
eligibility list by hand, and the Undertrial Review Committee meets once a quarter. The arithmetic is simple and
nobody runs it continuously across 1,300 prisons.

## What Rihai does

1. **Eligibility, deterministically.** Takes a prison roster (charge sections, custody start date, prior
   convictions) and computes Section 479 eligibility against a law table of maximum sentences. Every rule in
   [`rihai/eligibility/s479.py`](rihai/eligibility/s479.py) maps to a line of the section. Unknown sections are
   refused. Ambiguous ones (a bare "Section 118" that could be 3 years or life; attempt to murder, where life depends
   on whether hurt was caused) come back as `NEEDS_REVIEW` with the reason.
2. **Drafts, from the assessment only.** For each eligible prisoner it drafts the Section 479 application and the
   DLSA/UTRC memo. In template mode no model is involved, so the draft cannot contain a figure the engine did not
   compute. A model (Muse Spark, Nemotron, Claude) may rewrite the prose or translate it to Hindi and Marathi.
3. **A citation gate.** Every statutory reference in any draft, model-written or not, must resolve to the law
   table or to the short list of procedural provisions a s.479 application may cite. One unknown section blocks the
   draft. Same idea as SEEN's claim checker, pointed at sections instead of numbers.

Nothing in Rihai files anything, sends anything or decides anything. Legal-aid counsel reviews; the court decides.

## Try it

```bash
pip install -r requirements.txt
python -m pytest -q                              # 24 tests on the rule and the gate
streamlit run rihai/app/streamlit_app.py         # one prisoner / roster CSV / law table
python -m rihai.law.table                        # export data/law/law_table.jsonl and print stats
```

The demo case: a first-time offender charged with theft (BNS s.303(2), maximum three years) in custody since
10 January 2025 became eligible for release on bond on 10 January 2026. On 24 October 2026 he has been inside 652
days. Rihai writes the application in under a second; the citation gate passes it; a legal-aid lawyer files it.

## The law table

| | rows | source |
|---|---|---|
| BNS 2023 | 468 | sections and titles from the IPC/BNS concordance (GSMS-B, CC-BY-4.0); maximum terms encoded from the Act |
| IPC 1860 | 181 | the sections that fill prison rosters; most undertrials today were charged before July 2024 |
| Special Acts | 106 | NDPS (by quantity class), Arms, POCSO, Maharashtra Prohibition, MCOCA, UAPA, PMLA, IT, SC/ST, Dowry, ITPA, PC Act, MV, Electricity, Wildlife, Explosives, Gambling |

Every row carries `verified` (false until a reviewer checks it against the official text on India Code) and the
India Code handle for the Act. The engine reports which unverified rows it relied on. `data/law/verified.jsonl`
overrides a row once it is checked. Rows with no stated ceiling (e.g. IPC 397 "not less than seven years") and
rows where life is one of several punishments are handled exactly as the statute reads: the first is
`NEEDS_REVIEW`, the second is excluded.

## Agent

[`rihai/agent/tools.py`](rihai/agent/tools.py) exposes six tools: `lookup_section`, `check_eligibility`,
`assess_roster`, `draft_application`, `check_citations`, `law_table_stats`. They are plain Python for any harness
and are wrapped for the Claude Agent SDK (AgentFoundry's scaffold) by `sdk_tools()`. The model has no tool that
can change a date, a maximum term or a verdict. The eligibility rule and the citation gate are also expressed as
AgentFoundry guardrails so the agent cannot declare a prisoner eligible unless the deterministic check passed.

## Pilot

Pune. Yerawada Central Prison holds about 7,000 inmates; ILS Law College, Symbiosis Law School and DES Law College
run prison legal-aid clinics; the Pune DLSA secretary prepares the UTRC list. The pilot runs the clinics' anonymised
case files through Rihai, the clinic verifies the calls, and the eligible applications go to the DLSA through
Legal Aid Defence Counsel. Outreach drafts are in [`docs/outreach/`](docs/outreach/).

## What is not done yet

- Hindi and Marathi application templates (English is done; references stay in English).
- Verification of the law table against India Code row by row (the verification script is `scripts/verify.py`, pending).
- IPC s.392 is encoded at its highway-at-night maximum (14 years) pending a split row for the plain offence (10 years).
- OCR of scanned jail registers (Annexure A/B formats) into the roster CSV.

## Licence and attribution

MIT. Section titles and the IPC/BNS mapping: *IPC-BNS-CrPC-BNSS-IEA-BSA Respective Old & New Sections Mapping*
(GSMS-B), CC-BY-4.0, see `NOTICE`. Statutes are public domain. Nothing here is legal advice; every draft is for
review by counsel before filing.
