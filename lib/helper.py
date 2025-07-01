from typing import Any, Dict, Optional
from dateutil.parser import parse as parse_date

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Helper:

    @staticmethod
    def transform_dataframe(df: pd.DataFrame, date_columns: Dict[str, str]) -> pd.DataFrame:
        df_transformed = df.copy()
        
        for column, date_format in date_columns.items():
            if column in df_transformed.columns:
                if date_format == 'DD.MM.YYYY':
                    df_transformed[column] = df_transformed[column].apply(
                        lambda x: Helper.parse_date_safe(x, dayfirst=True)
                    )
                elif date_format == 'DD-MM-YYYY':
                    df_transformed[column] = df_transformed[column].apply(
                        lambda x: Helper.parse_date_safe(x, dayfirst=True)
                    )
                else:  # стандартный формат
                    df_transformed[column] = df_transformed[column].apply(
                        lambda x: Helper.parse_date_safe(x)
                    )
        
        return df_transformed
    
    @staticmethod
    def parse_date_safe(date_str: Any, dayfirst: bool = False) -> Optional[pd.Timestamp]:
        if pd.isna(date_str) or str(date_str).strip() == '':
            return None
        try:
            return parse_date(str(date_str), dayfirst=dayfirst)
        except Exception as e:
            logger.warning(f"Ошибка парсинга даты '{date_str}': {e}")
            return None