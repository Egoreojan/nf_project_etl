from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class TableConfig:
    name: str
    file_path: str
    table_name: str
    conflict_columns: List[str] = field(default_factory=list)
    date_columns: Dict[str, str] = field(default_factory=dict)  # column_name: date_format
    clear_before_load: bool = False
    custom_transform: Optional[Callable] = None
    encoding: Optional[str] = None

    def __post_init__(self):
        if not self.name or not self.file_path or not self.table_name:
            raise ValueError('name, file_path и table_name обязательны для TableConfig')