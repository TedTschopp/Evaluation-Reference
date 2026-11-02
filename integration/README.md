# Blog integration

The full app is at https://evals.tedt.org. The supplied ai-evaluation-lab.html file is a Jekyll landing page for /ai-evaluation-lab/ on tedt.org.

For an existing article, insert the iframe from embed.html. The app has an embedded layout and posts height changes only to the tedt.org parent. The optional resize listener verifies the exact child origin before updating the iframe.

The lab's Content-Security-Policy frame-ancestors directive permits tedt.org and its subdomains. TedT.org also adds a zone-wide X-Frame-Options header; supported modern browsers give the CSP directive precedence.

The parent blog's policy must permit the child too. TedT.org's shared content-security-policy include adds https://evals.tedt.org to frame-src for /ai-evaluation-lab/ and /Your-AI-Passed-the-Test/. Other blog pages retain their existing policy. When adapting this template to another site, configure the parent frame-src and the lab's frame-ancestors for the intended origins.

The article uses a native details/summary disclosure with a short guide. Its iframe loads on first expansion on wider screens and retains the selected lesson when collapsed and reopened. At phone widths, the disclosure provides a full-page lab link so its evidence and controls have more room.

Keep a normal link to the standalone lab as a fallback for narrow screens and readers who prefer a full-page view.

