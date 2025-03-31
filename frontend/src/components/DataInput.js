import React, { useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import './DataInput.css';
import ModelSelector from './ModelSelector';

const DataInput = ({ onDataProcessed, setLoading }) => {
    const [text, setText] = useState('');
    const [lastProcessedText, setLastProcessedText] = useState('');
    const [error, setError] = useState('');
    const [serverStatus, setServerStatus] = useState(null);
    const [selectedModel, setSelectedModel] = useState('');
    const [isProcessing, setIsProcessing] = useState(false);

    // Check server and Ollama status on component mount
    useEffect(() => {
        checkServerStatus();
    }, []);

    const checkServerStatus = async () => {
        try {
            const response = await axios.get('http://localhost:8000/api/status');
            setServerStatus(response.data);
            console.log('Server status:', response.data);
        } catch (err) {
            console.error('Error checking server status:', err);

            // Try a fallback endpoint to determine if server is actually running
            try {
                // Try to access the models endpoint as a fallback
                const modelsResponse = await axios.get('http://localhost:8000/api/models');
                // If we can reach the models endpoint, the server is running
                setServerStatus({
                    server: 'ok',
                    ollama: modelsResponse.data && modelsResponse.data.length > 0 ? 'ok' : 'error'
                });
                console.log('Server appears to be running (fallback check)');
            } catch (fallbackErr) {
                // Both checks failed, server is likely down
                setServerStatus({
                    server: 'error',
                    ollama: 'unknown'
                });
            }
        }
    };

    const { getRootProps, getInputProps } = useDropzone({
        accept: {
            'text/csv': ['.csv'],
            'text/plain': ['.txt'],
        },
        onDrop: (acceptedFiles) => {
            const file = acceptedFiles[0];
            if (file) {
                processFile(file);
            }
        },
        disabled: isProcessing
    });

    const processFile = async (file) => {
        setError('');
        setLoading(true);
        setIsProcessing(true);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('model', selectedModel);

        try {
            console.log('Sending file to server...');
            const response = await axios.post('http://localhost:8000/api/process-csv', formData, {
                timeout: 60000,
            });
            console.log('Server response:', response.data);
            onDataProcessed(response.data);
        } catch (err) {
            console.error('Error processing file:', err);
            setError(`Error processing file: ${err.message}`);
        } finally {
            setLoading(false);
            setIsProcessing(false);
        }
    };

    const processTextData = async () => {
        if (!text.trim()) {
            setError('Please enter some text data');
            return;
        }

        setError('');
        setLoading(true);
        setIsProcessing(true);
        setLastProcessedText(text);

        const formData = new FormData();
        formData.append('text', text);
        formData.append('model', selectedModel);

        try {
            console.log('Sending text to server...');
            const response = await axios.post('http://localhost:8000/api/process-text', formData, {
                timeout: 60000,
            });
            console.log('Server response:', response.data);

            // Add the source text to the response for potential retries
            const responseWithSource = {
                ...response.data,
                sourceText: text
            };

            if (response.data.visualizations) {
                // Add source text to each visualization for retry purposes
                responseWithSource.visualizations = response.data.visualizations.map(viz => ({
                    ...viz,
                    sourceText: text
                }));
            }

            onDataProcessed(responseWithSource);
        } catch (err) {
            console.error('Error processing text:', err);
            setError(`Error processing text: ${err.message}`);
        } finally {
            setLoading(false);
            setIsProcessing(false);
        }
    };

    const handleRetryLastVisualization = async () => {
        if (!lastProcessedText) {
            setError('No previous text to retry');
            return;
        }

        setError('');
        setLoading(true);
        setIsProcessing(true);

        const formData = new FormData();
        formData.append('text', lastProcessedText);
        formData.append('model', selectedModel);

        try {
            console.log('Sending retry request to server...');
            const response = await axios.post('http://localhost:8000/api/retry-visualization', formData, {
                timeout: 60000,
            });
            console.log('Retry response:', response.data);

            // Add the source text to the response
            const responseWithSource = {
                ...response.data,
                sourceText: lastProcessedText
            };

            if (response.data.visualizations) {
                // Add source text to each visualization
                responseWithSource.visualizations = response.data.visualizations.map(viz => ({
                    ...viz,
                    sourceText: lastProcessedText
                }));
            }

            onDataProcessed(responseWithSource);
        } catch (err) {
            console.error('Error retrying visualization:', err);
            setError(`Error retrying visualization: ${err.message}`);
        } finally {
            setLoading(false);
            setIsProcessing(false);
        }
    };

    return (
        <div className="data-input card">
            <div className="card-content">
                <span className="card-title">Input Data</span>

                <ModelSelector
                    selectedModel={selectedModel}
                    onModelSelect={setSelectedModel}
                />

                <div className="input-field">
                    <textarea
                        id="data-text-input"
                        className="materialize-textarea"
                        placeholder="Paste your text data here..."
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                    ></textarea>
                    <label htmlFor="data-text-input" className={text ? "active" : ""}>Text Data</label>
                </div>

                <div className="button-container">
                    <button
                        className="btn waves-effect waves-light"
                        onClick={processTextData}
                        disabled={!text.trim() || !selectedModel || isProcessing}
                    >
                        <i className="material-icons left">send</i>
                        Process Text
                    </button>

                    {lastProcessedText && (
                        <button
                            className="btn waves-effect waves-light orange"
                            onClick={handleRetryLastVisualization}
                            disabled={isProcessing}
                        >
                            <i className="material-icons left">refresh</i>
                            Retry
                        </button>
                    )}
                </div>

                <div className="file-upload-container">
                    <p>Or upload a file:</p>
                    <div {...getRootProps()} className="dropzone">
                        <input {...getInputProps()} />
                        <p><i className="material-icons">cloud_upload</i> Drag & drop a CSV file here, or click to select</p>
                    </div>
                </div>

                {error && (
                    <div className="card-panel red lighten-4">
                        <span className="red-text text-darken-4">{error}</span>
                    </div>
                )}

                {serverStatus && (
                    <div className="server-status">
                        <p>
                            Server:
                            {serverStatus.server === 'ok'
                                ? <span className="green-text"> ✓ Connected</span>
                                : <span className="red-text"> ✗ Not connected</span>}
                        </p>
                        <p>
                            Ollama:
                            {serverStatus.ollama === 'ok'
                                ? <span className="green-text"> ✓ Running</span>
                                : <span className="red-text"> ✗ Not running</span>}
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DataInput;