import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './ModelSelector.css';

const ModelSelector = ({ selectedModel, onModelSelect }) => {
    const [models, setModels] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchModels = useCallback(async () => {
        try {
            setLoading(true);
            const response = await axios.get('http://localhost:8000/api/models');
            if (response.data && response.data.models) {
                setModels(response.data.models);
                // If no model is selected and we have models, select the first one
                if (!selectedModel && response.data.models.length > 0) {
                    onModelSelect(response.data.models[0].name);
                }
            } else {
                setError('No models found');
            }
        } catch (err) {
            console.error('Error fetching models:', err);
            setError('Failed to fetch models');
        } finally {
            setLoading(false);
        }
    }, [selectedModel, onModelSelect]);

    useEffect(() => {
        fetchModels();
    }, [fetchModels]);

    // Initialize Materialize select on component mount
    useEffect(() => {
        if (!loading && models.length > 0) {
            const elems = document.querySelectorAll('select');
            // eslint-disable-next-line no-undef
            M.FormSelect.init(elems);
        }
    }, [loading, models]);

    const formatSize = (bytes) => {
        if (!bytes) return 'Unknown';
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
    };

    if (loading) {
        return (
            <div className="model-selector">
                <div className="progress">
                    <div className="indeterminate"></div>
                </div>
                <p className="center-align">Loading models...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="model-selector">
                <div className="card-panel red lighten-4">
                    <span className="red-text text-darken-4">{error}</span>
                </div>
            </div>
        );
    }

    return (
        <div className="model-selector">
            <h5>Select LLM Model</h5>
            <div className="input-field">
                <select
                    value={selectedModel || ''}
                    onChange={(e) => onModelSelect(e.target.value)}
                    className="browser-default"
                >
                    <option value="" disabled>Choose a model</option>
                    {models.map((model) => (
                        <option key={model.name} value={model.name}>
                            {model.name} ({formatSize(model.size)})
                        </option>
                    ))}
                </select>
            </div>
            <div className="model-info">
                {models.length > 0 ? (
                    <p className="grey-text">{models.length} models available</p>
                ) : (
                    <p className="red-text">No models found. Please make sure Ollama is running.</p>
                )}
            </div>
        </div>
    );
};

export default ModelSelector;