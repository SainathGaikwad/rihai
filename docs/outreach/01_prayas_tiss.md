**To:** prayas@tiss.edu (Prayas, Field Action Project of the Tata Institute of Social Sciences, Mumbai) · Cc: prayas@tiss.ac.in
**Subject:** A tool to find Section 479 BNSS-eligible undertrials in Maharashtra's prisons, built by a software engineer in Pune

Dear Prayas team,

I am Sainath Gaikwad, a software engineer in Pune. I have built a small open-source tool, Rihai,
that takes a list of undertrial prisoners (charge sections, date of custody, prior convictions) and computes who is
eligible for release under Section 479 of the BNSS, then drafts the application and the DLSA note. The eligibility
arithmetic is deterministic code, not an AI guess; the AI part only writes prose, and every section it cites is
checked against a law table before anything is shown.

We built it because the numbers are stark: 5.3 lakh prisoners nationally, and in the whole of July to September
2025 only 591 undertrials were identified under Section 479 across the country (NALSA UTRC report). The arithmetic
is simple and nobody is running it continuously.

Prayas has worked inside Maharashtra's prisons on exactly this for longer than anyone. Would you be willing to run
30 to 50 anonymised case files through it (no names, only charge sections and dates) and tell us where it is wrong?
A 15-minute call would also help us understand how the UTRC list is actually prepared, and whom we should speak to
in Pune, where we are starting with the law-college legal-aid clinics and the DLSA.

You can try it in a browser at rihai-pune.streamlit.app (a sample roster is built in; no names anywhere). The code is at
github.com/SainathGaikwad/rihai. It is MIT-licensed; you keep it whatever comes of this.

Thank you for your time.

Sainath Gaikwad
Pune | gaikwadsainath738@gmail.com | [phone]
