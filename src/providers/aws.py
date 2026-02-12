import concurrent.futures
import boto3
from typing import List, Dict, Optional
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError, BotoCoreError
from providers.base import CloudProvider
from core.logger import setup_logger

logger = setup_logger()

class AWSProvider(CloudProvider):
    def __init__(self):
        # Configure Boto3 client with timeouts to prevent hanging
        self.boto_config = BotoConfig(
            connect_timeout=5,
            read_timeout=10,
            retries={'max_attempts': 2}
        )

    def _get_regions(self) -> List[str]:
        print("Fetching regions...", end="\r")
        try:
            ec2 = boto3.client('ec2', config=self.boto_config)
            response = ec2.describe_regions()
            return [r['RegionName'] for r in response.get('Regions', [])]
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to fetch regions: {e}")
            return []

    def _get_instances_in_region(self, region: str) -> List[Dict]:
        instances = []
        try:
            # Create a client for the specific region
            ec2 = boto3.client('ec2', region_name=region, config=self.boto_config)
            
            # Use paginator to handle large results
            paginator = ec2.get_paginator('describe_instances')
            page_iterator = paginator.paginate(
                Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
            )

            for page in page_iterator:
                for reservation in page.get('Reservations', []):
                    for inst in reservation.get('Instances', []):
                        # Normalize data to match previous format
                        name_tag = next((t['Value'] for t in inst.get('Tags', []) if t['Key'] == 'Name'), None)
                        instances.append({
                            'Name': name_tag,
                            'PublicIp': inst.get('PublicIpAddress'),
                            'PrivateIp': inst.get('PrivateIpAddress'),
                            'Id': inst.get('InstanceId'),
                            'Lifecycle': inst.get('InstanceLifecycle'),
                            'Region': region,
                        })
        except (ClientError, BotoCoreError):
            logger.warning(f"Failed to scan region {region}")
            pass
            
        return instances

    def get_instances(self) -> List[Dict]:
        regions = self._get_regions()
        if not regions:
            logger.error("Could not fetch regions.")
            return []

        all_instances = []
        print(f"Scanning {len(regions)} regions...", end="\r")
        
        # Use ThreadPoolExecutor for parallel execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_region = {executor.submit(self._get_instances_in_region, region): region for region in regions}
            for future in concurrent.futures.as_completed(future_to_region):
                instances = future.result()
                if instances:
                    all_instances.extend(instances)
        
        return all_instances
