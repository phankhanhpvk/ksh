# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
import concurrent.futures
import threading
from typing import override

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError

from core.logger import get_logger
from providers.base import CloudProvider, Instance

logger = get_logger()


class AWSProvider(CloudProvider):
    def __init__(self) -> None:
        # Configure Boto3 client with timeouts to prevent hanging
        self.boto_config: BotoConfig = BotoConfig(
            connect_timeout=5,
            read_timeout=10,
            retries={"max_attempts": 2},
        )

    def _get_regions(self) -> list[str]:
        print("Fetching regions...", end="\r")
        try:
            ec2 = boto3.client("ec2", config=self.boto_config)
            response = ec2.describe_regions()
            return [r["RegionName"] for r in response.get("Regions", [])]
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to fetch regions: {e}")
            return []

    def _get_instances_in_region(self, region: str) -> list[Instance]:
        instances: list[Instance] = []
        try:
            ec2 = boto3.client("ec2", region_name=region, config=self.boto_config)

            paginator = ec2.get_paginator("describe_instances")
            page_iterator = paginator.paginate(
                Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
            )

            for page in page_iterator:
                for reservation in page.get("Reservations", []):
                    for inst in reservation.get("Instances", []):
                        name_tag: str | None = next(
                            (
                                t["Value"]
                                for t in inst.get("Tags", [])
                                if t["Key"] == "Name"
                            ),
                            None,
                        )
                        instances.append(
                            Instance(
                                name=name_tag,
                                public_ip=inst.get("PublicIpAddress"),
                                private_ip=inst.get("PrivateIpAddress"),
                                instance_id=inst.get("InstanceId", ""),
                                lifecycle=inst.get("InstanceLifecycle"),
                                region=region,
                            )
                        )
        except (ClientError, BotoCoreError):
            logger.warning(f"Failed to scan region {region}")

        return instances

    @override
    def get_instances(self) -> list[Instance]:
        regions = self._get_regions()
        if not regions:
            logger.error("Could not fetch regions.")
            return []

        total = len(regions)
        completed = 0
        lock = threading.Lock()
        all_instances: list[Instance] = []

        print(f"\033[KScanning 0/{total} regions...", end="\r")

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_region = {
                executor.submit(self._get_instances_in_region, region): region
                for region in regions
            }

            for future in concurrent.futures.as_completed(future_to_region):
                region = future_to_region[future]
                try:
                    instances = future.result()
                    if instances:
                        all_instances.extend(instances)
                except Exception:
                    logger.warning(f"Unexpected error scanning region {region}")

                with lock:
                    completed += 1
                    print(f"\033[KScanning {completed}/{total} regions...", end="\r")

        print()  # Newline after progress counter
        return all_instances
