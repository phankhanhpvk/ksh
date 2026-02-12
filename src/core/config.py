import os
from typing import Dict
from dataclasses import dataclass, field

@dataclass
class Config:
    no_spot: bool
    exclude_regex: str
    private_ip: bool
    user: str
    port: str
    ec2_config_file: str = os.path.expanduser("~/.ssh/ksh_ec2_config")
    region_jump_hosts: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def load_from_env(cls) -> 'Config':
        # Parse per-region jump hosts
        jump_hosts = {}
        for key, value in os.environ.items():
            if key.startswith("KSH_JUMP_HOST_"):
                # Extract region part: KSH_JUMP_HOST_US_EAST_1 -> us-east-1
                region_part = key[len("KSH_JUMP_HOST_"):].lower().replace("_", "-")
                jump_hosts[region_part] = value

        return cls(
            no_spot=os.getenv("KSH_SYNC_NO_SPOT", "false").lower() == "true",
            private_ip=os.getenv("KSH_SYNC_PRIVATE_IP", "false").lower() == "true",
            exclude_regex=os.getenv("KSH_SYNC_EXCLUDE_REGEX"),
            user=os.getenv("KSH_SYNC_USER", os.getenv("USER")),
            port=os.getenv("KSH_SYNC_PORT", "22"),
            region_jump_hosts=jump_hosts
        )
