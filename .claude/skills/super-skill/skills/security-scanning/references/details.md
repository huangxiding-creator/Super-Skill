# security-scanning — Detail Reference

Moved out of SKILL.md in the V4.1.5 progressive-disclosure upgrade (SKILL.md stays under the 490-line budget; this file loads on demand).

## OWASP Top 10 Coverage

```python
OWASP_TOP_10_CHECKS = {
    "A01_broken_access_control": {
        "patterns": [
            "role-based checks missing",
            "direct object reference",
            "missing authorization header"
        ],
        "tools": ["semgrep", "codeql"]
    },
    "A02_cryptographic_failures": {
        "patterns": [
            "weak algorithms (MD5, SHA1)",
            "hardcoded keys",
            "insecure random"
        ],
        "tools": ["semgrep", "sonarqube"]
    },
    "A03_injection": {
        "patterns": [
            "concatenated queries",
            "eval usage",
            "command execution"
        ],
        "tools": ["semgrep", "codeql", "snyk"]
    },
    "A04_insecure_design": {
        "patterns": [
            "missing rate limiting",
            "no input validation",
            "business logic flaws"
        ],
        "tools": ["ai-analysis", "manual-review"]
    },
    "A05_security_misconfiguration": {
        "patterns": [
            "debug mode enabled",
            "default credentials",
            "unnecessary services"
        ],
        "tools": ["trivy", "zap"]
    },
    "A06_vulnerable_components": {
        "patterns": [
            "outdated dependencies",
            "known CVEs"
        ],
        "tools": ["npm-audit", "snyk", "owasp-dependency-check"]
    },
    "A07_auth_failures": {
        "patterns": [
            "weak password policy",
            "no MFA",
            "session fixation"
        ],
        "tools": ["semgrep", "zap"]
    },
    "A08_integrity_failures": {
        "patterns": [
            "unsigned packages",
            "no CI/CD security"
        ],
        "tools": ["snyk", "sigstore"]
    },
    "A09_logging_failures": {
        "patterns": [
            "insufficient logging",
            "logged secrets"
        ],
        "tools": ["semgrep", "custom-rules"]
    },
    "A10_ssrf": {
        "patterns": [
            "user-provided URLs",
            "no URL validation"
        ],
        "tools": ["semgrep", "codeql"]
    }
}
```

## Security Report Template

```markdown
## Security Scan Report

### Summary
- **Critical**: 0
- **High**: 2
- **Medium**: 5
- **Low**: 12

### Critical/High Findings

| ID | Severity | Type | Location | Status |
|----|----------|------|----------|--------|
| VULN-001 | High | SQL Injection | api/users.py:45 | Open |
| VULN-002 | High | XSS | components/Form.tsx:23 | Open |

### Recommendations

1. **VULN-001**: Use parameterized queries
2. **VULN-002**: Sanitize user input before rendering

### Scan Coverage
- SAST: 100% of source files
- SCA: 847 dependencies scanned
- Secrets: Git history scanned

### Compliance
- OWASP Top 10: 80% covered
- SOC 2: Pass
- PCI-DSS: Requires remediation
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.7 |

---

## References

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [Semgrep Documentation](https://semgrep.dev/docs/)
- [Snyk Documentation](https://docs.snyk.io/)
- [GitHub Security Lab](https://securitylab.github.com/)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
