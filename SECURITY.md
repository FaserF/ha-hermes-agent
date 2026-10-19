# Security Policy for Hermes Agent Integration

---

## 🔒 Security Architecture

1. **Local & Remote Gateway Communication**
   - Connects directly to Hermes Agent gateway endpoints via HTTP/HTTPS or WebSocket with token-based authorization.
   - All API keys and connection tokens are securely stored in Home Assistant's encrypted configuration entry registry.

2. **Autonomous Tool Execution Controls**
   - Autonomous tool calling requires user consent by default through confirmation switches.
   - Fine-grained service permissions prevent unauthorized device actions.

3. **Masked Diagnostics**
   - Diagnostic exports automatically scrub API tokens, session authorization headers, and sensitive environment variables.

---

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability in this integration:

1. **Do NOT open a public issue.**
2. Report the vulnerability privately via [GitHub Security Advisories](https://github.com/FaserF/ha-hermes-agent/security/advisories/new) or email `github@fabiseitz.de`.
3. Provide reproduction details and impact assessment.
4. Reports are acknowledged within 48 hours with security patches prioritized.
