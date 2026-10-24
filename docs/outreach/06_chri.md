**To:** Prison Reforms Programme, Commonwealth Human Rights Initiative, New Delhi
**Subject:** An open-source Section 479 BNSS eligibility engine; would welcome your criticism

Dear CHRI team,

I am Sainath Gaikwad, a software engineer in Pune. I have built Rihai, an open-source tool that takes a prison
roster and computes Section 479 BNSS eligibility deterministically (the half and one-third thresholds, the
life/death exclusion, the multiple-cases bar in sub-section (2), the maximum-term proviso, the delay explanation),
then drafts the application for counsel. The AI writes prose only, and every statutory citation is checked against
a law table before the draft is shown.

CHRI's undertrial work is the reason the problem is on the national agenda. We would value two things: your view
on where the rule as we have encoded it is wrong or contested (we have put the whole encoding in one file with the
section text alongside), and any pointer to anonymised roster data in the UTRC Annexure format we could test on.

We are piloting in Pune with the law-college clinics and, we hope, the DLSA. It runs in a browser at rihai-pune.streamlit.app; the code is at
github.com/SainathGaikwad/rihai under the MIT licence.

Thank you,

Sainath Gaikwad
Pune | gaikwadsainath738@gmail.com
