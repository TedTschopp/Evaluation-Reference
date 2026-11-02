# Blog integration

The full app is at https://evals.tedt.org. The supplied ai-evaluation-lab.html file is a Jekyll landing page for /ai-evaluation-lab/ on tedt.org.

For an existing article, insert the iframe from embed.html. The app has an embedded layout and posts height changes only to the tedt.org parent. The optional resize listener verifies the exact child origin before updating the iframe.

The Cloudflare response permits framing by tedt.org and its subdomains. It does not set a conflicting same-origin X-Frame-Options header.

Keep a normal link to the standalone lab as a fallback for narrow screens and readers who prefer a full-page view.

