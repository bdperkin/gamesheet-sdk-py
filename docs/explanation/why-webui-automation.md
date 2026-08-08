# Why the SDK automates the WebUI

The single most consequential design choice in `gamesheet-sdk-py` is that it does not call a GameSheet API — it drives the GameSheet web interface from the
outside, like a very patient and very fast user would. This page explains why, what that costs, and the assumptions that follow from it.

## 1. The starting point: there is no public API

GameSheet Inc. does not publish a public REST or GraphQL surface for the operations this SDK targets. Their internal application talks to internal endpoints,
but those endpoints are not documented, are not versioned for third parties, and come with no compatibility promise. Treating them as a _de facto_ API —
sniffing requests in browser devtools and replaying them — is sometimes possible, but it is no more stable than driving the UI and it is much less honest about
what's happening.

So the choice is not "WebUI automation vs. a clean API." The choice is "WebUI automation vs. don't ship at all."

## 2. What we gain

Driving the WebUI is enough to cover the routine tasks the SDK exposes: the same task a human can do in a browser, the SDK can script. That is exactly the value
proposition — automate the routine work that GameSheet has built a UI for and nothing more.

The library is _also_ honest about what it is. There is no pretense of a stable contract; the README and the {doc}`docs landing <../index>` both say so plainly.
Users come in with their eyes open.

## 3. What it costs

WebUI automation has three structural costs that no engineering effort can fully eliminate:

- **Fragility.** Anything that changes the DOM — a new heading, a moved button, a reworked form — can break the automation without warning. GameSheet has no
  obligation to keep their UI stable for outside consumers, and they shouldn't have to.
- **Speed.** A browser is a heavy way to perform what is logically a few HTTP requests. Even with headless Chromium and aggressive caching, per-operation
  latency is dominated by browser startup and page rendering, not by the work itself.
- **Resource footprint.** Playwright's Chromium binary is roughly 150 MB on disk and noticeable RAM at runtime. That's the floor for anything this SDK does that
  needs a real browser.

The {doc}`README disclaimer <../index>` ("may break without warning") follows directly from the first cost. The Playwright install instructions in the
{doc}`Getting started tutorial <../tutorials/getting-started>` and the browser-cache step in
{doc}`the GitHub Actions how-to <../how-to/install-in-github-actions>` both exist to manage the third.

## 4. The HTTP-first, browser-only-when-required strategy

A pure browser-automation library would pay the full cost above for _every_ operation. The browser is only needed when JavaScript runs between you and the
result you want — dynamically rendered content, single-page-app routing, anti-bot challenges that need a real engine.

So the SDK is structured to try the cheap path first:

1. `requests` for raw HTTP where the server cooperates.
2. `playwright` driving headless Chromium only when steps 1–2 are not enough.

The intent is that workflows fall through to Playwright reluctantly, not eagerly. That keeps the SDK usable in lightweight contexts (CI runners, scripts that
don't want a Chromium dependency installed) for the operations where it is feasible.

## 5. What this means for you, the user

A few practical implications drop out of this design:

- **Always pin a version in production.** UI changes can land at any time. A pinned `gamesheet-sdk-py==X.Y.Z` lets your automation continue to work against a
  known-good DOM until you are ready to test against a newer release.
- **Have a fallback plan.** When the WebUI changes and the SDK breaks, your automation breaks too. That window may be hours or days. For anything that genuinely
  cannot tolerate that, an external automation layer (people doing it manually) is your only safe fallback.
- **Don't rely on it for adversarial workloads.** WebUI automation cannot reliably outrun a vendor who decides to push back on automation. The SDK exists for
  _routine_ tasks against accounts you control, as the {doc}`README terms <../index>` make explicit.

## 6. Alternatives we are not pursuing

- **Reverse-engineering a private API.** Strictly worse than UI automation: same fragility, plus the discomfort of inviting a vendor conversation about the
  boundary between observed traffic and legitimate use. UI automation is at least transparent about what it is doing.
- **Lobbying GameSheet to publish an API.** Not in this project's scope. If they ever do, this SDK should wrap _that_ and the WebUI layer should be deprecated.
- **A "headed" desktop-driver mode.** Adds operational complexity for no behavioral gain over headless Chromium.

## 7. Further reading

- {doc}`diataxis` — why these docs are organized the way they are.
- {doc}`../reference/index` — what the SDK actually exposes today.
- {doc}`../how-to/index` — recipes for using the SDK in specific contexts.
