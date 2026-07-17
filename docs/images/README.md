# Documentation images

Keep repository-owned visuals organized in two separate locations:

- `application/` contains manually captured UI screenshots.
- `diagrams/` contains source-controlled architecture SVGs.

Use filenames such as `01-login-page.png` through `09-api-documentation.png`
for application captures. Prefer PNG, a consistent `1440x900` desktop viewport,
and a readable `390x844` mobile capture when responsive behavior matters.

Remove personal data, tokens, passwords, local filesystem paths, real resumes,
phone numbers, and addresses before committing an image. Optimize large PNGs
without making text unreadable. Replace screenshots in place when the UI changes;
do not embed generated or fabricated screenshots.

The root README embeds only screenshots that actually exist. Architecture
diagrams remain under `diagrams/` and should not be mixed with application
captures.
