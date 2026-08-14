# Contributing

Thanks for wanting to add something. Please read this first — the rules here are unusual, and there's a
reason for them.

## The honest limitation

I can't verify your recipe. I don't have your device, your firmware version, or your network. Every
recipe in `docs/` was run on hardware I own, and that's the only thing that makes it trustworthy.

So this repository keeps two kinds of content, clearly separated:

**Verified** — `docs/`. Tested by me on real hardware. Nothing lands here that I haven't run myself.

**Community** — `docs/community/`. Contributed recipes, marked as not verified by the maintainer. Useful,
often correct, but nobody double-checked them.

Both are welcome. Please don't be offended if your recipe goes to the second folder — that's not a
judgement of quality, it's a statement of fact about who tested what.

## What a recipe needs

Whatever you send, include enough for a reader to tell whether it applies to them:

- **Device model** and where you bought it, if the same model ships under different names.
- **Firmware or protocol version.** For Tuya that's the protocol (3.1 / 3.3 / 3.4 / 3.5). For Zigbee, the
  Zigbee2MQTT model id.
- **What integration you used** and its version.
- **How you know it works.** This is the important one: a log fragment, a screenshot, the output of the
  command you ran. "It works for me" isn't evidence.
- **What didn't work**, if you found dead ends. Those are often more useful than the solution.

A pull request without evidence will be declined. Not because I doubt you — because I have no way to
check, and publishing unverifiable claims as if they were verified is worse than publishing nothing.

## Never include secrets

Before you open a PR, check your diff and your screenshots for:

- Tuya `local_key` — this is a full control credential for the device
- device IDs, `uid`, `terminal_id`, cloud project keys
- MAC addresses, real IP ranges, Wi-Fi names
- e-mail addresses, account names, one-time codes
- coordinates (Tuya diagnostics include your home's latitude and longitude)

Use placeholders. The existing articles use `192.168.10.0/24` for a home network and
`192.168.30.0/24` for IoT — please keep that convention.

If you notice a secret of mine that slipped through, please report it privately rather than opening a
public issue.

## Both languages, or just one

Articles live in `docs/en/` and `docs/ru/`. A recipe in one language is fine — a partial contribution
beats no contribution. Say in the PR which language you wrote, and don't machine-translate the other
half; a bad translation is worse than a missing one.

## Style

Nothing fancy. What matters:

- Plain sentences. This is documentation, not a blog post.
- Say what failed and why, not just the final answer. The dead ends are the value here.
- Wrap lines at about 100 characters so diffs stay readable.
- File names are numbered: `006-your-topic.md`, next free number.

## What CI checks

The workflow builds the site and catches broken links and YAML errors. It cannot check whether your
recipe is correct — only hardware can do that.
