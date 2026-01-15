# Changelog

All notable changes to AWS WasteFinder will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-01-13

### Added
- **CloudWatch Log Groups scanner** (7th waste type) - Detects log groups with infinite retention
- Added `logs:DescribeLogGroups` to IAM policy

### Changed
- Updated banner and documentation to reflect 7 waste categories

---

## [1.0.1] - 2026-01-10

### Added
- 13 unit tests with moto for AWS mocking (no real credentials needed)
- GitHub Actions CI/CD workflows for tests and releases
- CodeQL security scanning on every push
- Dependabot for automated dependency updates
- IAM policy JSON (`iam-policy.json`) for trust and transparency
- CONTRIBUTING.md with development guidelines
- Security badges in README

---

## [1.0.0] - 2026-01-10

### Added
- Initial release of AWS WasteFinder
- Scan for 6 types of cloud waste:
  - Orphaned EBS Volumes
  - Unused Elastic IPs
  - Idle Load Balancers (ALB/NLB)
  - Old EBS Snapshots (>90 days)
  - Idle NAT Gateways
  - Forgotten SageMaker Notebooks
- Multi-region scanning (all AWS regions)
- Cost estimation per resource
- Actionable AWS CLI commands for cleanup
- Text report generation with timestamps
- Console output with formatted tables

### Security
- Read-only access required (no write permissions)
- Minimal IAM policy documented

---

[1.0.1]: https://github.com/devopsjunctionn/AWS-WasteFinder/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/devopsjunctionn/AWS-WasteFinder/releases/tag/v1.0.0
