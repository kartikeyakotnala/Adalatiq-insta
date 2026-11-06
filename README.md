# AdalatIQ Instagram

Automated legal-awareness carousels for AdalatIQ's Instagram.

**How it works**
1. Every Sunday, Claude researches 14 common legal questions (each posted in English and Hindi) from government sources only, has every claim
   fact-checked independently, and renders the slides. Fact-check reports are kept in `reports/`.
2. The week's posts are committed to `queue/` and you get a summary.
3. Posts go out when you ask: tell Claude "post today's AdalatIQ posts" in any chat, or run it yourself
   (Actions → Publish to Instagram → Run workflow → batch, 4). See POSTING.md.
   Each posted carousel moves from `queue/` to `published/` with a link to the live post.

**Folders**
- `queue/` – approved posts waiting for their time (`YYYY-MM-DD-HHMM-<id>-<lang>`, time in IST)
- `published/` – posts already live, each with `result.json` holding the Instagram link
- `topics.md` – the question bank; `WEEKLY_BUILD.md` – the rules Claude follows
- `scripts/render_explainer.py` – turns `post.json` into slides in the default explainer style (`scripts/render.py` is the older plain style); `scripts/publish.py` – posts via Instagram's official API

**Handy controls**
- Test the token without posting: Actions → Publish to Instagram → Run workflow → `check`.
- Skip a post: delete its folder from `queue/`.
- The token lives only in Settings → Secrets → `IG_TOKEN`. Never commit it.
