import React, { useState, useEffect } from 'react';
import './PlotlyEditor.css';

const PlotlyEditor = ({ visualization, onUpdate }) => {
    const [dataJson, setDataJson] = useState('');
    const [layoutJson, setLayoutJson] = useState('');
    const [error, setError] = useState(null);
    const [isEditing, setIsEditing] = useState(false);
    const [autoApply, setAutoApply] = useState(false);

    useEffect(() => {
        if (visualization && visualization.plotlyData) {
            try {
                setDataJson(JSON.stringify(visualization.plotlyData, null, 2));
                setLayoutJson(JSON.stringify(visualization.plotlyLayout || {}, null, 2));
                setError(null);
            } catch (err) {
                setError(`Error parsing visualization data: ${err.message}`);
            }
        }
    }, [visualization]);

    const handleApplyChanges = () => {
        try {
            const parsedData = JSON.parse(dataJson);
            const parsedLayout = JSON.parse(layoutJson);

            onUpdate({
                plotlyData: parsedData,
                plotlyLayout: parsedLayout
            });

            setError(null);
            setIsEditing(false);
        } catch (err) {
            setError(`Invalid JSON: ${err.message}`);
        }
    };

    const handleDataChange = (e) => {
        setDataJson(e.target.value);
        setIsEditing(true);

        if (autoApply) {
            try {
                const parsedData = JSON.parse(e.target.value);
                const parsedLayout = JSON.parse(layoutJson);

                onUpdate({
                    plotlyData: parsedData,
                    plotlyLayout: parsedLayout
                });

                setError(null);
            } catch (err) {
                setError(`Invalid JSON: ${err.message}`);
            }
        }
    };

    const handleLayoutChange = (e) => {
        setLayoutJson(e.target.value);
        setIsEditing(true);

        if (autoApply) {
            try {
                const parsedData = JSON.parse(dataJson);
                const parsedLayout = JSON.parse(e.target.value);

                onUpdate({
                    plotlyData: parsedData,
                    plotlyLayout: parsedLayout
                });

                setError(null);
            } catch (err) {
                setError(`Invalid JSON: ${err.message}`);
            }
        }
    };

    if (!visualization || visualization.type !== 'plotly') {
        return <div className="card-panel blue-grey lighten-4 center-align">No Plotly visualization selected</div>;
    }

    return (
        <div className="plotly-editor">
            <div className="row">
                <div className="col s12">
                    <h5>Plotly JSON Editor</h5>
                    <div className="switch">
                        <label>
                            Manual Apply
                            <input
                                type="checkbox"
                                checked={autoApply}
                                onChange={() => setAutoApply(!autoApply)}
                            />
                            <span className="lever"></span>
                            Auto Apply
                        </label>
                    </div>

                    {!autoApply && (
                        <button
                            className="btn waves-effect waves-light green"
                            onClick={handleApplyChanges}
                            disabled={!isEditing}
                        >
                            <i className="material-icons left">check</i>
                            Apply Changes
                        </button>
                    )}

                    <button
                        className="btn waves-effect waves-light red right"
                        onClick={() => {
                            setDataJson(JSON.stringify(visualization.plotlyData, null, 2));
                            setLayoutJson(JSON.stringify(visualization.plotlyLayout || {}, null, 2));
                            setError(null);
                            setIsEditing(false);
                        }}
                    >
                        <i className="material-icons left">refresh</i>
                        Reset
                    </button>
                </div>
            </div>

            {error && (
                <div className="card-panel red lighten-4">
                    <span className="red-text text-darken-4">{error}</span>
                </div>
            )}

            <div className="row">
                <div className="col s12 m6">
                    <div className="input-field">
                        <h6>Data</h6>
                        <textarea
                            id="plotly-data-json"
                            className="materialize-textarea code-editor"
                            value={dataJson}
                            onChange={handleDataChange}
                            spellCheck="false"
                        ></textarea>
                    </div>
                </div>
                <div className="col s12 m6">
                    <div className="input-field">
                        <h6>Layout</h6>
                        <textarea
                            id="plotly-layout-json"
                            className="materialize-textarea code-editor"
                            value={layoutJson}
                            onChange={handleLayoutChange}
                            spellCheck="false"
                        ></textarea>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PlotlyEditor;