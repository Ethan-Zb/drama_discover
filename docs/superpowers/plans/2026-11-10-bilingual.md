# Bilingual public website

User requested Chinese/English switching and previously delegated implementation choices. Retain Django and current URLs. Use LocaleMiddleware, built-in POST set_language, django_language preference cookie and standard gettext catalogues; existing zh-hans default, browser preferences supported. No machine-translated database content or brand-name changes.

- [ ] Add tests for Chinese/English output, locale preference persistence, query-preserving return, unsupported language and safe next, CSRF protection, market labels and unchanged destinations.
- [ ] Enable Django language configuration and cookie-safe language endpoint; header switch in public navigation and legacy base templates; localize dynamic html lang and metadata. Use gettext for every public UI phrase, including ad labels and destination labels.
- [ ] Generate standard zh_Hans LC_MESSAGES django.po/mo using a reproducible local stdlib build helper (GNU gettext may not be installed). English msgids are fallback. Include code messages for destinations and market-label filter.
- [ ] Style switch for desktop/mobile and preserve fragment with small local JS enhancement; forms work without JS. Keep selected search filters and campaigns.
- [ ] Full isolated regression, compilation checks, preserve source changes, back up modified source, deploy without database migration, validate real HTTP and browser switching.

No new dependencies, payment, data migration or translations claimed for editorial records. This is interface localization; separate language URLs for independently indexed editorial content are a later SEO task.
