"""Publish the next due AdalatIQ carousel to Instagram (run by GitHub Actions).

MODE=check    -> verify the token reaches the Instagram account; posts nothing.
MODE=batch    -> publish the next COUNT folders in queue/ (in name order) right now.
MODE=publish  -> publish the earliest folder whose time has passed (one post).

A queue folder is named  YYYY-MM-DD-HHMM-<post-id>  (time in IST) and holds
slide-01.jpg ... slide-NN.jpg and caption.txt. A folder is "due" once its time has passed.
Only one post is published per run.

Needs env: IG_TOKEN (GitHub secret), GITHUB_REPOSITORY and GITHUB_SHA (set by Actions).
Uses only the Python standard library.
"""
import json, os, shutil, subprocess, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE, DONE = ROOT / "queue", ROOT / "published"
GRAPH = "https://graph.facebook.com/" + os.environ.get("GRAPH_VERSION", "v24.0")
IST = timezone(timedelta(hours=5, minutes=30))
TOKEN = os.environ.get("IG_TOKEN", "").strip()


class ApiError(RuntimeError):
    pass


def api(method, path, soft=False, **params):
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        req = urllib.request.Request(f"{GRAPH}/{path}?{data.decode()}")
    else:
        req = urllib.request.Request(f"{GRAPH}/{path}", data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as err:
        try:
            msg = json.load(err).get("error", {})
        except Exception:
            msg = {"message": f"HTTP {err.code}"}
        text = (f"Instagram API error on {path.split('?')[0]}: {msg.get('message')} "
                f"(code {msg.get('code')}, subcode {msg.get('error_subcode')})")
        if soft:
            raise ApiError(text)
        sys.exit(text)


def find_account():
    if os.environ.get("IG_USER_ID"):
        info = api("GET", os.environ["IG_USER_ID"], fields="id,username")
        return info["id"], info.get("username")
    pages = api("GET", "me/accounts", fields="name,instagram_business_account{id,username}").get("data", [])
    for p in pages:
        ig = p.get("instagram_business_account")
        if ig:
            return ig["id"], ig.get("username")
    names = ", ".join(p.get("name", "?") for p in pages) or "none"
    perms = api("GET", "me/permissions").get("data", [])
    granted = ", ".join(p["permission"] for p in perms if p.get("status") == "granted") or "none"
    me = api("GET", "me", fields="id,name")
    sys.exit(f"No Instagram account found.\n  Token belongs to: {me.get('name')}\n"
             f"  Permissions granted: {granted}\n  Pages this token can see: {names}\n"
             "Fix: assign the Facebook Page and the Instagram account to the system user, "
             "or set IG_USER_ID.")


def due_folder(now):
    for f in sorted(p for p in QUEUE.iterdir() if p.is_dir()):
        try:
            when = datetime.strptime(f.name[:15], "%Y-%m-%d-%H%M").replace(tzinfo=IST)
        except ValueError:
            print(f"skipping {f.name}: name must start with YYYY-MM-DD-HHMM")
            continue
        if when <= now:
            return f
    return None


def topic_of(folder):
    """queue/2026-11-09-0930-015-landlord-deposit-en -> 015-landlord-deposit"""
    return folder.name[16:].rsplit("-", 1)[0]


def pick_batch(count):
    """Next `count` posts in queue order, always including every language of a question together."""
    queued = sorted(p for p in QUEUE.iterdir() if p.is_dir())
    topics, chosen = [], []
    for f in queued:
        t = topic_of(f)
        if t in topics:
            continue
        if len(chosen) >= count:
            break
        topics.append(t)
        group = [g for g in queued if topic_of(g) == t]
        group.sort(key=lambda g: (g.name.rsplit("-", 1)[1] != "en", g.name))   # English first, then Hindi
        chosen += group
    return chosen


def wait_ready(container_id, tries=30, soft=False):
    for _ in range(tries):
        status = api("GET", container_id, soft=soft, fields="status_code").get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            msg = f"Instagram could not process media {container_id}: {status}"
            if soft:
                raise ApiError(msg)
            sys.exit(msg)
        time.sleep(5)
    msg = f"Timed out waiting for media {container_id}"
    if soft:
        raise ApiError(msg)
    sys.exit(msg)


def publish_reel(ig_id, base, caption):
    """Post reel.mp4 as a Reel (also shown in the feed). Returns (media_id, permalink); raises ApiError on failure."""
    c = api("POST", f"{ig_id}/media", soft=True, media_type="REELS", video_url=f"{base}/reel.mp4",
            caption=caption, share_to_feed="true")["id"]
    wait_ready(c, tries=72, soft=True)          # videos take longer to process (up to ~6 min)
    media_id = api("POST", f"{ig_id}/media_publish", soft=True, creation_id=c)["id"]
    return media_id, api("GET", media_id, soft=True, fields="permalink").get("permalink")


def publish(ig_id, folder):
    repo = os.environ["GITHUB_REPOSITORY"]
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    slides = sorted(folder.glob("slide-*.jpg"))
    if not 1 <= len(slides) <= 10:
        sys.exit(f"{folder.name} has {len(slides)} slides; a post needs 1 (single image) or 2-10 (carousel)")
    caption = (folder / "caption.txt").read_text(encoding="utf-8")
    base = f"https://raw.githubusercontent.com/{repo}/{sha}/queue/{urllib.parse.quote(folder.name)}"
    if len(slides) == 1:                      # single-image post (e.g. a festival greeting)
        carousel = api("POST", f"{ig_id}/media", image_url=f"{base}/{slides[0].name}", caption=caption)["id"]
        wait_ready(carousel)
    else:
        children = []
        for s in slides:
            c = api("POST", f"{ig_id}/media", image_url=f"{base}/{s.name}", is_carousel_item="true")["id"]
            wait_ready(c)
            children.append(c)
        carousel = api("POST", f"{ig_id}/media", media_type="CAROUSEL", children=",".join(children), caption=caption)["id"]
        wait_ready(carousel)
    media_id = api("POST", f"{ig_id}/media_publish", creation_id=carousel)["id"]
    link = api("GET", media_id, fields="permalink").get("permalink")
    print(f"Published {folder.name}: {link}")
    result = {"media_id": media_id, "permalink": link, "published_at": datetime.now(IST).isoformat()}
    if (folder / "reel.mp4").exists() and os.environ.get("POST_REELS", "false").lower() == "true":
        try:
            reel_id, reel_link = publish_reel(ig_id, base, caption)
            result.update(reel_id=reel_id, reel_permalink=reel_link)
            print(f"Published reel {folder.name}: {reel_link}")
        except ApiError as err:            # the carousel is already live; don't fail the whole run
            result["reel_error"] = str(err)
            print(f"Reel not posted for {folder.name}: {err}")
    target = DONE / folder.name
    shutil.move(str(folder), str(target))
    (target / "result.json").write_text(json.dumps(result, indent=2))
    (target / "reel.mp4").unlink(missing_ok=True)   # keep the repository small; the Reel lives on Instagram


def main():
    if not TOKEN:
        sys.exit("IG_TOKEN secret is missing. Add it under Settings -> Secrets and variables -> Actions.")
    ig_id, username = find_account()
    mode = os.environ.get("MODE", "publish")
    if mode == "check":
        limit = api("GET", f"{ig_id}/content_publishing_limit", fields="quota_usage,config").get("data", [{}])[0]
        print(f"OK: token works for Instagram @{username} (account ID {ig_id}).")
        print(f"Posts published via API in the last 24h: {limit.get('quota_usage')} "
              f"(limit {limit.get('config', {}).get('quota_total')}).")
        queued = sorted(p.name for p in QUEUE.iterdir() if p.is_dir())
        print(f"Queued posts: {len(queued)}" + ("".join(f"\n  - {q}" for q in queued)))
        return
    if mode == "batch":
        count = int(os.environ.get("COUNT") or 4)
        folders = pick_batch(count)
        if not folders:
            print("The queue is empty. Nothing to post.")
            return
        for f in folders:
            publish(ig_id, f)
        left = len([p for p in QUEUE.iterdir() if p.is_dir()])
        print(f"Done: posted {len(folders)}. Still in queue: {left}.")
        return
    folder = due_folder(datetime.now(IST))
    if not folder:
        print("Nothing due right now.")
        return
    publish(ig_id, folder)


if __name__ == "__main__":
    QUEUE.mkdir(exist_ok=True)
    DONE.mkdir(exist_ok=True)
    main()
