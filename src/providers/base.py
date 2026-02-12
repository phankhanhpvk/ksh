from abc import ABC, abstractmethod
from typing import List, Dict

class CloudProvider(ABC):
    @abstractmethod
    def get_instances(self) -> List[Dict]:
        pass
