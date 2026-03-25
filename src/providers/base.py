from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Instance:
    name: str | None
    public_ip: str | None
    private_ip: str | None
    instance_id: str
    lifecycle: str | None
    region: str


class CloudProvider(ABC):
    @abstractmethod
    def get_instances(self) -> list[Instance]:
        pass
