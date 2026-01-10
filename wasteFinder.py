#!/usr/bin/env python3
"""
AWS WasteFinder - Free Edition
Scans for 6 types of cloud waste across all AWS regions

Author: Vaibhav Thukral
GitHub: https://github.com/devopsjunctionn/AWS-WasteFinder
License: MIT
"""

__version__ = "1.0.1"

import boto3
import logging
import time
from datetime import datetime, timedelta, timezone
from botocore.exceptions import ClientError
import sys

# Configure logging - set to DEBUG for troubleshooting
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AWSWasteFinder:
    """
    AWS WasteFinder scans for unused/idle resources that cost money.
    
    Pricing data last verified: January 2026
    Note: AWS prices vary by region; these are US East (N. Virginia) estimates.
    For accurate pricing, consult: https://aws.amazon.com/pricing/
    """
    
    # Centralized pricing configuration (USD) - Last updated: January 2026
    PRICING = {
        'ebs_per_gb': {
            'gp2': 0.10, 'gp3': 0.08, 'io1': 0.125,
            'io2': 0.125, 'st1': 0.045, 'sc1': 0.015,
            'standard': 0.05
        },
        'elastic_ip': 3.60,           # Per unused IP/month (since Feb 2024)
        'snapshot_per_gb': 0.05,      # Per GB/month
        'nat_gateway': 32.40,         # Base monthly cost (excludes data transfer)
        'load_balancer': {
            'application': 18.0,      # ALB monthly base
            'network': 22.0,          # NLB monthly base
            'classic': 18.0           # Classic ELB monthly base
        },
        'sagemaker_instances': {
            'ml.t3.medium': 70, 'ml.t3.large': 120,
            'ml.m5.xlarge': 230, 'ml.p3.2xlarge': 490,
            'default': 100
        }
    }
    
    # Rate limiting: seconds to wait between region scans
    SCAN_DELAY = 0.3
    
    def __init__(self):
        self.total_waste = 0
        self.findings = []
        
    def print_banner(self):
        banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║             AWS WASTEFINDER - FREE EDITION                ║
║                                                           ║
║          Scan for Cloud Waste in 6 Categories            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""
        print(banner)
        
    def get_all_regions(self):
        """Get list of all AWS regions"""
        try:
            ec2 = boto3.client('ec2', region_name='us-east-1')
            regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
            return regions
        except Exception as e:
            print(f"Error fetching regions: {e}")
            return ['us-east-1']  # Fallback to default region
    
    def scan_ebs_volumes(self, region):
        """
        WASTE TYPE 1: Orphaned EBS Volumes
        These are storage volumes not attached to any EC2 instance
        Cost: $0.08-0.125 per GB/month depending on type
        """
        findings = []
        try:
            ec2 = boto3.client('ec2', region_name=region)
            volumes = ec2.describe_volumes()['Volumes']
            
            for vol in volumes:
                if vol['State'] == 'available':  # Not attached to anything
                    vol_id = vol['VolumeId']
                    size_gb = vol['Size']
                    vol_type = vol['VolumeType']
                    create_time = vol['CreateTime']
                    
                    # Cost calculation based on volume type
                    monthly_cost = size_gb * self.PRICING['ebs_per_gb'].get(vol_type, 0.10)
                    
                    days_orphaned = (datetime.now(create_time.tzinfo) - create_time).days
                    
                    findings.append({
                        'type': 'EBS Volume',
                        'id': vol_id,
                        'region': region,
                        'details': f"{size_gb} GB ({vol_type})",
                        'age': f"{days_orphaned} days orphaned",
                        'monthly_cost': monthly_cost,
                        'action': f"aws ec2 delete-volume --volume-id {vol_id} --region {region}"
                    })
        except ClientError as e:
            if 'AuthFailure' not in str(e):
                logger.warning(f"Error scanning EBS in {region}: {e}")
        except Exception as e:
            logger.debug(f"Unexpected error scanning EBS in {region}: {e}")
            
        return findings
    
    def scan_elastic_ips(self, region):
        """
        WASTE TYPE 2: Unused Elastic IPs
        AWS charges $3.60/month for EACH unattached IP (since Feb 2024)
        Cost: $3.60/month per unused IP
        """
        findings = []
        try:
            ec2 = boto3.client('ec2', region_name=region)
            addresses = ec2.describe_addresses()['Addresses']
            
            for addr in addresses:
                # If no AssociationId, the IP is not attached to anything
                if 'AssociationId' not in addr:
                    public_ip = addr['PublicIp']
                    allocation_id = addr.get('AllocationId')
                    
                    # EC2-Classic IPs don't have AllocationId - handle differently
                    if allocation_id:
                        action = f"aws ec2 release-address --allocation-id {allocation_id} --region {region}"
                    else:
                        # EC2-Classic IP (legacy) - use public IP to release
                        action = f"aws ec2 release-address --public-ip {public_ip} --region {region}"
                    
                    findings.append({
                        'type': 'Elastic IP',
                        'id': public_ip,
                        'region': region,
                        'details': f"Allocation: {allocation_id or 'EC2-Classic'}",
                        'age': 'Unattached',
                        'monthly_cost': self.PRICING['elastic_ip'],
                        'action': action
                    })
        except ClientError as e:
            if 'AuthFailure' not in str(e):
                logger.warning(f"Error scanning IPs in {region}: {e}")
        except Exception as e:
            logger.debug(f"Unexpected error scanning IPs in {region}: {e}")
            
        return findings
    
    def scan_load_balancers(self, region):
        """
        WASTE TYPE 3: Idle Load Balancers
        Load balancers with no active targets cost $16-25/month
        Cost: ~$18/month average
        """
        findings = []
        try:
            # Check ELBv2 (Application/Network Load Balancers)
            elbv2 = boto3.client('elbv2', region_name=region)
            load_balancers = elbv2.describe_load_balancers()['LoadBalancers']
            
            for lb in load_balancers:
                lb_arn = lb['LoadBalancerArn']
                lb_name = lb['LoadBalancerName']
                lb_type = lb['Type']
                
                # Check if it has any healthy targets
                target_groups = elbv2.describe_target_groups(LoadBalancerArn=lb_arn)['TargetGroups']
                
                has_healthy_targets = False
                for tg in target_groups:
                    tg_arn = tg['TargetGroupArn']
                    health = elbv2.describe_target_health(TargetGroupArn=tg_arn)['TargetHealthDescriptions']
                    
                    if any(t['TargetHealth']['State'] == 'healthy' for t in health):
                        has_healthy_targets = True
                        break
                
                if not has_healthy_targets:
                    cost = self.PRICING['load_balancer'].get(lb_type, 18.0)
                    
                    findings.append({
                        'type': 'Load Balancer',
                        'id': lb_name,
                        'region': region,
                        'details': f"Type: {lb_type.upper()}",
                        'age': 'No healthy targets',
                        'monthly_cost': cost,
                        'action': f"aws elbv2 delete-load-balancer --load-balancer-arn {lb_arn} --region {region}"
                    })
            
            # Also check Classic Load Balancers (ELB)
            elb = boto3.client('elb', region_name=region)
            classic_lbs = elb.describe_load_balancers()['LoadBalancerDescriptions']
            
            for clb in classic_lbs:
                clb_name = clb['LoadBalancerName']
                instances = clb.get('Instances', [])
                
                # Check if Classic LB has any registered instances
                if not instances:
                    findings.append({
                        'type': 'Load Balancer',
                        'id': clb_name,
                        'region': region,
                        'details': 'Type: CLASSIC',
                        'age': 'No registered instances',
                        'monthly_cost': self.PRICING['load_balancer']['classic'],
                        'action': f"aws elb delete-load-balancer --load-balancer-name {clb_name} --region {region}"
                    })
                    
        except ClientError as e:
            if 'AuthFailure' not in str(e) and 'AccessDenied' not in str(e):
                logger.warning(f"Error scanning Load Balancers in {region}: {e}")
        except Exception as e:
            logger.debug(f"Unexpected error scanning Load Balancers in {region}: {e}")
            
        return findings
    
    def scan_snapshots(self, region):
        """
        WASTE TYPE 4: Old EBS Snapshots
        Snapshots from deleted volumes accumulate costs
        Cost: $0.05 per GB/month
        """
        findings = []
        try:
            ec2 = boto3.client('ec2', region_name=region)
            
            # Get snapshots owned by this account
            snapshots = ec2.describe_snapshots(OwnerIds=['self'])['Snapshots']
            
            # Get all current volume IDs
            volumes = ec2.describe_volumes()['Volumes']
            current_volume_ids = {v['VolumeId'] for v in volumes}
            
            ninety_days_ago = datetime.now(timezone.utc) - timedelta(days=90)
            
            for snap in snapshots:
                snap_id = snap['SnapshotId']
                volume_id = snap.get('VolumeId', 'unknown')
                size_gb = snap['VolumeSize']
                start_time = snap['StartTime']
                
                # Flag if snapshot is from a deleted volume AND is older than 90 days
                if volume_id not in current_volume_ids and start_time < ninety_days_ago:
                    monthly_cost = size_gb * self.PRICING['snapshot_per_gb']
                    age_days = (datetime.now(start_time.tzinfo) - start_time).days
                    
                    findings.append({
                        'type': 'EBS Snapshot',
                        'id': snap_id,
                        'region': region,
                        'details': f"{size_gb} GB from deleted volume",
                        'age': f"{age_days} days old",
                        'monthly_cost': monthly_cost,
                        'action': f"aws ec2 delete-snapshot --snapshot-id {snap_id} --region {region}"
                    })
                    
        except ClientError as e:
            if 'AuthFailure' not in str(e):
                logger.warning(f"Error scanning Snapshots in {region}: {e}")
        except Exception as e:
            logger.debug(f"Unexpected error scanning Snapshots in {region}: {e}")
            
        return findings
    
    def scan_nat_gateways(self, region):
        """
        WASTE TYPE 5: Idle NAT Gateways
        NAT Gateways cost $32/month + data charges even if idle
        Cost: ~$32/month
        """
        findings = []
        try:
            ec2 = boto3.client('ec2', region_name=region)
            nat_gateways = ec2.describe_nat_gateways(
                Filters=[{'Name': 'state', 'Values': ['available']}]
            )['NatGateways']
            
            # For free version, we flag ALL NAT gateways (paid version would check CloudWatch metrics)
            for nat in nat_gateways:
                nat_id = nat['NatGatewayId']
                subnet_id = nat['SubnetId']
                
                findings.append({
                    'type': 'NAT Gateway',
                    'id': nat_id,
                    'region': region,
                    'details': f"Subnet: {subnet_id}",
                    'age': 'Active (check if needed)',
                    'monthly_cost': self.PRICING['nat_gateway'],
                    'action': f"aws ec2 delete-nat-gateway --nat-gateway-id {nat_id} --region {region}"
                })
                
        except ClientError as e:
            if 'AuthFailure' not in str(e):
                logger.warning(f"Error scanning NAT Gateways in {region}: {e}")
        except Exception as e:
            logger.debug(f"Unexpected error scanning NAT Gateways in {region}: {e}")
            
        return findings
    
    def scan_sagemaker(self, region):
        """
        WASTE TYPE 6: Forgotten SageMaker Notebooks
        ML notebook instances cost $50-500/month if left running
        Cost: Varies by instance type (~$70/month average for ml.t3.medium)
        """
        findings = []
        try:
            sagemaker = boto3.client('sagemaker', region_name=region)
            notebooks = sagemaker.list_notebook_instances()['NotebookInstances']
            
            for nb in notebooks:
                if nb['NotebookInstanceStatus'] == 'InService':
                    nb_name = nb['NotebookInstanceName']
                    instance_type = nb['InstanceType']
                    last_modified = nb['LastModifiedTime']
                    
                    days_running = (datetime.now(last_modified.tzinfo) - last_modified).days
                    
                    # Cost estimation (approximate)
                    sagemaker_pricing = self.PRICING['sagemaker_instances']
                    monthly_cost = sagemaker_pricing.get(instance_type, sagemaker_pricing['default'])
                    
                    findings.append({
                        'type': 'SageMaker Notebook',
                        'id': nb_name,
                        'region': region,
                        'details': f"Instance: {instance_type}",
                        'age': f"Running for {days_running} days",
                        'monthly_cost': monthly_cost,
                        'action': f"aws sagemaker stop-notebook-instance --notebook-instance-name {nb_name} --region {region}"
                    })
                    
        except ClientError as e:
            if 'AuthFailure' not in str(e):
                logger.warning(f"Error scanning SageMaker in {region}: {e}")
        except Exception as e:
            logger.debug(f"Unexpected error scanning SageMaker in {region}: {e}")
            
        return findings
    
    def scan_region(self, region):
        """Scan all waste types in a single region"""
        findings = []
        findings.extend(self.scan_ebs_volumes(region))
        findings.extend(self.scan_elastic_ips(region))
        findings.extend(self.scan_load_balancers(region))
        findings.extend(self.scan_snapshots(region))
        findings.extend(self.scan_nat_gateways(region))
        findings.extend(self.scan_sagemaker(region))
        return findings
    
    def generate_report(self):
        """Generate formatted console and file report"""
        print("\n" + "="*80)
        
        if not self.findings:
            print("\n EXCELLENT NEWS! No waste detected in your AWS account.")
            print("   Your infrastructure is clean and optimized!\n")
            print("="*80)
            return
        
        print("\n🚨 WASTE DETECTED - Resources Costing You Money\n")
        print("="*80 + "\n")
        
        # Group by type
        by_type = {}
        for finding in self.findings:
            waste_type = finding['type']
            if waste_type not in by_type:
                by_type[waste_type] = []
            by_type[waste_type].append(finding)
        
        # Print findings by type
        for waste_type, items in by_type.items():
            print(f"\n{'='*80}")
            print(f"  {waste_type.upper()} WASTE")
            print(f"{'='*80}\n")
            
            for item in items:
                print(f"  Resource ID: {item['id']}")
                print(f"  Region:      {item['region']}")
                print(f"  Details:     {item['details']}")
                print(f"  Status:      {item['age']}")
                print(f"  💰 Cost:     ${item['monthly_cost']:.2f}/month (${item['monthly_cost']*12:.2f}/year)")
                print(f"  Action:      {item['action']}")
                print(f"  {'-'*76}")
        
        # Summary
        print(f"\n{'='*80}")
        print(f"  SUMMARY")
        print(f"{'='*80}\n")
        print(f"  Total Resources Found: {len(self.findings)}")
        print(f"  MONTHLY WASTE:      ${self.total_waste:.2f}")
        print(f"  YEARLY WASTE:       ${self.total_waste * 12:.2f}")
        print(f"\n{'='*80}\n")
        
        # Save to file
        self.save_report()
        
        # Upsell message
        self.print_upsell()
    
    def save_report(self):
        """Save detailed report to file"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"aws_waste_report_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write("AWS WASTEFINDER - WASTE DETECTION REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            
            if not self.findings:
                f.write("No waste detected. Account is clean!\n")
            else:
                by_type = {}
                for finding in self.findings:
                    waste_type = finding['type']
                    if waste_type not in by_type:
                        by_type[waste_type] = []
                    by_type[waste_type].append(finding)
                
                for waste_type, items in by_type.items():
                    f.write(f"\n{waste_type.upper()} WASTE\n")
                    f.write("-"*80 + "\n")
                    
                    for item in items:
                        f.write(f"\nResource ID: {item['id']}\n")
                        f.write(f"Region: {item['region']}\n")
                        f.write(f"Details: {item['details']}\n")
                        f.write(f"Status: {item['age']}\n")
                        f.write(f"Monthly Cost: ${item['monthly_cost']:.2f}\n")
                        f.write(f"Yearly Cost: ${item['monthly_cost']*12:.2f}\n")
                        f.write(f"Cleanup Command: {item['action']}\n")
                        f.write("-"*80 + "\n")
                
                f.write(f"\n\nTOTAL SUMMARY\n")
                f.write("="*80 + "\n")
                f.write(f"Total Resources: {len(self.findings)}\n")
                f.write(f"Monthly Waste: ${self.total_waste:.2f}\n")
                f.write(f"Yearly Waste: ${self.total_waste * 12:.2f}\n")
        
        print(f"  📄 Detailed report saved to: {filename}\n")
    
    def print_upsell(self):
        """Print upgrade message"""
        print("╔═════════════════════════════════════════════════════════════════════════╗")
        print("║                                                                         ║")
        print("║  💡 UPGRADE TO WASTEFINDER PRO                                          ║")
        print("║                                                                         ║")
        print("║  WasteFinder Pro includes:                                              ║")
        print("║    ✓ Notion Dashboard (professional visual reports)                     ║")
        print("║    ✓ AI-Powered Analysis (explains WHY waste exists)                    ║")
        print("║    ✓ Scheduled Scans & Email Notifications                              ║")
        print("║                                                                         ║")
        print("║  Pricing: ₹999 ($12 USD) - For individuals & small teams                ║")
        print("║                                                                         ║")
        print("║  Contact: engineer.vaibhavt@gmail.com                                   ║")
        print("║                                                                         ║")
        print("╚═════════════════════════════════════════════════════════════════════════╝")
    
    def run(self):
        """Main execution"""
        self.print_banner()
        
        print("Starting comprehensive waste scan...")
        print("   This will check all AWS regions for 6 types of waste.\n")
        
        # Verify AWS credentials
        try:
            sts = boto3.client('sts')
            account_id = sts.get_caller_identity()['Account']
            print(f"Connected to AWS Account: {account_id}\n")
        except Exception as e:
            print("ERROR: Could not connect to AWS.")
            print("\nPlease configure your AWS credentials:")
            print("  Option 1: Run 'aws configure'")
            print("  Option 2: Set environment variables AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY\n")
            sys.exit(1)
        
        # Get regions and scan
        print("Fetching AWS regions...\n")
        regions = self.get_all_regions()
        print(f"   Found {len(regions)} regions to scan\n")
        print("="*80)
        
        for i, region in enumerate(regions):
            print(f"Scanning {region}...", end=" ", flush=True)
            region_findings = self.scan_region(region)
            
            if region_findings:
                print(f"⚠️  Found {len(region_findings)} waste items")
                self.findings.extend(region_findings)
                self.total_waste += sum(f['monthly_cost'] for f in region_findings)
            else:
                print("✓")
            
            # Rate limiting: avoid API throttling (skip delay on last region)
            if i < len(regions) - 1:
                time.sleep(self.SCAN_DELAY)
        
        print("="*80)
        
        # Generate report
        self.generate_report()

if __name__ == "__main__":
    scanner = AWSWasteFinder()
    scanner.run()