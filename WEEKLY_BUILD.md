# Weekly build playbook

Claude follows this every Sunday to prepare next week's 14 Instagram carousels for AdalatIQ.
The output is a pull request. **Nothing is posted until the owner merges it.**

## The non-negotiables

1. **Government sources only.** Every fact must come from an official source:
   indiacode.nic.in, egazette.gov.in, legislative.gov.in, a ministry or department site (`*.gov.in`, `*.nic.in`),
   nalsa.gov.in or a State/District Legal Services Authority, sci.gov.in or a High Court site, pib.gov.in,
   a regulator (RBI, SEBI, IRDAI, TRAI…) or an official government handbook/PDF.
   Blogs, law-firm sites, news sites, coaching sites and Wikipedia may help you *find* a source, but are never the source.
2. **No guessing.** If a claim can't be matched to the official text, cut it. If the post can't stand without it, drop the topic.
3. **Current law.** Criminal law is now BNS / BNSS / BSA (in force from 1 July 2024), not IPC / CrPC / Evidence Act.
   Check every Act you cite for later amendments.
4. **State-dependent rules** (income limits, rent laws, minimum wage, stamp duty…): say "depends on your State"
   rather than quoting one State's number as if it applied everywhere.
5. **Every answer slide carries a reference** (Act + section, or the official body). The last slide lists sources.
6. **Every caption** ends with the disclaimer and the link — see the template below.

## Steps

### 1. Set up
```
git clone https://github.com/kartikeyakotnala/Adalatiq-insta.git && cd Adalatiq-insta
pip install playwright --break-system-packages   # only if `import playwright` fails
git checkout -b week-<Monday's date YYYY-MM-DD>
```
Read `topics.md` and list what's already in `queue/` and `published/` so nothing repeats.

### 2. Pick 14 topics and languages
Take the first 14 unticked topics in `topics.md` (skip any that clearly need State-specific numbers you can't verify
for all States). Language mix per week: **4 English, 2 each Hindi (hi), Marathi (mr), Tamil (ta), Telugu (te), Kannada (kn)**.
Give each a 3-digit post id continuing from the highest id used so far.

### 3. Research (one topic at a time)
For each topic: find the governing Act/section or official scheme on an official site, read the actual text,
and write down each claim with its source URL and section. Keep a research note per post in the PR description.

### 4. Write the post (`post.json`)
Write it in the target language from the start — natural everyday language, not a word-for-word translation.
Use the official name of the Act in that language if one exists; otherwise keep the English name.
Section numbers and helpline numbers stay as digits.

```json
{
  "id": "003-landlord-deposit",
  "lang": "en",
  "hook": "The common worry, as people say it.",
  "hook_q": "The question, short. Ends with ?",
  "slides": [
    {"title": "Short answer headline.", "body": "One or two plain sentences.", "ref": "Act Year · Sec N"},
    {"title": "A list slide.", "list": ["Point", "Point", "Point"], "ref": "Act Year · Sec N(a)"}
  ],
  "sources": ["Full Act name, Year – Section N", "Official body (site.gov.in)"],
  "caption": "…"
}
```
Rules: 3–7 answer slides; titles under ~8 words; bodies under ~35 words; lists 3–5 items.
Caption template (in the post's language):
```
<hook line> 👇

<3–6 short points, one per line>

Source: <Act, Section>

<disclaimer: AI-assisted, for general awareness only, not legal advice, speak to a lawyer>

<Stuck with a legal problem? Ask AdalatIQ free → adalatiq.com>

<5–7 hashtags, ending #AdalatIQ>
```

### 5. Independent fact-check (required)
Spawn a separate agent that has **not** seen your drafting. Give it only the `post.json` files and the list of
official source URLs. Ask it to open each source and mark every claim on every slide and in every caption as
VERIFIED (quote the matching official text), WRONG, or UNSUPPORTED. For non-English posts it must also check that the
meaning matches the law. Fix or cut anything not VERIFIED, then re-check those claims. Drop a post that still fails.

### 6. Schedule and render
Two posts a day, Monday to Sunday of the coming week, at 0930 and 1930 IST. Alternate languages so the same
language isn't posted twice in a row. Folder name: `queue/YYYY-MM-DD-HHMM-<id>-<lang>/post.json`.
```
python3 scripts/render.py queue/<each new folder>
```
Look at every rendered slide (build a contact sheet and view it). Fix overflow, cut-off words or broken script,
and re-render.

### 7. Open the pull request
Tick the used topics in `topics.md` with their ids and languages. Commit and push the branch, then open a PR titled
`Instagram posts: week of <Monday's date>`. In the description list each post (date, time, language, question),
its sources, and the fact-check result. Embed the first slide of each post using its raw URL so the owner can review
on their phone, e.g. `![](https://raw.githubusercontent.com/kartikeyakotnala/Adalatiq-insta/<branch>/queue/<folder>/slide-01.jpg)`.
If fewer than 14 posts passed, say how many and why.

Merging the PR approves the week. The `Publish to Instagram` workflow then posts each one at its time.
