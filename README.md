# Rihai (रिहाई)

**Release eligibility of undertrial prisoners under Section 479 of the Bharatiya Nagarik Suraksha Sanhita, 2023.**
The code decides; the model narrates.

Bharat Agentic-AI Hackathon 2026 (Code for India), impact area: Timely Justice / Legal Backlog.
Live: **https://rihai-pune.streamlit.app** (template mode, sample roster built in, no names anywhere).
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
   DLSA/UTRC memo, in English, Hindi or Marathi. In template mode no model is involved, so the draft cannot contain
   a figure the engine did not compute. A model (Muse Spark, Nemotron, Claude) may rewrite the prose.
3. **A citation gate.** Every statutory reference in any draft, model-written or not, English or Devanagari, must
   resolve to the law table or to the short list of procedural provisions a s.479 application may cite. A bare
   "Section 999" with no Act named, or "Section 999 of the Sanhita", blocks the draft. Same idea as SEEN's claim
   checker, pointed at sections instead of numbers.

Nothing in Rihai files anything, sends anything or decides anything. Legal-aid counsel reviews; the court decides.

## How it fits together

```
 roster CSV / one case                      law table (755 rows, verified flags)
        |                                              |
        v                                              v
 rihai/eligibility/s479.py  <----- lookup -----  rihai/law/table.py
   (the rule as code; ELIGIBLE / NOT_YET / MUST_RELEASE_MAX_TERM /
    EXCLUDED_* / NEEDS_REVIEW / UNKNOWN_SECTION, with reasons)
        |
        v
 rihai/agent/draft.py (+ draft_i18n.py)     template application + DLSA memo, en / hi / mr
        |
        v
 rihai/gate/citations.py                    every section in the text must resolve; else BLOCKED
        |
        +---- optional: rihai/agent/llm.py   a model rewrites the prose; accepted only if the gate
        |                                    passes and every date, day count and section is unchanged
        v
 Streamlit app  |  python -m rihai.agent.run  |  Claude Agent SDK harness (six tools, two guardrail hooks)
```

The model never sees a tool that can compute a date or a maximum term. It can look up, assess, draft and check.

## Try it

```bash
pip install -r requirements.txt
python -m pytest -q                              # 53 tests: rule, gate, three languages, model contract, guardrails, app
streamlit run rihai/app/streamlit_app.py         # one prisoner / roster CSV / law table
python -m rihai.agent.run --charges "BNS 303(2)" --custody 2025-01-10 --first-time --lang mr
python -m rihai.agent.run --roster data/samples/roster_sample.csv --out out/   # results.csv, memos, applications
python -m rihai.agent.run --agent --charges "BNS 303(2)" --custody 2025-01-10 --first-time   # Claude Agent SDK
python -m rihai.law.table                        # export data/law/law_table.jsonl and print stats
```

Deploy notes (Streamlit Community Cloud, laptop, CLI) are in [`docs/deploy.md`](docs/deploy.md).

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
`assess_roster_tool`, `draft_application`, `check_citations`, `law_table_stats`. They are plain Python for any
harness and are wrapped for the Claude Agent SDK (AgentFoundry's Claude scaffold) by `sdk_tools()`.

[`rihai/agent/run.py`](rihai/agent/run.py) is the harness. In `--agent` mode the model gets those six tools and
nothing else: built-in tools are off, a `PreToolUse` hook denies any other tool by name, a `Stop` hook runs the
citation gate over the model's final answer and sends it back if a section does not resolve, and the runner gates
the result once more. The system prompt says the same things, but the hooks are what enforce them.

[`rihai/agent/llm.py`](rihai/agent/llm.py) is the prose layer for any OpenAI-compatible endpoint (Nebius, Meta's
Llama API, a local vLLM). Three environment variables or Streamlit secrets configure it; with none set, Rihai runs in
template mode. A rewrite is accepted only if the gate passes, it cites no fewer provisions than the template, and
every anchor fact (custody date, assessment date, eligibility date, days served, controlling section) is present
verbatim. Otherwise the template is returned with the reason.

## Pilot

Pune. Yerawada Central Prison holds about 7,000 inmates; ILS Law College, Symbiosis Law School and DES Law College
run prison legal-aid clinics; the Pune DLSA secretary prepares the UTRC list. The pilot runs the clinics' anonymised
case files through Rihai, the clinic verifies the calls, and the eligible applications go to the DLSA through
Legal Aid Defence Counsel. Outreach drafts are in [`docs/outreach/`](docs/outreach/).

## What is not done yet

- Law-clinic review of the Hindi and Marathi legal terms (templates are done; each draft carries a review line until then).
- Verification of the law table against India Code row by row: `python scripts/verify.py` records each checked row.
- IPC s.392 is encoded at its highway-at-night maximum (14 years) pending a split row for the plain offence (10 years).
- OCR of scanned jail registers (Annexure A/B formats) into the roster CSV.

## Licence and attribution

MIT. Section titles and the IPC/BNS mapping: *IPC-BNS-CrPC-BNSS-IEA-BSA Respective Old & New Sections Mapping*
(GSMS-B), CC-BY-4.0, see `NOTICE`. Statutes are public domain. Nothing here is legal advice; every draft is for
review by counsel before filing.
