# Short drama operations implementation plan

> For agentic workers: execute inline using superpowers:executing-plans. User delegated implementation decisions and asked for completion.

Goal: upgrade existing Django/MySQL directory into a usable multi-site editorial CMS.
Architecture: retain server-rendered Django, existing records and admin; add operations models and staff-only CMS. Publications associate an existing drama with one site and original editorial copy. Site resolution is exact-domain based with localhost pointing to a default site. No scraping or generated factual claims.
Tech stack: Django 5.2, MySQL 8, local CSS/JS; SQLite isolated tests.

Design decisions: evolving existing models is smaller and safer than replacing Django with a separate frontend/API. Separate deployments would duplicate administration and do not fit centralized management. User explicitly delegated these choices. Stage in a file copy because source has no Git repository; preserve code and application data before applying additive migrations.

Global constraints: existing 50 platforms retained; unknown domains never inherit another site's content; unpublished/unlicensed/expired sources cannot reach public pages or redirects; generated SEO stays draft until reviewed; no external AI provider or invented synopsis; CMS requires staff plus model permissions; CSRF for writes; no destructive database reset. Ads are structured banner/text placements rather than executable pasted scripts.

Review focus: unknown domains and port parsing; cross-site detail/redirect leakage; revoked/expired evidence; unauthorized bulk operations and bad CSV; safe tracking/HTML and concurrent updates.

- [ ] 1. Model foundation: operations/models.py (Site, ContentSource, Publication); additive source/site/event relations in existing apps. Seed default site and associate existing content as drafts. Test two sites, license validity and duplicate publications.
- [ ] 2. Public delivery: operations/middleware.py and services.py resolve site, filter publication visibility, render canonical/JSON-LD, scoped sitemap and outbound links. Test unknown host, unreviewed/expired/foreign-site links, XML and structured data.
- [ ] 3. Staff CMS: operations/forms.py, views.py, urls.py and templates/operations; dashboard, searchable paginated CRUD, bulk SEO/publish/unpublish, CSV import/export, publication validation. Test anonymous/nonstaff/model permissions, CSRF, invalid CSV atomicity, originality and license gate.
- [ ] 4. Ads and analytics: site-scoped banner placements, safe click redirects, successful public HTML page tracking, charts and grouped reports by site/page/drama/link/campaign. Test tracking exclusion and site scoping, ad scheduling and target validation.
- [ ] 5. Verify: run full Django tests, system checks, migration drift, migrations on staging SQLite then MySQL after code/data backup; retain existing platforms; HTTP smoke tests for home/login/CMS protection. Document operating instructions and actual limitations. Fresh review before delivery.

Verification: python -B manage.py test --settings=config.test_settings; python -B manage.py check; python -B manage.py makemigrations --check --dry-run. CMS auth smoke via isolated Django test client, public HTTP on running server.
