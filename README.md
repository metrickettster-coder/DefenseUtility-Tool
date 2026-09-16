# DefenseUtility-Tool

Utilities for working against DoD acquisition rules, regulations, and clauses.

## Web app (`public/index.html`)

A single-file, client-side "Defense Contract & Operations Management Suite" covering
pre-award/strategy, admin & mods, hardware/ops, compliance & SCRM, data rights, and
closeout/audit calculators. Everything runs in the browser (no backend) and inputs are
persisted to `localStorage`, so it's suitable for static hosting or fully air-gapped use.
Open `public/index.html` directly in a browser to use it standalone.

### Deploying to Cloudflare Workers (free tier)

The repo is set up to deploy as a Worker serving static assets (`wrangler.toml` +
`src/worker.js`, which adds a few defensive response headers on top of the asset
response).

```bash
npm install       # pulls in wrangler as a dev dependency
npx wrangler dev   # serve locally at http://localhost:8787
npx wrangler deploy  # deploy to your Cloudflare account (requires `wrangler login` or
                      # CLOUDFLARE_API_TOKEN / CLOUDFLARE_ACCOUNT_ID env vars)
```

Or connect this GitHub repo in the Cloudflare dashboard under **Workers & Pages → Create
→ Workers → Import a repository** (Workers Builds) for auto-deploy on every push to `main`
— it detects `wrangler.toml` and runs `wrangler deploy` for you.

## Python CLI (`defutil`)

A command-line companion covering three things:

1. **Regulation/clause reference & search** — keyword/ID search across a curated set of
   FAR/DFARS clauses and NIST SP 800-171 control families.
2. **Document compliance gap-checking** — scan a document (SOW, SSP, contract text) for
   references to a baseline set of clauses/controls and report what's missing.
3. **Local system security posture scanning** — read-only, STIG-style checks against the
   local machine (SSH hardening, firewall/auditd status, world-writable files, empty
   passwords, patching). No remote scanning of other hosts; informational only.

### Install

```bash
pip install -e .
```

### Usage

```bash
# Search clauses/controls
defutil search "multifactor"
defutil search "cmmc" --source clauses

# Check a document against the default CUI/DFARS baseline
defutil check-doc path/to/sow.txt
defutil check-doc path/to/sow.txt --baseline my_baseline.json   # JSON array of clause/control IDs

# Run local system security posture checks
defutil scan-system

# Machine-readable output
defutil --json search "incident response"
```

`check-doc` and `scan-system` exit with status `2` if there are missing baseline items /
failed checks, `0` if everything is covered/passing, so they can be used in CI gates.

### Notes / limitations

- The bundled clause and NIST SP 800-171 control datasets (`defenseutility/data/*.json`)
  are illustrative, curated subsets — **not** a complete or authoritative restatement of
  FAR/DFARS or NIST SP 800-171. Verify against acquisition.gov, the DFARS PGI, and
  NIST SP 800-171 Rev. 2/3 before relying on this for actual compliance determinations.
- `check-doc` matching is keyword/ID-based (not semantic), so it can both over- and
  under-match — treat results as a starting point for review, not a final determination.
- `scan-system` only inspects the local host it runs on and never modifies configuration;
  checks that require elevated privileges (e.g. reading `/etc/shadow`) report `UNKNOWN`
  rather than failing when permission is denied.

### Tests

```bash
python -m pytest
```
