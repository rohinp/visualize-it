import React from 'react';
import './VisualizationSelector.css';

const VisualizationSelector = ({ visualizations, selectedIndex, onSelect }) => {
    return (
        <div className="visualization-selector">
            <h2>Available Visualizations</h2>
            <div className="visualization-options">
                {visualizations.map((viz, index) => (
                    <div
                        key={index}
                        className={`visualization-option ${selectedIndex === index ? 'selected' : ''}`}
                        onClick={() => onSelect(index)}
                    >
                        <h3>{viz.title}</h3>
                        <p>Type: {viz.type}</p>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default VisualizationSelector;