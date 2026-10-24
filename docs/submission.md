# Submission draft: Code for a Billion (Code for India), Bharat Agentic-AI Hackathon 2026

Deadline 15 November 2026. The submission is a GitHub issue on `karlmehta/code-for-a-billion`, filed through the
"Project Submission" form. The fields below are the form's fields, in its order, so each block can be pasted into
its box on the day. Fill every `[...]` with a real value or delete the line.

How it is scored (JUDGING.md): four criteria, 25 points each. Size of the problem and severity of the problem
are answered in one box ("Scale & severity", 50%). Proven impact is its own box (25%) and breaks ties, so it is
written last from the outreach log, with nothing estimated. The README lists prizes of $10,000 / $5,000 / $2,500
overall (not per track); the website says otherwise, which was raised with the organisers on [date].

---

## Title

`[Submission] Rihai: Section 479 BNSS release eligibility for undertrial prisoners`

## Team / Project name

Rihai (रिहाई)

## Team members (names + GitHub handles)

Sainath Gaikwad (@SainathGaikwad), build. Pushkar [surname], field pilot, Pune (no GitHub handle).

## Problem statement

Three in four people in Indian prisons have not been convicted of anything. Section 479 of the Bharatiya Nagarik
Suraksha Sanhita, 2023 says an undertrial must be released on bail after serving half the maximum sentence for the
offence charged, a first-time offender on bond after one-third, and nobody may be held beyond the maximum term.
The Supreme Court has ordered every state to apply it proactively, yet in nine months only 334 people were
released under it nationally, because eligibility is checked by hand, jail by jail, once a quarter. Rihai is for the
jail superintendent, the District Legal Services Authority secretary and the prison legal-aid clinic who have to
find those people.

## What you built

Rihai takes a prison roster (charge sections, custody start date, prior convictions, pending cases) and computes
Section 479 eligibility deterministically against a law table of maximum sentences (757 rows: BNS 2023, IPC 1860,
17 special Acts). Every rule in the engine maps to a line of the section; unknown sections are refused, ambiguous
ones come back as "needs review" with the reason, life and death offences are excluded as the section requires.
For every eligible prisoner it drafts the application to the court and the memo for the DLSA/Undertrial Review
Committee, in English, Hindi or Marathi, from the assessment alone, so no figure in a draft can differ from what
the engine computed. A citation gate then checks every statutory reference in every draft (template or
model-written, English or Devanagari) against the law table; a bare "Section 999" blocks the draft.

The agent was built in AgentFoundry on the Claude Agent SDK scaffold. The model gets six tools (`lookup_section`,
`check_eligibility`, `assess_roster_tool`, `draft_application`, `check_citations`, `law_table_stats`) and nothing
else: built-in tools are off, a PreToolUse hook denies any other tool, a Stop hook runs the citation gate over the
model's final answer and sends it back if a section does not resolve. The model can narrate; it cannot compute a
date or a maximum term or invent a section. A second, optional prose layer lets any OpenAI-compatible model
rewrite a draft, and its text is used only if the gate passes and every date, day count and section is unchanged.
With no model configured, Rihai still works end to end. Rihai files nothing and decides nothing: legal-aid counsel
reviews, the court decides. 54 automated tests. MIT licence. No prisoner name anywhere in the code or data.

Impact area on the hackathon site: Timely Justice / Legal Backlog.

## GitHub repository URL

https://github.com/SainathGaikwad/rihai

## Demo URL (live app or video)

https://rihai-pune.streamlit.app  [and the video link, under 3 minutes]

## Scale & severity of the problem  (judged, 50%)

Scale. India's prisons held 5,30,333 people on 31 December 2023, 73.5% of them undertrials, in 1,332 prisons
built for 4,39,119, an occupancy of 120.8% (NCRB, Prison Statistics India 2023). NALSA's Undertrial Review
Committee report for July to September 2025 counts 5,34,993 prisoners. Section 479 applies to every one of the
roughly 3.9 lakh undertrials; the share that has already crossed the one-third or one-half threshold is not
published anywhere, which is itself the problem: nobody computes it. Maharashtra alone holds [n] prisoners in
[n] jails at [n]% occupancy; Yerawada Central Prison, Pune, where the pilot runs, holds about 7,000 against a
capacity of about 2,400 [verify from the Maharashtra Prisons Department].

Severity. An undertrial who has crossed the threshold is, from that day, in prison without any legal basis for it:
the section says "shall be released". The person loses income, the family often loses its only earner, bail that
could have been given on a personal bond is never applied for, and the state pays to hold them: the sanctioned
prison budget of all states and union territories was ₹10,035.6 crore for 2023-24 (NCRB), about ₹1.9 lakh per
inmate-year. The Supreme Court directed every state to apply Section 479 proactively (*In Re: Inhuman Conditions
in 1382 Prisons*, W.P.(C) 406/2013, orders of 23 August and 22 October 2024). The result between July 2024 and
April 2025: 951 undertrials identified as eligible and 334 released in the whole country (Rajya Sabha, 3 April
2025); in the quarter July to September 2025, 591 identified and 393 released (NALSA UTRC report). Against a
population of 3.9 lakh undertrials, the section is reaching a few hundred people a quarter. The bottleneck is not
the courts; it is the list. The jail compiles it by hand, the DLSA checks it by hand, the Undertrial Review
Committee meets once a quarter, and the arithmetic (a date, a fraction, a maximum sentence) is never run
continuously across 1,332 prisons.

## Deployment & impact data  (judged, 25%; ties are broken on this)

Write only what happened. A line with no real number is deleted, not estimated.

- Organisations met, with dates: [Prayas (TISS) Pune; Pune DLSA; ILS Law College legal-aid clinic; Symbiosis Law
  School clinic; DES Law College clinic; CHRI; Project 39A]
- Anonymised case files run through Rihai (identifiers only): [n]
- Found eligible by Rihai: [n]. Confirmed by the clinic's lawyer: [n]. Rihai wrong: [n], with the reason and the fix
- Applications drafted: [n]. Filed through the Legal Aid Defence Counsel: [n]. Orders received: [n], people
  released: [n]
- Time per case, clinic's own estimate before and measured with Rihai: [minutes]
- Law-table rows verified against India Code by law students: [n] of 757
- Letter of intent / MoU / written feedback: [who, date, attached to the issue]

## Track / category

Governance  (the dropdown has no justice track; Governance is the closest. "Other" is the alternative.)

## Contact email

gaikwadsainath738@gmail.com

## Confirmations

- [x] Built using AgentFoundry (AF), the official IDE
- [x] Our repository is public and includes a README with setup steps
- [x] The demo link works and is accessible to judges

---

Attach to the issue: a screenshot of the AgentFoundry project showing the agent and its tools; the demo video link;
any written feedback from a clinic or the DLSA (with names of staff only with their consent, never a prisoner's).

Sources for the numbers above: NCRB Prison Statistics India 2023 (ncrb.gov.in/uploads/files/PSI-2023.pdf; confirm
the page numbers from the PDF before posting); NALSA UTRC quarterly report Q3 2025; Rajya Sabha unstarred question
reply of 3 April 2025 on Section 479 BNSS; Supreme Court orders of 23.08.2024 and 22.10.2024 in W.P.(C) 406/2013.

*Draft prepared 24 October 2026. Rewrite the deployment section from the outreach log before posting.*
