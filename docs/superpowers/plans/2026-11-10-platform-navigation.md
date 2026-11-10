# Platform navigation V1 plan

User requested continuing autonomous development of a free intermediary navigation directory for 50 overseas short-drama platforms. No payment integration. Retain existing Django CMS and site scoping.

Design: make the homepage a searchable platform directory with website/app-store buttons, explicit destination labels, and internal tracked redirects. Official-link verification is independent from content licensing; navigating a platform does not require a fictitious distribution contract. Never assert a global top-50 ranking without a dated source and metric. Keep uncertain URLs unavailable rather than guessing.

- [ ] Research each official destination using first-party app listings and publisher sites; save evidence and checked date. Website takes precedence, official store fallback. Check lookalikes and regional restrictions.
- [ ] Add PlatformClick(platform, site, destination_kind, campaign, created_at); validate external destinations and status, reject cross-site/inactive/unknown targets. Add route /platform-go/id/.
- [ ] Replace homepage with local CSS platform directory, query/type filters, recommended cards, honest counts and no claimed paid unlocking. Keep published dramas below when present. No auto-loaded third-party logos.
- [ ] CMS shows destination verification inputs and platform performance by site/platform/campaign; use existing per-model permissions.
- [ ] Tests: official navigation without drama/source; cross-site isolation; invalid URL / unverified status; configured-target-only redirect; accurate counts/filtering; tracking; report permissions; no regression to 25 existing tests.
- [ ] Back up current code/data; apply additive migration and reviewed researched records; preserve user edits and all existing records; verify live homepage and redirects without following external destinations.

Execution inline per executing-plans; no Git repository, so use staged filesystem copy. Full tests use config.test_settings in-memory SQLite; verify migration on business MySQL after backup. Independent review before delivery.
