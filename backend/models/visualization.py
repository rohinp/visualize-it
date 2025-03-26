from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class PlotlyData(BaseModel):
    """Model for Plotly data specification"""
    type: str
    x: Optional[List[Any]] = None
    y: Optional[List[Any]] = None
    z: Optional[List[Any]] = None
    labels: Optional[List[str]] = None
    values: Optional[List[Any]] = None
    text: Optional[List[str]] = None
    marker: Optional[Dict[str, Any]] = None
    line: Optional[Dict[str, Any]] = None
    name: Optional[str] = None
    orientation: Optional[str] = None
    mode: Optional[str] = None
    colorscale: Optional[Union[str, List[List[Any]]]] = None
    hovertext: Optional[List[str]] = None
    hoverinfo: Optional[str] = None
    showscale: Optional[bool] = None
    
    class Config:
        extra = "allow"  # Allow extra fields not defined in the model


class PlotlyLayout(BaseModel):
    """Model for Plotly layout specification"""
    title: Optional[str] = None
    xaxis: Optional[Dict[str, Any]] = None
    yaxis: Optional[Dict[str, Any]] = None
    zaxis: Optional[Dict[str, Any]] = None
    width: Optional[int] = None
    height: Optional[int] = None
    margin: Optional[Dict[str, int]] = None
    legend: Optional[Dict[str, Any]] = None
    coloraxis: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "allow"  # Allow extra fields not defined in the model


class Visualization(BaseModel):
    """Model for a complete visualization"""
    title: str
    description: Optional[str] = None
    type: str = "plotly"  # Default to plotly, could also be "d3" for legacy support
    plotlyData: List[PlotlyData] = Field(default_factory=list)
    plotlyLayout: Optional[PlotlyLayout] = None
    
    class Config:
        extra = "allow"  # Allow extra fields not defined in the model


class VisualizationResponse(BaseModel):
    """Model for the response containing multiple visualizations"""
    visualizations: List[Visualization] = Field(default_factory=list)
