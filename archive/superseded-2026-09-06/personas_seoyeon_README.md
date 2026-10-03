# Seo-yeon

An AI persona built for Instagram and Fanvue. Photorealism and the impression
of a real person are the two rules everything else serves.

**Start with [`CLAUDE.md`](CLAUDE.md)** — the operative layer, loaded
automatically, ~300 lines. The full reasoning behind every rule in it is
[`wiki/domains/pipeline/playbook.md`](wiki/domains/pipeline/playbook.md), read
on demand rather than loaded.

## Run it

```powershell
python console.py            # localhost control panel: generate + publish desk
python outside.py --week2 --all
python outside.py --plates --all
python reel_build.py --from-posts --out clips/reel.mp4
python audit.py              # before spending anything
python drift_gate.py --in content\week2
```

Key in `kie_key.txt`. Provider is Kie.ai; `fal_api.py` is kept unused in case
that changes back.

## Where things are

| | |
|---|---|
| [`wiki/index.md`](wiki/index.md) | catalog of every document |
| [`wiki/overview.md`](wiki/overview.md) | the domain map |
| [`wiki/log.md`](wiki/log.md) | append-only decision log |
| `content/` | generated images, by pool |
| `master/`, `locations/` | identity references and room plates |
| `_trash/` | spent one-shot scripts |
