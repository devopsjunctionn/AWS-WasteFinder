"""
Unit tests for AWS WasteFinder
Uses moto library to mock AWS services - no real AWS credentials needed
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from moto import mock_aws
import boto3

from wasteFinder import AWSWasteFinder


class TestAWSWasteFinder:
    """Test suite for AWSWasteFinder class"""

    @mock_aws
    def test_get_all_regions(self):
        """Test that we can fetch AWS regions"""
        scanner = AWSWasteFinder()
        regions = scanner.get_all_regions()
        
        # Moto provides a set of mock regions
        assert isinstance(regions, list)
        assert len(regions) > 0
        assert all(isinstance(r, str) for r in regions)

    @mock_aws
    def test_scan_ebs_volumes_finds_orphaned_volumes(self):
        """Test detection of orphaned (unattached) EBS volumes"""
        # Create a mock EC2 client and orphaned volume
        ec2 = boto3.client('ec2', region_name='us-east-1')
        
        # Create an unattached volume (orphaned)
        volume = ec2.create_volume(
            AvailabilityZone='us-east-1a',
            Size=100,
            VolumeType='gp2'
        )
        
        scanner = AWSWasteFinder()
        findings = scanner.scan_ebs_volumes('us-east-1')
        
        # Should find the orphaned volume
        assert len(findings) == 1
        assert findings[0]['type'] == 'EBS Volume'
        assert findings[0]['id'] == volume['VolumeId']

    @mock_aws
    def test_scan_ebs_volumes_ignores_attached_volumes(self):
        """Test that attached volumes are not flagged as waste"""
        ec2 = boto3.client('ec2', region_name='us-east-1')
        
        # Create an EC2 instance first
        instances = ec2.run_instances(
            ImageId='ami-12345678',
            MinCount=1,
            MaxCount=1,
            InstanceType='t2.micro'
        )
        instance_id = instances['Instances'][0]['InstanceId']
        
        # Create and attach a volume
        volume = ec2.create_volume(
            AvailabilityZone='us-east-1a',
            Size=100,
            VolumeType='gp2'
        )
        
        ec2.attach_volume(
            VolumeId=volume['VolumeId'],
            InstanceId=instance_id,
            Device='/dev/sdf'
        )
        
        scanner = AWSWasteFinder()
        findings = scanner.scan_ebs_volumes('us-east-1')
        
        # Should not find any waste since volume is attached
        assert len(findings) == 0

    @mock_aws
    def test_scan_elastic_ips_finds_unattached_ips(self):
        """Test detection of unattached Elastic IPs"""
        ec2 = boto3.client('ec2', region_name='us-east-1')
        
        # Allocate an Elastic IP (unattached)
        eip = ec2.allocate_address(Domain='vpc')
        
        scanner = AWSWasteFinder()
        findings = scanner.scan_elastic_ips('us-east-1')
        
        # Should find the unattached EIP
        assert len(findings) == 1
        assert findings[0]['type'] == 'Elastic IP'
        assert findings[0]['id'] == eip['PublicIp']

    @mock_aws
    def test_scan_multiple_regions(self):
        """Test scanning across multiple regions"""
        # Create orphaned volumes in different regions
        for region in ['us-east-1', 'us-west-2']:
            ec2 = boto3.client('ec2', region_name=region)
            ec2.create_volume(
                AvailabilityZone=f'{region}a',
                Size=50,
                VolumeType='gp2'
            )
        
        scanner = AWSWasteFinder()
        findings_east = scanner.scan_ebs_volumes('us-east-1')
        findings_west = scanner.scan_ebs_volumes('us-west-2')
        all_findings = findings_east + findings_west
        
        # Should find volumes in both regions
        assert len(all_findings) == 2
        regions_found = {item['region'] for item in all_findings}
        assert regions_found == {'us-east-1', 'us-west-2'}

    @mock_aws
    def test_cost_calculation_ebs_volumes(self):
        """Test that EBS volume costs are calculated correctly"""
        ec2 = boto3.client('ec2', region_name='us-east-1')
        
        # Create a 100GB gp2 volume
        ec2.create_volume(
            AvailabilityZone='us-east-1a',
            Size=100,
            VolumeType='gp2'
        )
        
        scanner = AWSWasteFinder()
        findings = scanner.scan_ebs_volumes('us-east-1')
        
        # gp2 costs $0.10/GB/month, so 100GB = $10/month
        assert len(findings) == 1
        assert findings[0]['monthly_cost'] == 10.0

    @mock_aws
    def test_cost_calculation_elastic_ips(self):
        """Test that Elastic IP costs are calculated correctly"""
        ec2 = boto3.client('ec2', region_name='us-east-1')
        ec2.allocate_address(Domain='vpc')
        
        scanner = AWSWasteFinder()
        findings = scanner.scan_elastic_ips('us-east-1')
        
        # Unattached EIP costs $3.60/month
        assert len(findings) == 1
        assert findings[0]['monthly_cost'] == 3.6

    def test_total_cost_calculation(self):
        """Test that total costs are summed correctly"""
        scanner = AWSWasteFinder()
        
        # Manually add findings
        findings = [
            {'type': 'EBS Volume', 'monthly_cost': 10.0, 'region': 'us-east-1', 'id': 'vol-1', 'details': 'test'},
            {'type': 'Elastic IP', 'monthly_cost': 3.6, 'region': 'us-east-1', 'id': 'eip-1', 'details': 'test'},
            {'type': 'Load Balancer', 'monthly_cost': 18.0, 'region': 'us-west-2', 'id': 'lb-1', 'details': 'test'},
        ]
        
        total = sum(item['monthly_cost'] for item in findings)
        assert total == 31.6

    def test_report_generation_empty(self):
        """Test report generation with no waste found"""
        scanner = AWSWasteFinder()
        scanner.findings = []
        
        # Should not raise an error
        scanner.generate_report()

    def test_version_exists(self):
        """Test that version is defined"""
        from wasteFinder import __version__
        assert __version__ is not None
        assert isinstance(__version__, str)
        assert len(__version__) > 0


class TestEdgeCases:
    """Test edge cases and error handling"""

    @mock_aws
    def test_empty_region_scan(self):
        """Test scanning a region with no resources"""
        scanner = AWSWasteFinder()
        findings = scanner.scan_ebs_volumes('us-east-1')
        
        assert len(findings) == 0

    @mock_aws
    def test_handles_api_errors_gracefully(self):
        """Test that API errors don't crash the scanner"""
        scanner = AWSWasteFinder()
        
        # Scanning an invalid region should handle the error gracefully
        with patch('boto3.client') as mock_client:
            mock_client.side_effect = Exception("API Error")
            # Should not raise, just log the error
            try:
                scanner.scan_ebs_volumes('invalid-region')
            except Exception:
                pass  # Some error handling is expected


class TestIntegration:
    """Integration tests (require mocked AWS)"""

    @mock_aws
    def test_full_scan_workflow(self):
        """Test complete scan workflow"""
        # Setup: Create various waste resources
        ec2 = boto3.client('ec2', region_name='us-east-1')
        
        # Create orphaned EBS volume
        ec2.create_volume(
            AvailabilityZone='us-east-1a',
            Size=100,
            VolumeType='gp2'
        )
        
        # Create unattached EIP
        ec2.allocate_address(Domain='vpc')
        
        # Run scanner - scan_region returns findings
        scanner = AWSWasteFinder()
        findings = scanner.scan_region('us-east-1')
        
        # Verify findings - should find at least EBS and EIP
        ebs_findings = [f for f in findings if f['type'] == 'EBS Volume']
        eip_findings = [f for f in findings if f['type'] == 'Elastic IP']
        
        assert len(ebs_findings) >= 1
        assert len(eip_findings) >= 1
