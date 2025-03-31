import React, { useState, useEffect } from 'react';
import './services/LoggingService';
import DataInput from './components/DataInput';
import VisualizationDisplay from './components/VisualizationDisplay';
import VisualizationSelector from './components/VisualizationSelector';
import PlotlyEditor from './components/PlotlyEditor';
import Logs from './components/Logs';
import './App.css';

function App() {
  const [visualizationData, setVisualizationData] = useState(null);
  const [selectedVisualization, setSelectedVisualization] = useState(0);
  const [loading, setLoading] = useState(false);
  const [activeView, setActiveView] = useState('main'); // 'main' or 'logs'

  // Listen for visualization updates from the retry mechanism
  useEffect(() => {
    const handleRetryUpdate = (event) => {
      if (event.detail && event.detail.visualizations) {
        setVisualizationData(event.detail);
        setSelectedVisualization(0);
      }
    };

    window.addEventListener('visualization-update', handleRetryUpdate);

    return () => {
      window.removeEventListener('visualization-update', handleRetryUpdate);
    };
  }, []);

  const handleDataProcessed = (data) => {
    setVisualizationData(data);
    setSelectedVisualization(0);
  };

  const getCurrentVisualization = () => {
    if (!visualizationData || !visualizationData.visualizations || visualizationData.visualizations.length === 0) {
      return null;
    }
    return visualizationData.visualizations[selectedVisualization];
  };

  const handleEditorUpdate = (updates) => {
    if (!visualizationData || !visualizationData.visualizations) return;

    // Create a deep copy of the visualization data
    const updatedData = {
      ...visualizationData,
      visualizations: [...visualizationData.visualizations]
    };

    // Update the selected visualization with the new data
    updatedData.visualizations[selectedVisualization] = {
      ...updatedData.visualizations[selectedVisualization],
      ...updates
    };

    setVisualizationData(updatedData);
  };

  // Initialize Materialize components
  useEffect(() => {
    // Initialize tabs
    const tabsElem = document.querySelector('.tabs');
    if (tabsElem) {
      // eslint-disable-next-line no-undef
      M.Tabs.init(tabsElem);
    }
  }, []);

  return (
    <div className="App">
      <nav className="blue darken-2">
        <div className="nav-wrapper container">
          <a href="#!" className="brand-logo">Visualize-It</a>
          <ul className="right">
            <li className={activeView === 'main' ? 'active' : ''}>
              <a href="#!" onClick={() => setActiveView('main')}>Main</a>
            </li>
            <li className={activeView === 'logs' ? 'active' : ''}>
              <a href="#!" onClick={() => setActiveView('logs')}>Logs</a>
            </li>
          </ul>
        </div>
      </nav>

      {activeView === 'main' ? (
        <div className="container">
          <div className="row">
            <div className="col s12 m4">
              <DataInput
                onDataProcessed={handleDataProcessed}
                setLoading={setLoading}
              />
            </div>

            <div className="col s12 m8">
              {visualizationData && visualizationData.visualizations && (
                <div className="card">
                  <div className="card-content">
                    <div className="row mb-0">
                      <div className="col s12 m8">
                        <VisualizationSelector
                          visualizations={visualizationData.visualizations}
                          selectedIndex={selectedVisualization}
                          onSelect={setSelectedVisualization}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="card">
                <div className="card-content visualization-container">
                  {loading ? (
                    <div className="center-align">
                      <div className="preloader-wrapper big active">
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
                      <p>Processing data...</p>
                    </div>
                  ) : (
                    visualizationData && visualizationData.visualizations && (
                      <VisualizationDisplay
                        visualization={getCurrentVisualization()}
                      />
                    )
                  )}
                </div>
              </div>

              {visualizationData && getCurrentVisualization()?.type === 'plotly' && (
                <div className="card">
                  <div className="card-content">
                    <PlotlyEditor
                      visualization={getCurrentVisualization()}
                      onUpdate={handleEditorUpdate}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="container">
          <Logs />
        </div>
      )}
    </div>
  );
}

export default App;