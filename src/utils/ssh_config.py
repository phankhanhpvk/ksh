import re

from core.config import Config
from providers.base import Instance


class SSHConfigGenerator:
    config: Config

    def __init__(self, config: Config):
        self.config = config

    def _sanitize_alias(self, alias: str) -> str:
        if not alias or alias == "None":
            return ""
        # Replace spaces with hyphens and remove invalid chars
        return re.sub(r"[^a-zA-Z0-9.\-_]", "", alias.replace(" ", "-"))

    def generate_entry(self, instance: Instance) -> str | None:

        # 1. Check Spot Exclusion
        if self.config.no_spot and instance.lifecycle == "spot":
            return None

        # Determine Alias
        alias = self._sanitize_alias(instance.name) if instance.name else ""
        if not alias:
            alias = instance.instance_id

        # 2. Check Regex Exclusion
        if self.config.exclude_regex and re.search(self.config.exclude_regex, alias):
            return None

        # Determine Hostname (IP)
        if self.config.private_ip:
            hostname = instance.private_ip
        else:
            hostname = instance.public_ip if instance.public_ip else instance.private_ip

        if not hostname:
            return None

        region = instance.region or "unknown"

        entry = [
            f"# Region: {region}",
            f"Host {alias}",
            f"    HostName {hostname}",
            f"    User {self.config.user}",
            f"    Port {self.config.port}",
            "    StrictHostKeyChecking no",
            "    UserKnownHostsFile /dev/null",
        ]

        return "\n".join(entry) + "\n"
