"""Publish the next due AdalatIQ carousel to Instagram (run by GitHub Actions).

MODE=check    -> verify the token reaches the Instagram account; posts nothing.
MODE=publish  -> publish the earliest due folder in queue/ and move it to published/.

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


def api(method, path, **params):
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
        sys.exit(f"Instagram API error on {path.split('?')[0]}: {msg.get('message')} "
                 f"(code {msg.get('code')}, subcode {msg.get('error_subcode')})")


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


def wait_ready(container_id):
    for _ in range(30):
        status = api("GET", container_id, fields="status_code").get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            sys.exit(f"Instagram could not process media {container_id}: {status}")
        time.sleep(5)
    sys.exit(f"Timed out waiting for media {container_id}")


def publish(ig_id, folder):
    repo = os.environ["GITHUB_REPOSITORY"]
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    slides = sorted(folder.glob("slide-*.jpg"))
    if not 2 <= len(slides) <= 10:
        sys.exit(f"{folder.name} has {len(slides)} slides; a carousel needs 2-10")
    caption = (folder / "caption.txt").read_text(encoding="utf-8")
    base = f"https://raw.githubusercontent.com/{repo}/{sha}/queue/{urllib.parse.quote(folder.name)}"
    children = []
    for s in slides:
        c = api("POST", f"{ig_id}/media", image_url=f"{base}/{s.name}", is_carousel_item="true")["id"]
        wait_ready(c)
        children.append(c)
    carousel = api("POST", f"{ig_id}/media", media_type="CAROUSEL", children=",".join(children), caption=caption)["id"]
    wait_ready(carousel)
    media_id = api("POST", f"{ig_id}/media_publish", creation_id=carousel)["id"]
    link = api("GET", media_id, fields="permalink").get("permalink")
    target = DONE / folder.name
    shutil.move(str(folder), str(target))
    (target / "result.json").write_text(json.dumps(
        {"media_id": media_id, "permalink": link, "published_at": datetime.now(IST).isoformat()}, indent=2))
    print(f"Published {folder.name}: {link}")


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
    folder = due_folder(datetime.now(IST))
    if not folder:
        print("Nothing due right now.")
        return
    publish(ig_id, folder)


if __name__ == "__main__":
    QUEUE.mkdir(exist_ok=True)
    DONE.mkdir(exist_ok=True)
    main()
