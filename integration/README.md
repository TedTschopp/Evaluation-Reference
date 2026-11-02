# Embedding your installation

The self-contained [example](embed.html) assumes it is served at `integration/embed.html` beneath the lab. Its links use the local parent directory. Copy it to your site and adjust those relative paths to your deployment.

The iframe uses `embed=1`. The example sets `parent_origin` to the parent page's exact origin. The app sends height updates only to that validated HTTP(S) origin. The parent listener verifies both the child's origin and window identity.

For different parent and child origins, set the iframe's lab URL and the full-page link to your own installation, and retain the checks in the example. Configure the parent's Content-Security-Policy `frame-src` and the lab's `frame-ancestors` for the intended origins. The reference imposes no personal-domain allowlist.

The app's reference-materials panel can generate an iframe URL from the currently running installation. Supply the parent origin there if automatic height updates are wanted. Without one, the iframe still works at its specified fixed height.

The article uses a native details/summary disclosure with a short guide. Its iframe loads on first expansion on wider screens and retains the selected lesson when collapsed and reopened. At phone widths, the disclosure provides a full-page lab link so its evidence and controls have more room.

Keep a normal link to the standalone lab as a fallback for narrow screens and readers who prefer a full-page view.

