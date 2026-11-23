# OUR SCHOOL, OUR MEMORIES — SJK(C) Jenjarom, Building 4 Auditorium

Pixel top-down school RPG. Phaser 3 + Vite client, Cloudflare Workers + Durable Objects (or the local `ws` dev server) for multiplayer.

## Quick start
```bash
npm install
npm run dev:server     # local multiplayer server  ws://localhost:8787
npm run dev            # game                       http://localhost:5173
```
Open two browser tabs to see two players. The computer beside the rear exit opens **AUDITORIUMC**; the second monitor opens the **Media Player**
(which monitor is which is `COMPUTER_ASSIGNMENT` in `server/roomLogic.js` — NEEDS_REFERENCE, the photos don't say).

## Controls
| | |
|---|---|
| Desktop | WASD / arrows move · Shift run · E / Space interact (sit, stand, doors, computers) · seated: arrows hop to the next seat · G wave · M sound · Esc pause |
| Phone / tablet | left stick = move · RUN · A = interact (multi-touch: move + run + interact together) |

## What you can upload
AUDITORIUMC: **PDF** (best — in PowerPoint use *Save As → PDF*), PNG / JPG / WEBP. `.pptx` is **not** supported in the browser and says so.
Media Player: **MP3 / MP4**, up to 80 MB (real bytes are checked on the server, not just the extension).

## Scripts
`npm run assets` rebuild sprites/maps from `originals/` (needs Python + Pillow/numpy/scipy) · `npm run test:logic` server tests · `npm run test:ui` real-Chrome UI tests · `npm run test:e2e` Phaser e2e · `npm run build` · `npm run deploy:server` / `deploy:web`.

## Deploy
1. `npx wrangler r2 bucket create osom-media`, then edit `server/wrangler.toml` (`ALLOWED_ORIGINS`).
2. `npm run deploy:server` → note the `*.workers.dev` URL.
3. `VITE_WS_URL=wss://<that-host> npm run build && npm run deploy:web`.

## Verification status (honest)
| Area | Status |
|---|---|
| Asset pipeline (sprites, atlas, auditorium art, collision/seat alignment) | PASS (inspected visually + numerically) |
| Server room logic (30 tests: 25 logic + 5 real WebSocket/HTTP) | PASS |
| AUDITORIUMC / Media Player / game panels / HUD / touch controls in real Chrome (17 tests, see `build/ui-test-results.json`) | PASS |
| Phone / tablet | emulated only (Chrome device emulation + CDP multi-touch). Real Android: NOT TESTED |
| Auditorium scene LOGIC (walk, walls, seats, hop, stand, exit message, stage door to 2F and back, other players) with a *fake* Phaser against the real server (`npm run test:smoke`, 6 tests) | PASS — proves the logic, not rendering |
| Phaser rendering itself (`src/scenes`, `src/entities`, `src/main.js`) | **BLOCKED / NOT TESTED** — the npm registry was unreachable, so Phaser was never installed. Syntax and import wiring were checked statically only. Expect small first-run fixes. |
| Playwright e2e (`tests/e2e`) | BLOCKED / NOT TESTED |
| Cloudflare Worker / Durable Object / R2 deploy | NOT TESTED, not deployed |
| Real 20-player load | NOT TESTED |

## Honest content notes
- Photos are perspective views; the map is redrawn top-down. Anything not visible in the photos is **NEEDS_REFERENCE**: 2F interior, stairwell, campus map and Buildings 1–3 (the exit shows a message), exact booth door.
- Male sit / run / interact animations and all right-facing frames are generated (mirrored) from the supplied art; see `ASSETS.md`.
- The "Guide" NPC and its lines are my own placeholder, not from the spec.


## Publish on GitHub Pages

This repository includes `.github/workflows/deploy-pages.yml`. To publish:

1. Create a GitHub repository and upload/push **the contents of this project folder** (so `index.html`, `package.json`, `src/`, and `.github/` are at the repository root).
2. In GitHub, open **Settings → Pages**.
3. Under **Build and deployment**, choose **GitHub Actions** as the source.
4. Push to the `main` branch, or run **Actions → Deploy game to GitHub Pages → Run workflow**.
5. Wait for the workflow to finish. GitHub will show the published URL under **Settings → Pages**.

The Vite build uses relative asset paths, so it supports a normal project URL such as `https://YOUR-NAME.github.io/REPOSITORY/`.

### Important: what works on GitHub Pages

GitHub Pages is static hosting. The game client can be hosted there, but GitHub Pages does **not** run the Node/Cloudflare server.

- The game can start in offline mode; walking around and local client-side features can work.
- Online multiplayer, shared auditorium state, server-backed media uploads, and synchronized presentation/media require the separate Cloudflare Worker + Durable Objects + R2 backend.
- To enable that backend, deploy `server/worker.js` to Cloudflare as described in the Cloudflare section below, then add a GitHub Actions repository secret named `VITE_WS_URL` whose value is the Worker WebSocket origin, for example `wss://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev`. Do not include `/ws` at the end.
- Without that secret, the published game intentionally stays offline instead of repeatedly trying to connect to the GitHub Pages website.

### Cloudflare backend (optional, for online features)

1. Create/configure the R2 bucket and Worker bindings using `server/wrangler.toml` (the provided file may need to be renamed from `server/wrangler.toml.txt` to `server/wrangler.toml` and reviewed).
2. Deploy the Worker with Wrangler.
3. In GitHub, open **Settings → Secrets and variables → Actions → New repository secret**.
4. Name it `VITE_WS_URL` and enter the Worker origin, e.g. `wss://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev`.
5. Push a new commit to trigger a rebuild with the backend URL.

Never put private API keys or Cloudflare credentials in frontend source code.
