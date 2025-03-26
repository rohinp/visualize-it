import io
import logging
import pandas as pd
import re
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger("visualize-it")

class DataUtils:
    """
    Utility class for data processing and transformation
    """
    def __init__(self):
        pass
    
    def extract_dataframe_from_file(self, file_content: bytes, filename: str) -> Optional[pd.DataFrame]:
        """
        Extract a pandas DataFrame from a file
        """
        try:
            # Determine file type from extension
            file_extension = filename.split('.')[-1].lower()
            
            # Create a file-like object from the bytes
            file_obj = io.BytesIO(file_content)
            
            # Parse based on file type
            if file_extension == 'csv':
                df = pd.read_csv(file_obj)
            elif file_extension == 'xlsx' or file_extension == 'xls':
                df = pd.read_excel(file_obj)
            elif file_extension == 'json':
                df = pd.read_json(file_obj)
            elif file_extension == 'txt':
                # Try to parse as CSV first, then as fixed-width
                try:
                    df = pd.read_csv(file_obj, sep=None, engine='python')
                except Exception:
                    # Reset the file pointer
                    file_obj.seek(0)
                    # Try as fixed-width
                    df = pd.read_fwf(file_obj)
            else:
                logger.error(f"Unsupported file extension: {file_extension}")
                return None
            
            logger.info(f"Successfully extracted dataframe with shape {df.shape} from {filename}")
            return df
        except Exception as e:
            logger.error(f"Error extracting dataframe from file {filename}: {str(e)}")
            return None
    
    def extract_dataframe_from_text(self, text: str) -> Optional[pd.DataFrame]:
        """
        Extract a pandas DataFrame from text
        """
        try:
            # Try to parse as CSV
            try:
                df = pd.read_csv(io.StringIO(text), sep=None, engine='python')
                if not df.empty:
                    logger.info(f"Successfully extracted CSV dataframe with shape {df.shape}")
                    return df
            except Exception as e:
                logger.info(f"Could not parse text as CSV: {str(e)}")
            
            # Try to parse as fixed-width
            try:
                df = pd.read_fwf(io.StringIO(text))
                if not df.empty:
                    logger.info(f"Successfully extracted fixed-width dataframe with shape {df.shape}")
                    return df
            except Exception as e:
                logger.info(f"Could not parse text as fixed-width: {str(e)}")
            
            # Try to extract a table-like structure from the text
            df = self._extract_table_from_text(text)
            if df is not None and not df.empty:
                logger.info(f"Successfully extracted table from text with shape {df.shape}")
                return df
            
            logger.error("Could not extract dataframe from text")
            return None
        except Exception as e:
            logger.error(f"Error extracting dataframe from text: {str(e)}")
            return None
    
    def _extract_table_from_text(self, text: str) -> Optional[pd.DataFrame]:
        """
        Extract a table-like structure from text
        """
        try:
            # Split text into lines
            lines = text.strip().split('\n')
            
            # Find lines that look like data (contain numbers or structured content)
            data_lines = []
            for line in lines:
                # Skip empty lines
                if not line.strip():
                    continue
                
                # Check if line contains numbers or looks like structured data
                if re.search(r'\d', line) or re.search(r'[,\t|]', line):
                    data_lines.append(line)
            
            if not data_lines:
                return None
            
            # Determine the delimiter (comma, tab, pipe)
            delimiters = [',', '\t', '|']
            delimiter_counts = {d: sum(line.count(d) for line in data_lines) for d in delimiters}
            delimiter = max(delimiter_counts, key=delimiter_counts.get)
            
            # If no clear delimiter, try to parse as space-separated
            if delimiter_counts[delimiter] == 0:
                delimiter = ' '
            
            # Parse the data lines
            data = []
            for line in data_lines:
                if delimiter == ' ':
                    # Split by multiple spaces for space-separated data
                    row = [item for item in re.split(r'\s+', line.strip()) if item]
                else:
                    row = [item.strip() for item in line.split(delimiter)]
                data.append(row)
            
            # Ensure all rows have the same number of columns
            max_cols = max(len(row) for row in data)
            for i, row in enumerate(data):
                if len(row) < max_cols:
                    data[i] = row + [''] * (max_cols - len(row))
            
            # Create dataframe
            df = pd.DataFrame(data[1:], columns=data[0] if len(data) > 1 else None)
            
            # If the first row doesn't look like headers, use default column names
            if len(data) > 1:
                first_row_is_numeric = all(cell.replace('.', '', 1).isdigit() if cell.replace('.', '', 1).replace('-', '', 1).isdigit() else False for cell in data[0] if cell)
                if first_row_is_numeric:
                    df = pd.DataFrame(data, columns=[f'Column{i+1}' for i in range(max_cols)])
            
            return df
        except Exception as e:
            logger.error(f"Error extracting table from text: {str(e)}")
            return None
    
    def get_dataframe_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get information about a dataframe
        """
        try:
            # Get basic info
            info = {
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "has_nulls": df.isnull().any().any(),
                "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
                "categorical_columns": df.select_dtypes(include=['object', 'category']).columns.tolist(),
                "datetime_columns": df.select_dtypes(include=['datetime']).columns.tolist(),
            }
            
            # Get summary statistics for numeric columns
            if info["numeric_columns"]:
                info["numeric_stats"] = df[info["numeric_columns"]].describe().to_dict()
            
            # Get value counts for categorical columns (limited to top 10)
            if info["categorical_columns"]:
                info["categorical_stats"] = {
                    col: df[col].value_counts().head(10).to_dict() 
                    for col in info["categorical_columns"]
                }
            
            return info
        except Exception as e:
            logger.error(f"Error getting dataframe info: {str(e)}")
            return {"error": str(e)}
