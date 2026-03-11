import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

def export_to_csv(data: List[Dict[str, Any]], filename_prefix: str = "census_export") -> Path:
    """
    Converts a list of dictionaries into a CSV file using pandas.
    Uses pathlib for cross-platform path management.
    """
    df = pd.DataFrame(data)
    
    # Create a temporary exports directory if it doesn't exist
    export_dir = Path("data/exports")
    export_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = export_dir / f"{filename_prefix}_{timestamp}.csv"
    
    df.to_csv(file_path, index=False)
    return file_path
