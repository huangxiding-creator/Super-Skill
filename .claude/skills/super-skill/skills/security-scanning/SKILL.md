---
name: security-scanning
description: Comprehensive security scanning with SAST, dependency vulnerability detection, and AI-powered analysis. Integrates multiple security tools for production-grade vulnerability management.
tags: [security, sast, vulnerability, scanning, dependency, owasp]
version: 1.0.0
source: Based on industry SAST tools (Snyk, Semgrep, Checkmarx), OWASP best practices
integrated-with: super-skill v3.7+
---

# Security Scanning Skill

This skill provides comprehensive security scanning capabilities including Static Application Security Testing (SAST), dependency vulnerability detection, secret scanning, and AI-powered security analysis.

## Security Scanning Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY SCANNING STACK                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Layer 1: CODE SCANNING (SAST)                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • SQL Injection    • XSS        • CSRF                  │    │
│  │ • Path Traversal   • SSRF       • Command Injection     │    │
│  │ • Insecure Crypto  • Auth Bypass • IDOR                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Layer 2: DEPENDENCY SCANNING (SCA)                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Known CVEs       • License Issues   • Malware        │    │
│  │ • Transitive Deps  • Outdated Pkgs     • Supply Chain  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Layer 3: SECRET SCANNING                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • API Keys         • Passwords      • Tokens           │    │
│  │ • Certificates     • Private Keys   • Connection Strs  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Layer 4: CONTAINER SCANNING                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Base Image CVEs  • Config Issues   • Secrets in Img  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## SAST Tools Integration

### Top SAST Tools 2025

| Tool | Type | Key Features | Best For |
|------|------|-------------|----------|
| **Semgrep** | Open Source | Fast, custom rules, AI Assistant | Developer-focused |
| **Snyk Code** | Commercial | AI intent analysis, 65% FP reduction | Full SDLC |
| **CodeQL** | Free (OSS) | Deep semantic analysis | GitHub projects |
| **SonarQube** | Open/Comm | Quality + Security combined | Enterprise |
| **Checkmarx** | Commercial | Multi-language, AI semantic | Enterprise |

### Semgrep Configuration

```yaml
# .semgrep.yml
rules:
  - id: secrets-detection
    patterns:
      - pattern-either:
          - pattern: $API_KEY = "..."
          - pattern: api_key = $VAL
          - pattern: password = $VAL
    message: Potential hardcoded secret
    severity: ERROR
    languages: [python, javascript, typescript]

  - id: sql-injection
    patterns:
      - pattern: cursor.execute($QUERY, ...)
      - pattern-not: cursor.execute("...", ...)
    message: Potential SQL injection
    severity: ERROR
    languages: [python]
```

### CodeQL Configuration

```yaml
# .github/codeql/codeql-config.yml
name: Custom CodeQL Configuration

paths:
  - src
  - lib

paths-ignore:
  - '**/test/**'
  - '**/tests/**'

queries:
  - uses: security-and-quality
  - uses: security-extended

query-filters:
  - exclude:
      id: cpp/unused-local-variable
```

## Dependency Scanning (SCA)

### npm Audit

```bash
# Basic audit
npm audit

# Audit with fix
npm audit fix

# Production only
npm audit --production

# JSON output for CI
npm audit --json
```

### Snyk Integration

```yaml
# .github/workflows/security.yml
name: Security
on: [push, pull_request]

jobs:
  snyk:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high
```

### OWASP Dependency-Check

```xml
<!-- Maven plugin -->
<plugin>
    <groupId>org.owasp</groupId>
    <artifactId>dependency-check-maven</artifactId>
    <version>9.0.0</version>
    <configuration>
        <failBuildOnCVSS>7</failBuildOnCVSS>
        <suppressionFile>dependency-check-suppressions.xml</suppressionFile>
    </configuration>
</plugin>
```

## Secret Scanning

### GitLeaks Configuration

```yaml
# .gitleaks.toml
title = "Custom Gitleaks Config"

[[rules]]
id = "api-key"
description = "API Key"
regex = '''(?i)(api[_-]?key|apikey)['\"]?\s*[:=]\s*['\"]?[a-zA-Z0-9]{20,}'''
tags = ["key", "API"]

[[rules]]
id = "aws-access-key"
description = "AWS Access Key"
regex = '''AKIA[0-9A-Z]{16}'''
tags = ["key", "AWS"]

[[rules]]
id = "private-key"
description = "Private Key"
regex = '''-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----'''
tags = ["key", "private"]

[allowlist]
paths = [
    '''tests/''',
    '''\.example$'''
]
```

### TruffleHog

```bash
# Scan git history
trufflehog git file://. --only-verified

# Scan directory
trufflehog filesystem ./src

# Output JSON
trufflehog git file://. --json
```

## AI-Powered Security Analysis

### Claude Security Patterns

```python
SECURITY_ANALYSIS_PROMPT = """
Analyze the following code for security vulnerabilities:

Code:
```
{code}
```

Check for:
1. **Injection Vulnerabilities**
   - SQL Injection
   - Command Injection
   - LDAP Injection
   - XPath Injection

2. **Authentication & Authorization**
   - Broken authentication
   - Session management issues
   - Insecure access control

3. **Data Protection**
   - Sensitive data exposure
   - Insecure cryptography
   - Hardcoded secrets

4. **Input Validation**
   - XSS vulnerabilities
   - SSRF vulnerabilities
   - Path traversal

5. **Configuration**
   - Security misconfiguration
   - Insecure defaults
   - Missing security headers

For each finding:
- Severity: Critical/High/Medium/Low
- Line numbers affected
- Description of vulnerability
- Remediation steps
- Code example for fix
"""
```

### Automated Security Review

```python
class AISecurityScanner:
    """
    AI-powered security analysis.
    """

    async def analyze_code(self, code: str) -> dict:
        """
        Perform AI-powered security analysis.
        """
        response = await self.llm.generate(
            SECURITY_ANALYSIS_PROMPT.format(code=code)
        )

        return {
            "vulnerabilities": self.parse_findings(response),
            "recommendations": self.extract_recommendations(response),
            "secure_code": self.extract_fixes(response),
            "confidence": self.calculate_confidence(response)
        }

    async def analyze_diff(self, diff: str) -> dict:
        """
        Analyze code changes for security implications.
        """
        prompt = f"""
        Analyze these code changes for security vulnerabilities:

        Diff:
        ```diff
        {diff}
        ```

        Focus on:
        - New attack surface introduced
        - Security controls added/removed
        - Potential regression in security posture
        """

        return await self.analyze(prompt)
```

## Container Security

### Trivy Configuration

```yaml
# .github/workflows/container-scan.yml
name: Container Security
on:
  push:
    tags:
      - 'v*'

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build image
        run: docker build -t app:${{ github.sha }} .

      - name: Run Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'app:${{ github.sha }}'
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Upload results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
```

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

## Integration with Super-Skill

### Phase Integration

```yaml
security_phase_mapping:
  phase_5_design:
    actions:
      - threat_modeling
      - security_architecture_review

  phase_8_development:
    actions:
      - sast_scanning
      - secret_scanning
      - dependency_check

  phase_9_qa:
    actions:
      - penetration_testing
      - dast_scanning
      - security_regression_tests

  phase_11_deployment:
    actions:
      - container_scanning
      - iac_scanning
      - production_security_check
```

### Automated Security Gate

```python
async def security_gate(phase: int, context: dict) -> bool:
    """
    Security gate check before proceeding to next phase.
    """
    findings = []

    # Run all applicable scanners
    scanners = get_scanners_for_phase(phase)
    for scanner in scanners:
        results = await scanner.scan(context)
        findings.extend(results)

    # Check for blocking issues
    critical = [f for f in findings if f.severity == "CRITICAL"]
    high = [f for f in findings if f.severity == "HIGH"]

    if critical:
        raise SecurityGateFailure(
            f"Blocked by {len(critical)} critical findings"
        )

    if len(high) > 5:
        raise SecurityGateFailure(
            f"Too many high-severity findings: {len(high)}"
        )

    # Generate security report
    await generate_security_report(findings, context)

    return True
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

## Best Practices Checklist

### Pre-Commit
- [ ] No hardcoded secrets
- [ ] Input validation implemented
- [ ] Parameterized queries used
- [ ] Output encoding applied

### CI/CD
- [ ] SAST scan configured
- [ ] Dependency scan enabled
- [ ] Secret scanning active
- [ ] Security gate in place

### Deployment
- [ ] Container scan passed
- [ ] IaC scan passed
- [ ] Security headers configured
- [ ] TLS enabled

### Monitoring
- [ ] Security alerts configured
- [ ] Audit logging enabled
- [ ] Incident response plan ready
- [ ] Regular penetration testing scheduled

## Deliverables

- Security scan configuration files
- Custom Semgrep/CodeQL rules
- Security report
- Remediation recommendations
- Compliance documentation

---

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
