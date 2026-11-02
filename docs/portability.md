# Portability changes in 1.1.0

The public reference and both independent downloads contain local assets and portable configuration. Live hosting is an operator concern, separate from the reference source.

| Previous dependency | Replacement |
|---|---|
| Personal hosting account, route, container, and deployment configuration in the React reference | Removed from public source and packaging. The operator maintains these outside the reference. |
| Provider deployment packages and scripts | Removed from the reference Node dependencies and CI. Local Python, static HTTP, and Docker startup remain available. |
| Absolute links to the author's site and hosted lab | Relative links to this installation, bundled guides, corpus, and optional local download catalogue. |
| Download buttons returning local users to the original host | Portable ZIP builds show local reference materials. Distributing builds add archives beside themselves through a relative-path catalogue. |
| Hardcoded embed destination and message recipient | Embed URL derived from the current installation; an explicit validated parent origin enables height messages. A generic example verifies message origin and source. |
| Personal production origin in the API | Same-origin support plus environment-configured permitted origins. |
| Provider-specific client-address header in the API | An optional trusted-proxy header configured by the operator; otherwise the direct client address. |
| Expired inference tunnel addresses in captured runs | Reserved non-resolving example addresses and explicit redaction provenance, preserving captured results and version metadata. |
| External article link in the Python sidebar | The bundled instructor guide, readable inside the app. |

The corpus transcriptions and archival source URLs are unchanged. Fonts, licenses, replay JSON, schemas, and the entire corpus are bundled. Microsoft documentation, National Archives citations, source repository links, and dependency registries remain available as external references; replay does not fetch them.

Run `python scripts/check_portability.py` after building and packaging. The guard checks distributable source, the compiled site, and every member of both ZIPs for prohibited destination domains, account fields, and operator files. It also verifies ZIP contents and embedded download catalogues. It does not rewrite Git history or authenticate imported model recordings.
