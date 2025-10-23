import pandas as pd
from typing import List, Dict, Any

def normalize_to_dataframe(rows: List[Dict[str,Any]]):
    df = pd.DataFrame(rows)
    return df
