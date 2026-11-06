"""Google Cloud Text-to-Speech helper (runs in GitHub Actions, where Google is reachable).

  python3 scripts/google_tts.py samples            -> voice-samples/<voice>.mp3 for every en-IN FEMALE voice
  python3 scripts/google_tts.py say VOICE "text" out.mp3

Needs env GOOGLE_TTS_API_KEY (GitHub secret). Standard library only.
"""
import base64, json, os, sys, urllib.request
from pathlib import Path

KEY = os.environ.get("GOOGLE_TTS_API_KEY", "").strip()
API = "https://texttospeech.googleapis.com/v1"
SAMPLE = ("Can your brothers deny you a share in your joint family property? Here's what the law says. "
          "In a Hindu joint family, a daughter is a coparcener by birth, just like a son. "
          "Know your rights. Follow AdalatIQ for more.")


def call(path, body=None):
    req = urllib.request.Request(f"{API}/{path}{'&' if '?' in path else '?'}key={KEY}",
                                 data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Google TTS error {e.code}: {json.load(e).get('error', {}).get('message')}")


def say(voice, text, out, rate=1.0, pitch=0.0):
    body = {"input": {"text": text}, "voice": {"languageCode": voice[:5], "name": voice},
            "audioConfig": {"audioEncoding": "MP3", "sampleRateHertz": 48000}}
    if "Chirp" not in voice:                       # Chirp voices don't accept rate/pitch tweaks
        body["audioConfig"].update(speakingRate=rate, pitch=pitch)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_bytes(base64.b64decode(call("text:synthesize", body)["audioContent"]))


def samples():
    voices = [v for v in call("voices?languageCode=en-IN")["voices"] if v.get("ssmlGender") == "FEMALE"]
    print(f"{len(voices)} en-IN female voices")
    for v in sorted(voices, key=lambda v: v["name"]):
        say(v["name"], SAMPLE, f"voice-samples/{v['name']}.mp3")
        print("sample:", v["name"])


if __name__ == "__main__":
    if not KEY:
        sys.exit("GOOGLE_TTS_API_KEY secret is missing.")
    if sys.argv[1:2] == ["samples"]:
        samples()
    elif sys.argv[1:2] == ["say"]:
        say(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        sys.exit(__doc__)
