# AWS WasteFinder

[![Tests](https://github.com/devopsjunctionn/AWS-WasteFinder/actions/workflows/tests.yml/badge.svg)](https://github.com/devopsjunctionn/AWS-WasteFinder/actions/workflows/tests.yml)
[![Security](https://github.com/devopsjunctionn/AWS-WasteFinder/actions/workflows/security.yml/badge.svg)](https://github.com/devopsjunctionn/AWS-WasteFinder/actions/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)


A read-only CLI that scans all AWS regions and reports unused AWS resources.

Detects:
- Unattached EBS volumes
- Unused Elastic IPs
- Idle load balancers
- Old snapshots
- NAT Gateways
- Running SageMaker notebooks
- CloudWatch logs with infinite retention
- **Idle RDS databases** (0 connections in 7 days)

The tool does **not** delete anything.  
It prints AWS CLI commands so you can review and run them yourself.

---

## What It Does

AWS WasteFinder automatically scans **all AWS regions** and detects:

| Waste Type | What It Finds |
|------------|---------------|
| **EBS Volumes** | Orphaned volumes (not attached to instances) |
| **Elastic IPs** | Unattached public IPs |
| **Load Balancers** | Load balancers with no healthy targets |
| **Snapshots** | Old snapshots from deleted volumes (>90 days) |
| **NAT Gateways** | Idle network gateways |
| **SageMaker** | Forgotten ML notebook instances |
| **CloudWatch Logs** | Log groups with infinite retention |
| **RDS Instances** | Databases with 0 connections in 7 days |

---

## Quick Start

### Prerequisites

- Python 3.8 or higher
- AWS account with credentials configured
- AWS IAM user with `ReadOnlyAccess` policy

### Installation

```bash
# Clone the repository
git clone https://github.com/devopsjunctionn/AWS-WasteFinder.git
cd aws-wastefinder

# Install dependencies
pip install -r requirements.txt

# Run the scanner
python wasteFinder.py
```
## Dry Run & Safety

AWS WasteFinder is **read-only**.

It only calls AWS `Describe*` and `List*` APIs.
It does **not** create, modify, or delete any AWS resources.

The tool prints AWS CLI delete commands so you can review and run them manually.


### Output Example

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║                 AWS WASTEFINDER                           ║
║                                                           ║
║          Scan for Cloud Waste in 8 Categories             ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

Starting comprehensive waste scan...
   This will check all AWS regions for 8 types of waste.

Connected to AWS Account: 123456789012

 Fetching AWS regions...
   Found 17 regions to scan

Scanning us-east-1...   Found 3 waste items
Scanning us-west-2...  Found 1 waste items
Scanning eu-west-1... ✓
...

 WASTE DETECTED - Resources Costing You Money

EBS VOLUME WASTE
  Resource ID: vol-0abc123def456
  Region:      us-east-1
  Details:     100 GB (gp2)
  Status:      45 days orphaned
  Cost:     $10.00/month ($120.00/year)
  Action:      aws ec2 delete-volume --volume-id vol-0abc123def456 --region us-east-1

SUMMARY
  Total Resources Found: 8
  MONTHLY WASTE:      $247.20
  YEARLY WASTE:       $2,966.40

Detailed report saved to: aws_waste_report_2026-01-07_14-30-45.txt
```

---

## Setup Guide

### Step 1: Configure AWS Credentials

**Option 1: AWS CLI (Recommended)**

```bash
aws configure
```

Enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `us-east-1`)
- Default output format (e.g., `json`)

**Option 2: Environment Variables**

```bash
# Linux/Mac
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"

# Windows
set AWS_ACCESS_KEY_ID=your-access-key
set AWS_SECRET_ACCESS_KEY=your-secret-key
```

### Step 2: Create IAM User (If You Don't Have One)

1. Go to AWS Console → IAM → Users
2. Click "Create User"
3. Username: `wastefinder-scanner`
4. Attach policy: `ReadOnlyAccess`
5. Create access keys under "Security Credentials" tab

**Important:** This tool only READS data. It never deletes anything automatically.

---

## What Gets Scanned

### EBS Volumes
- Detects volumes with state `available` (not attached to any instance)
- Calculates cost based on volume type and size
- Shows how long the volume has been orphaned

### Elastic IPs
- Finds unattached Elastic IPs
- Since Feb 2024, AWS charges for ALL public IPs ($3.60/month)
- Shows allocation ID for easy deletion

### Load Balancers
- Checks Application and Network Load Balancers
- Identifies load balancers with no healthy targets

### EBS Snapshots
- Finds snapshots from deleted volumes
- Flags snapshots older than 90 days

### NAT Gateways
- Lists all active NAT Gateways
- Note: Manual verification needed (check CloudWatch for actual usage)

### SageMaker Notebooks
- Detects notebook instances in "InService" status
- Shows instance type and running duration
- Cost varies: $70-500/month depending on instance type

### CloudWatch Logs
- Finds log groups with no retention policy (infinite retention)
- Shows stored data size and estimated cost
- Cost: $0.03/GB/month for storage

---

## Limitations
- **Pricing estimates**: Actual costs may vary by region (estimates based on US East).
- **Snapshots**: Only flags snapshots older than 90 days from deleted volumes. These may be your only backup - verify before deleting.
- **CloudWatch Logs**: AWS updates `storedBytes` with ~24 hour delay. Cost shows $0.00 for newly created log groups until AWS updates the storage size.
- **RDS**: Read Replicas are skipped (they may have 0 connections intentionally).
- **Services covered**: Currently scans 8 resource types. Does not cover Lambda, S3, or other services.
- **Single account**: Scans one AWS account at a time. For multi-account, run separately per account.

## How Is This Different?

### vs. AWS Cost Explorer
| Feature | AWS Cost Explorer | WasteFinder |
|---------|-------------------|-------------|
| Shows total spend | ✅ | ✅ |
| Identifies specific waste | ❌ | ✅ |
| Multi-region scan | Manual (20+ clicks) | Automatic |
| Actionable commands | ❌ | ✅ |
| Cost | Free (basic) / $0.01/API call | Free |

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Setting up your development environment
- Running tests
- Branch naming conventions
- PR process

---

## License

This project is licensed under the MIT License

**TL;DR:** Free to use, modify, and distribute. Just keep the license notice.

---

## Security

This tool is **100% read-only** and never modifies or deletes any AWS resources.

### IAM Policy (Minimal Permissions)

For maximum security, create a dedicated IAM user with only the permissions WasteFinder needs. Copy this policy:

<details>
<summary>Click to expand IAM Policy JSON</summary>

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "WasteFinderReadOnly",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeVolumes",
        "ec2:DescribeAddresses",
        "ec2:DescribeRegions",
        "ec2:DescribeSnapshots",
        "ec2:DescribeNatGateways",
        "elasticloadbalancing:DescribeLoadBalancers",
        "elasticloadbalancing:DescribeTargetGroups",
        "elasticloadbalancing:DescribeTargetHealth",
        "sagemaker:ListNotebookInstances",
        "sagemaker:DescribeNotebookInstance",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

</details>

> **Note:** This policy is also available in [`iam-policy.json`](iam-policy.json) for easy import.

### How to Create a Dedicated IAM User

1. **Go to AWS Console** → IAM → Policies → **Create Policy**
2. Click the **JSON** tab
3. **Copy-paste** the contents of `iam-policy.json` (or the policy above)
4. Click **Next** → Name it `WasteFinderReadOnly` → **Create Policy**
5. Go to **Users** → **Create User** → Name: `wastefinder-scanner`
6. Click **Attach policies directly** → Search for `WasteFinderReadOnly` → Select it
7. **Create User** → Go to **Security Credentials** → **Create Access Key**
8. Choose **CLI** → Copy the Access Key and Secret
9. Run `aws configure` and paste your keys

**Or use AWS CLI:**
```bash
# Create the policy
aws iam create-policy --policy-name WasteFinderReadOnly --policy-document file://iam-policy.json

# Create user and attach policy (replace ACCOUNT_ID with your AWS account ID)
aws iam create-user --user-name wastefinder-scanner
aws iam attach-user-policy --user-name wastefinder-scanner --policy-arn arn:aws:iam::ACCOUNT_ID:policy/WasteFinderReadOnly
```

### Security Practices

- **Automated Security Scanning**: CodeQL analysis on every push
- **Dependency Updates**: Dependabot enabled for security patches  
- **No Secrets**: Never stores or transmits AWS credentials
- **Open Source**: Full code visibility for audit

### Safety Guarantees

- This tool **never deletes anything** automatically
- Always verify findings before taking action
- Test deletion commands in a dev account first

### Costs

- Running this script is **FREE** (only reads data, no API charges)
- Deleting resources after scanning saves you money

---

## Troubleshooting

### "Could not connect to AWS"
**Fix:** Configure your AWS credentials using `aws configure` or set environment variables.

### "Access Denied" errors
**Fix:** Ensure your IAM user has `ReadOnlyAccess` policy attached.

### Script finds nothing but you have waste
**Fix:** Check that you're scanning the correct AWS account. Run `aws sts get-caller-identity` to verify.

### Script is slow
**Normal:** Scanning 17 regions takes 2-3 minutes.

---

## Support

- **Issues:** [GitHub Issues](https://github.com/devopsjunctionn/aws-wastefinder/issues)

---

## 📚 Related Resources

- [AWS Cost Optimization Guide](https://aws.amazon.com/pricing/cost-optimization/)
- [AWS Trusted Advisor](https://aws.amazon.com/premiumsupport/technology/trusted-advisor/)
- [AWS Cost Optimization Blog Posts](https://aws.amazon.com/blogs/aws-cost-management/)

---

<div align="center">

*Helping developers save money one forgotten resource at a time*

</div>
