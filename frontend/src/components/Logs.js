import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './Logs.css';

const Logs = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('server');
    const [lines, setLines] = useState(50);
    const [autoRefresh, setAutoRefresh] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [filteredLogs, setFilteredLogs] = useState([]);

    // Filter logs based on search term
    useEffect(() => {
        if (!searchTerm.trim()) {
            setFilteredLogs(logs);
            return;
        }

        const filtered = logs.filter(log =>
            log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
            log.level.toLowerCase().includes(searchTerm.toLowerCase()) ||
            log.timestamp.toLowerCase().includes(searchTerm.toLowerCase())
        );
        setFilteredLogs(filtered);
    }, [logs, searchTerm]);

    // Initialize Materialize components
    useEffect(() => {
        // Initialize tabs
        const tabsElem = document.querySelector('.tabs');
        if (tabsElem) {
            // eslint-disable-next-line no-undef
            M.Tabs.init(tabsElem);
        }
    }, []);

    const fetchLogs = useCallback(async () => {
        try {
            setError(null);
            setLoading(true);

            const endpoint = activeTab === 'server'
                ? 'http://localhost:8000/api/logs/server'
                : 'http://localhost:8000/api/logs/client';

            const response = await axios.get(endpoint, {
                params: { lines }
            });

            if (response.data && response.data.logs) {
                setLogs(response.data.logs);
            } else {
                setLogs([]);
            }
        } catch (err) {
            setError('Error fetching logs: ' + (err.response?.data?.detail || err.message));
            console.error('Error fetching logs:', err);
        } finally {
            setLoading(false);
        }
    }, [activeTab, lines]);

    // Function to clear logs
    const clearLogs = useCallback(async () => {
        try {
            setError(null);
            setLoading(true);

            const endpoint = activeTab === 'server'
                ? 'http://localhost:8000/api/logs/server/clear'
                : 'http://localhost:8000/api/logs/client/clear';

            await axios.post(endpoint);
            setLogs([]);
            console.log(`${activeTab} logs cleared`);
        } catch (err) {
            setError('Error clearing logs: ' + (err.response?.data?.detail || err.message));
            console.error('Error clearing logs:', err);
        } finally {
            setLoading(false);
        }
    }, [activeTab]);

    // Fetch logs on component mount and when activeTab or lines changes
    useEffect(() => {
        fetchLogs();
    }, [fetchLogs]);

    // Auto-refresh logs if enabled
    useEffect(() => {
        let interval;
        if (autoRefresh) {
            interval = setInterval(fetchLogs, 5000);
        }
        return () => clearInterval(interval);
    }, [autoRefresh, fetchLogs]);

    return (
        <div className="logs-container">
            <div className="logs-header">
                <h2>Application Logs</h2>
                <div className="logs-controls">
                    <div className="logs-tabs">
                        <button
                            className={`btn ${activeTab === 'server' ? 'active blue' : 'grey'}`}
                            onClick={() => setActiveTab('server')}
                        >
                            Server Logs
                        </button>
                        <button
                            className={`btn ${activeTab === 'client' ? 'active blue' : 'grey'}`}
                            onClick={() => setActiveTab('client')}
                        >
                            Client Logs
                        </button>
                    </div>
                    <div className="logs-options">
                        <div className="input-field inline">
                            <select
                                value={lines}
                                onChange={(e) => setLines(Number(e.target.value))}
                                className="browser-default"
                            >
                                <option value="10">10 lines</option>
                                <option value="50">50 lines</option>
                                <option value="100">100 lines</option>
                                <option value="500">500 lines</option>
                            </select>
                        </div>
                        <div className="switch">
                            <label>
                                Auto-refresh
                                <input
                                    type="checkbox"
                                    checked={autoRefresh}
                                    onChange={() => setAutoRefresh(!autoRefresh)}
                                />
                                <span className="lever"></span>
                            </label>
                        </div>
                        <button
                            className="btn-small waves-effect waves-light"
                            onClick={fetchLogs}
                        >
                            <i className="material-icons left">refresh</i>
                            Refresh
                        </button>
                        <button
                            className="btn-small waves-effect waves-light red"
                            onClick={clearLogs}
                        >
                            <i className="material-icons left">delete</i>
                            Clear Logs
                        </button>
                    </div>
                </div>
                <div className="input-field">
                    <input
                        type="text"
                        placeholder="Search logs..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            {error && (
                <div className="card-panel red lighten-4">
                    <span className="red-text text-darken-4">{error}</span>
                </div>
            )}

            {loading ? (
                <div className="center-align">
                    <div className="preloader-wrapper active">
                        <div className="spinner-layer spinner-blue-only">
                            <div className="circle-clipper left">
                                <div className="circle"></div>
                            </div>
                            <div className="gap-patch">
                                <div className="circle"></div>
                            </div>
                            <div className="circle-clipper right">
                                <div className="circle"></div>
                            </div>
                        </div>
                    </div>
                    <p>Loading logs...</p>
                </div>
            ) : (
                <div className="logs-table-container">
                    {filteredLogs.length === 0 ? (
                        <div className="center-align">
                            <p>No logs found</p>
                        </div>
                    ) : (
                        <table className="striped">
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Level</th>
                                    <th>Message</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredLogs.map((log, index) => (
                                    <tr key={index} className={`log-level-${log.level.toLowerCase()}`}>
                                        <td>{log.timestamp}</td>
                                        <td>{log.level}</td>
                                        <td>{log.message}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            )}
        </div>
    );
};

export default Logs;