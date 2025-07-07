# Security Policy

## Supported Versions

We currently support security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in csDNA, please report it responsibly:

1. **Do not** create a public GitHub issue for security vulnerabilities
2. Send an email to the maintainers with details about the vulnerability
3. Include steps to reproduce the issue
4. Allow time for the vulnerability to be fixed before public disclosure

## Security Considerations

### File Uploads
- Only accept specific image file types (PNG, JPG, etc.)
- Validate file sizes to prevent denial of service
- Scan uploaded files for malicious content

### Data Processing
- Sanitize all user inputs
- Use secure temporary file handling
- Ensure proper cleanup of processed files

### Web Application
- Keep Django and all dependencies updated
- Use CSRF protection for all forms
- Implement proper authentication where needed
- Secure static file serving in production

## Best Practices

When contributing to csDNA:
- Never commit sensitive information (API keys, passwords, etc.)
- Use environment variables for configuration
- Follow secure coding practices
- Test security features thoroughly

Thank you for helping keep csDNA secure!