# Security Policy

## Maintainers
- Jordan Lee ([@jordan-lee](https://github.com/jordan-lee)) — jordan@whispertranscriber.io
- Priya Desai ([@priyadesai](https://github.com/priyadesai)) — priya@whispertranscriber.io

The maintainer team also monitors the shared distribution list security@whispertranscriber.io.

## Supported Versions

| Version | Supported |
| ------- | --------- |
| `main`  | ✅        |
| Latest tagged release | ✅ |
| Older releases | ❌ |

Security fixes are applied to the `main` branch and cherry-picked to the most recent stable tag when feasible.

## Reporting a Vulnerability

- Email security@whispertranscriber.io with a detailed report, proof-of-concept (if available), and reproduction steps.
- **Do not** open public issues for sensitive reports; send us an email instead.
- Encrypt reports with our PGP key on request.

### Response Service-Level Agreement (SLA)

We commit to the following timelines for security disclosures:

- **Acknowledgement**: within 1 business day of receipt.
- **Initial assessment**: within 3 business days, including a severity rating and next steps.
- **Remediation or mitigation**:
  - Critical severity: patch or mitigation within 7 calendar days.
  - High severity: patch or mitigation within 14 calendar days.
  - Medium severity: fix scheduled within the next planned release (no later than 30 calendar days).
  - Low severity / informational: addressed as part of regular maintenance.

If we cannot meet these targets, we will notify the reporter with status updates and revised timelines.

## Additional Guidance

- Rotate any credential committed to the repository immediately.
- Prefer private disclosure channels until a fix is available and deployed.
- When in doubt, reach out: security@whispertranscriber.io.
