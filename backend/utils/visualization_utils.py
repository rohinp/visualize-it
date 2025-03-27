import logging
import pandas as pd
from typing import Dict, Any

logger = logging.getLogger("visualize-it")


def generate_sample_plotly_visualizations():
    """Generate sample Plotly visualizations when parsing fails"""
    logger.info("Generating sample Plotly visualizations")
    return {
        "visualizations": [
            {
                "type": "plotly",
                "plotlyData": [
                    {
                        "x": ["A", "B", "C", "D"],
                        "y": [10, 15, 7, 12],
                        "type": "bar",
                        "name": "Sample Data",
                    }
                ],
                "plotlyLayout": {
                    "title": "Sample Bar Chart",
                    "xaxis": {"title": "Category"},
                    "yaxis": {"title": "Value"},
                },
                "title": "Sample Bar Chart",
                "description": "A sample bar chart showing placeholder data",
            },
            {
                "type": "plotly",
                "plotlyData": [
                    {
                        "values": [30, 70],
                        "labels": ["Group 1", "Group 2"],
                        "type": "pie",
                        "name": "Sample Pie Data",
                    }
                ],
                "plotlyLayout": {"title": "Sample Pie Chart"},
                "title": "Sample Pie Chart",
                "description": "A sample pie chart showing placeholder data",
            },
            {
                "type": "plotly",
                "plotlyData": [
                    {
                        "x": [1, 2, 3, 4, 5],
                        "y": [10, 15, 13, 17, 20],
                        "type": "scatter",
                        "mode": "lines+markers",
                        "name": "Sample Series",
                    }
                ],
                "plotlyLayout": {
                    "title": "Sample Line Chart",
                    "xaxis": {"title": "X"},
                    "yaxis": {"title": "Y"},
                },
                "title": "Sample Line Chart",
                "description": "A sample line chart showing placeholder data",
            },
        ]
    }


class VisualizationUtils:
    """
    Utility class for visualization generation and validation
    """
    def __init__(self):
        pass
    
    def is_valid_visualization(self, visualization: Dict[str, Any]) -> bool:
        """
        Check if a visualization is valid
        """
        try:
            # Check required fields
            if not all(key in visualization for key in ["title", "type"]):
                logger.warning("Visualization missing required fields")
                return False
            
            # For Plotly visualizations
            if visualization["type"] == "plotly":
                if "plotlyData" not in visualization or not isinstance(visualization["plotlyData"], list):
                    logger.warning("Plotly visualization missing plotlyData array")
                    return False
                
                if not visualization["plotlyData"]:
                    logger.warning("Plotly visualization has empty plotlyData array")
                    return False
                
                # Check each plotly data item
                for data_item in visualization["plotlyData"]:
                    if "type" not in data_item:
                        logger.warning("Plotly data item missing type")
                        return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating visualization: {str(e)}")
            return False
    
    def generate_dataframe_visualizations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate fallback visualizations from a dataframe
        """
        try:
            logger.info(f"Generating fallback visualizations for dataframe with shape {df.shape}")
            
            visualizations = []
            created_types = set()
            
            # Get column information
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()
            
            # Determine which visualization types to generate
            viz_types_to_generate = set()
            
            # If we have at least one numeric column, we can do bar charts
            if len(numeric_cols) >= 1:
                viz_types_to_generate.add('bar')
            
            # If we have at least two numeric columns, we can do scatter plots
            if len(numeric_cols) >= 2:
                viz_types_to_generate.add('scatter')
            
            # If we have categorical and numeric columns, we can do pie charts
            if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
                viz_types_to_generate.add('pie')
            
            # If we have datetime and numeric columns, we can do line charts
            if (len(datetime_cols) >= 1 or any('date' in col.lower() for col in df.columns)) and len(numeric_cols) >= 1:
                viz_types_to_generate.add('line')
            
            # 1. Bar chart
            if 'bar' in viz_types_to_generate and 'bar' not in created_types:
                try:
                    # If we have categorical columns, use the first one for x-axis
                    if categorical_cols:
                        cat_col = categorical_cols[0]
                        num_col = numeric_cols[0]
                        
                        # Aggregate data by the categorical column
                        agg_data = df.groupby(cat_col)[num_col].sum().reset_index()
                        
                        # Limit to top 10 categories if there are too many
                        if len(agg_data) > 10:
                            agg_data = agg_data.sort_values(by=num_col, ascending=False).head(10)
                        
                        visualizations.append({
                            "title": f"{num_col} by {cat_col}",
                            "description": f"Bar chart showing {num_col} grouped by {cat_col}",
                            "type": "plotly",
                            "plotlyData": [{
                                "type": "bar",
                                "x": agg_data[cat_col].tolist(),
                                "y": agg_data[num_col].tolist(),
                                "name": num_col,
                            }],
                            "plotlyLayout": {
                                "title": f"{num_col} by {cat_col}",
                                "xaxis": {"title": cat_col},
                                "yaxis": {"title": num_col},
                            },
                        })
                        
                        logger.info(f"Created bar chart visualization with {len(agg_data)} categories")
                        created_types.add('bar')
                    # If no categorical columns, use the first numeric column
                    elif numeric_cols:
                        visualizations.append({
                            "title": f"{numeric_cols[0]} Distribution",
                            "description": f"Bar chart showing the distribution of {numeric_cols[0]}",
                            "type": "plotly",
                            "plotlyData": [{
                                "type": "bar",
                                "x": df.index.tolist()[:50],  # Limit to first 50 rows
                                "y": df[numeric_cols[0]].tolist()[:50],
                                "name": numeric_cols[0],
                            }],
                            "plotlyLayout": {
                                "title": f"{numeric_cols[0]} Distribution",
                                "xaxis": {"title": "Index"},
                                "yaxis": {"title": numeric_cols[0]},
                            },
                        })
                        
                        logger.info("Created bar chart visualization with index as x-axis")
                        created_types.add('bar')
                except Exception as e:
                    logger.error(f"Error creating bar chart: {str(e)}")
            
            # 2. Scatter plot
            if 'scatter' in viz_types_to_generate and 'scatter' not in created_types and len(numeric_cols) >= 2:
                try:
                    visualizations.append({
                        "title": f"{numeric_cols[0]} vs {numeric_cols[1]}",
                        "description": f"Scatter plot showing the relationship between {numeric_cols[0]} and {numeric_cols[1]}",
                        "type": "plotly",
                        "plotlyData": [{
                            "type": "scatter",
                            "mode": "markers",
                            "x": df[numeric_cols[0]].head(50).tolist(),
                            "y": df[numeric_cols[1]].head(50).tolist(),
                            "name": f"{numeric_cols[0]} vs {numeric_cols[1]}",
                        }],
                        "plotlyLayout": {
                            "title": f"{numeric_cols[0]} vs {numeric_cols[1]}",
                            "xaxis": {"title": numeric_cols[0]},
                            "yaxis": {"title": numeric_cols[1]},
                        },
                    })
                    
                    logger.info(f"Created scatter plot visualization with {min(50, len(df))} data points")
                    created_types.add('scatter')
                except Exception as e:
                    logger.error(f"Error creating scatter plot: {str(e)}")
            
            # 3. Pie chart
            if 'pie' in viz_types_to_generate and 'pie' not in created_types:
                try:
                    cat_col = categorical_cols[0]
                    num_col = numeric_cols[0]
                    agg_data = df.groupby(cat_col)[num_col].sum().reset_index()
                    
                    # Limit to top 8 categories if there are too many
                    if len(agg_data) > 8:
                        agg_data = agg_data.sort_values(by=num_col, ascending=False).head(8)
                        
                    visualizations.append({
                        "title": f"{num_col} Distribution by {cat_col}",
                        "description": f"Pie chart showing the distribution of {num_col} across different {cat_col} categories",
                        "type": "plotly",
                        "plotlyData": [{
                            "type": "pie",
                            "labels": agg_data[cat_col].tolist(),
                            "values": agg_data[num_col].tolist(),
                            "name": num_col,
                        }],
                        "plotlyLayout": {
                            "title": f"{num_col} Distribution by {cat_col}",
                        },
                    })
                    
                    logger.info(f"Created pie chart visualization with {len(agg_data)} categories")
                    created_types.add('pie')
                except Exception as e:
                    logger.error(f"Error creating pie chart: {str(e)}")
            
            # 4. Line chart (time series)
            if 'line' in viz_types_to_generate and 'line' not in created_types:
                try:
                    # Check if we have a datetime column
                    date_col = None
                    if datetime_cols:
                        date_col = datetime_cols[0]
                    else:
                        # Try to find a column with 'date' in the name
                        date_cols = [col for col in df.columns if 'date' in col.lower()]
                        if date_cols:
                            date_col = date_cols[0]
                    
                    if date_col is not None:
                        # Sort by date
                        df_sorted = df.sort_values(by=date_col)
                        
                        visualizations.append({
                            "title": f"{numeric_cols[0]} Over Time",
                            "description": f"Line chart showing {numeric_cols[0]} over time",
                            "type": "plotly",
                            "plotlyData": [{
                                "type": "scatter",
                                "mode": "lines+markers",
                                "x": df_sorted[date_col].head(50).tolist(),
                                "y": df_sorted[numeric_cols[0]].head(50).tolist(),
                                "name": numeric_cols[0],
                            }],
                            "plotlyLayout": {
                                "title": f"{numeric_cols[0]} Over Time",
                                "xaxis": {"title": date_col},
                                "yaxis": {"title": numeric_cols[0]},
                            },
                        })
                        
                        logger.info(f"Created line chart visualization with {min(50, len(df_sorted))} data points")
                        created_types.add('line')
                except Exception as e:
                    logger.error(f"Error creating line chart: {str(e)}")
            
            # 5. Heatmap (if multiple numeric columns)
            if len(numeric_cols) >= 3 and 'heatmap' not in created_types:
                try:
                    # Use the first 3 numeric columns
                    heatmap_cols = numeric_cols[:3]
                    
                    # Create a pivot table
                    if len(categorical_cols) >= 2:
                        pivot_data = df.pivot_table(
                            index=categorical_cols[0],
                            columns=categorical_cols[1],
                            values=heatmap_cols[0],
                            aggfunc='mean'
                        ).fillna(0)
                        
                        # Convert to lists for plotly
                        z_data = pivot_data.values.tolist()
                        x_data = pivot_data.columns.tolist()
                        y_data = pivot_data.index.tolist()
                        
                        visualizations.append({
                            "title": f"{heatmap_cols[0]} Heatmap by {categorical_cols[0]} and {categorical_cols[1]}",
                            "description": f"Heatmap showing {heatmap_cols[0]} values across {categorical_cols[0]} and {categorical_cols[1]}",
                            "type": "plotly",
                            "plotlyData": [{
                                "type": "heatmap",
                                "z": z_data,
                                "x": x_data,
                                "y": y_data,
                                "colorscale": "Viridis",
                            }],
                            "plotlyLayout": {
                                "title": f"{heatmap_cols[0]} Heatmap",
                                "xaxis": {"title": categorical_cols[1]},
                                "yaxis": {"title": categorical_cols[0]},
                            },
                        })
                        
                        logger.info(f"Created heatmap visualization with shape {len(y_data)}x{len(x_data)}")
                        created_types.add('heatmap')
                except Exception as e:
                    logger.error(f"Error creating heatmap: {str(e)}")
            
            logger.info(f"Generated {len(visualizations)} fallback visualizations")
            return {"visualizations": visualizations}
        except Exception as e:
            logger.error(f"Error generating fallback visualizations: {str(e)}")
            return {"error": str(e), "visualizations": []}
