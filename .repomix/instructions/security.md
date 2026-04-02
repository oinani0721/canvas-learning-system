# Security Review Instructions

Analyze this codebase for security vulnerabilities:

1. **Input validation**: Are all user inputs validated? Any injection risks (SQL, XSS, command)?
2. **Authentication/Authorization**: Are auth flows secure? Token handling?
3. **Sensitive data**: Any hardcoded secrets, API keys, or credentials in code?
4. **File handling**: Are file uploads/downloads properly sanitized?
5. **Dependencies**: Any known vulnerable dependencies?
6. **API security**: Rate limiting? CORS configuration? Error message information leakage?

For each vulnerability: severity (CVSS-like), affected files, exploitation scenario, fix recommendation.
