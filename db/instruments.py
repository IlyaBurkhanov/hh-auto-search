from dataclasses import dataclass, field
from .core import Base


@dataclass
class RelatedMapping:
    model: Base.metadata
    mapping: dict = field(default_factory=dict)
    relate_table: str = field(init=False)

    def __post_init__(self):
        self.relate_table = self.model.__tablename__
