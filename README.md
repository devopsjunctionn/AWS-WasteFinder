# AWS WasteFinder

**Stop paying for cloud resources you forgot to delete.**

AWS WasteFinder scans your entire AWS account across all regions and finds 6 types of waste that silently drain your budget every month.

---

## The Problem

Every month, companies waste **27% of their cloud spending** on forgotten resources:

- **Orphaned EBS volumes** from deleted servers → $50-500/month
- **Unused Elastic IPs** (AWS charges $3.60/month each since Feb 2024)
- **Idle Load Balancers** with no traffic → $18-25/month each
- **Old snapshots** from projects abandoned months ago → $20-200/month
- **NAT Gateways** nobody's using → $32/month each
- **SageMaker notebooks** left running after testing → $70-500/month

**AWS Cost Explorer shows you spent money. WasteFinder shows you WHERE to save it.**

---

## What It Does

AWS WasteFinder automatically scans **all AWS regions** and detects:

| Waste Type | What It Finds | Typical Savings |
|------------|---------------|-----------------|
| 🗄️ **EBS Volumes** | Orphaned volumes (not attached to instances) | $50-500/month |
| 🌐 **Elastic IPs** | Unattached public IPs | $3.60/month each |
| ⚖️ **Load Balancers** | Load balancers with no healthy targets | $18-25/month each |
| 💾 **Snapshots** | Old snapshots from deleted volumes (>90 days) | $20-200/month |
| 🔌 **NAT Gateways** | Idle network gateways | $32/month each |
| 🤖 **SageMaker** | Forgotten ML notebook instances | $70-500/month each |

---

## Quick Start

### Prerequisites

- Python 3.8 or higher
- AWS account with credentials configured
- AWS IAM user with `ReadOnlyAccess` policy

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/aws-wastefinder.git
cd aws-wastefinder

# Install dependencies
pip install boto3

# Run the scanner
python wastefinder.py
```

### Output Example

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║             AWS WASTEFINDER - FREE EDITION                ║
║                                                           ║
║          Scan for Cloud Waste in 6 Categories            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

Starting comprehensive waste scan...
   This will check all AWS regions for 6 types of waste.

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
- Typical cost: $18-25/month per idle LB

### EBS Snapshots
- Finds snapshots from deleted volumes
- Flags snapshots older than 90 days
- Cost: $0.05 per GB/month

### NAT Gateways
- Lists all active NAT Gateways
- Cost: $32.40/month + data transfer charges
- Note: Manual verification needed (check CloudWatch for actual usage)

### SageMaker Notebooks
- Detects notebook instances in "InService" status
- Shows instance type and running duration
- Cost varies: $70-500/month depending on instance type

---

## Use Cases

### For Startups
- **Problem:** AWS bill jumped from $2K to $5K unexpectedly
- **Solution:** Run WasteFinder monthly to catch forgotten resources
- **Result:** Save $500-2000/month

### For DevOps Engineers
- **Problem:** Boss asks "Why is our bill so high?"
- **Solution:** Run WasteFinder, generate report, show findings
- **Result:** Look like a hero by finding $2K in waste

### For Freelance CTOs
- **Problem:** Managing AWS for 5-10 clients manually
- **Solution:** Run WasteFinder on each client account monthly
- **Result:** Save each client $500-1500/month, bill them for "cost optimization"

### For Agencies
- **Problem:** Client complains about high AWS costs
- **Solution:** Use WasteFinder to audit their account
- **Result:** Show quick wins, increase trust, upsell management services

---

## How Is This Different?

### vs. AWS Cost Explorer
| Feature | AWS Cost Explorer | WasteFinder |
|---------|-------------------|-------------|
| Shows total spend | ✅ | ✅ |
| Identifies specific waste | ❌ | ✅ |
| Multi-region scan | Manual (20+ clicks) | Automatic |
| Actionable commands | ❌ | ✅ |
| Cost | Free (basic) / $0.01/API call | Free |

### vs. Enterprise Tools (CloudHealth, nOps, Vantage)
| Feature | Enterprise Tools | WasteFinder |
|---------|------------------|-------------|
| Waste detection | ✅ | ✅ |
| Price | $5,000-50,000/year | Free |
| Setup complexity | Hours + sales calls | 5 minutes |
| Target audience | Large enterprises | Startups, freelancers |

---

## Upgrade to WasteFinder Pro

Like what you see? **WasteFinder Pro** adds professional features:

### Pro Features (₹999 / $12 USD)
✅ **Notion Dashboard** - Visual reports you can share with your team  
✅ **PDF Export** - Professional reports for clients/management  
✅ **Scheduled Scans** - Automated weekly/monthly checks  
✅ **Email Notifications** - Get alerted when waste is detected  

### Enterprise Features ($49 USD)
✅ **AI Analysis** - GPT-4 explains WHY resources are wasting money  
✅ **Slack Integration** - Real-time alerts in your Slack workspace  
✅ **Multi-Account Support** - Scan 10+ AWS accounts from one dashboard  
✅ **Commercial License** - Use on unlimited client projects  
✅ **White-Label** - Rebrand with your company name  

**[Send a Mail for purchase →](#engineer.vaibhavt@gmail.com)**

---

## Contributing

Contributions are welcome! Here's how you can help:

1. **Report bugs** - Open an issue if you find something broken
2. **Suggest features** - What waste types should we add next?
3. **Submit PRs** - Improve the code, add documentation
4. **Share** - Star the repo and tell your DevOps friends

---

## 📝 License

This project is licensed under the MIT License

**TL;DR:** Free to use, modify, and distribute. Just keep the license notice.

---

## Important Notes

### Safety
- This tool is **READ-ONLY** - it never deletes anything automatically
- Always verify findings before deleting resources
- Test deletion commands in a dev account first

### Permissions
- Requires AWS IAM `ReadOnlyAccess` policy
- No write permissions needed
- Safe to run in production accounts

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
**Normal:** Scanning 17 regions takes 2-3 minutes. Enterprise tools take similar time.

---

## Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/aws-wastefinder/issues)

---

## 🌟 Show Your Support

If this tool saved you money:
- ⭐ Star this repository
- 🐦 Tweet about it
- 👨‍💻 Share with your DevOps friends
- ☕ [Buy me a coffee](#) (optional!)

---

## 📚 Related Resources

- [AWS Cost Optimization Guide](https://aws.amazon.com/pricing/cost-optimization/)
- [AWS Trusted Advisor](https://aws.amazon.com/premiumsupport/technology/trusted-advisor/)
- [r/aws Subreddit](https://reddit.com/r/aws)
- [AWS Cost Optimization Blog Posts](https://aws.amazon.com/blogs/aws-cost-management/)

---

<div align="center">

**Made with ❤️ by Unkown**

*Helping developers save money one forgotten resource at a time*

</div>
