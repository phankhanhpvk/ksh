import re
from typing import Optional, Dict
from core.config import Config

class SSHConfigGenerator:
    def __init__(self, config: Config):
        self.config = config

    def _sanitize_alias(self, alias: str) -> str:
        if not alias or alias == "None":
            return ""
        # Replace spaces with hyphens and remove invalid chars
        return re.sub(r'[^a-zA-Z0-9.\-_]', '', alias.replace(' ', '-'))

    def generate_entry(self, instance: Dict) -> Optional[str]:
        # 1. Check Spot Exclusion
        if self.config.no_spot and instance.get("Lifecycle") == "spot":
            return None

        # Determine Alias
        name = instance.get("Name")
        instance_id = instance.get("Id")
        
        alias = self._sanitize_alias(name)
        if not alias:
            alias = instance_id

        # 2. Check Regex Exclusion
        if self.config.exclude_regex and re.search(self.config.exclude_regex, alias):
            return None

        # Determine Hostname (IP)
        public_ip = instance.get("PublicIp")
        private_ip = instance.get("PrivateIp")
        
        hostname = ""
        if self.config.private_ip:
            hostname = private_ip
        else:
            hostname = public_ip if public_ip else private_ip

        if not hostname:
            return None

        region = instance.get("Region", "Unknown")
        
        entry = [
            f"# Region: {region}",
            f"Host {alias}",
            f"    HostName {hostname}",
            f"    User {self.config.user}",
            f"    Port {self.config.port}"
        ]



        return "\n".join(entry) + "\n"
