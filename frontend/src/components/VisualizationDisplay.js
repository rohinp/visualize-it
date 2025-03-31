import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import Plot from 'react-plotly.js';
import axios from 'axios';
import './VisualizationDisplay.css';

const VisualizationDisplay = ({ visualization }) => {
    const svgRef = useRef(null);
    const [plotlyError, setPlotlyError] = useState(null);
    const [isRetrying, setIsRetrying] = useState(false);
    const [retryCount, setRetryCount] = useState(0);

    // Helper function to validate Plotly data
    const isValidPlotlyData = useCallback((data) => {
        if (!data) {
            console.error("Plotly data is undefined or null");
            return false;
        }

        if (!Array.isArray(data)) {
            console.error("Plotly data is not an array:", data);
            return false;
        }

        if (data.length === 0) {
            console.error("Plotly data array is empty");
            return false;
        }

        // Check if each trace has the minimum required properties
        for (const trace of data) {
            if (!trace.type) {
                console.error("Trace is missing 'type' property:", trace);
                return false;
            }

            // Validate based on chart type
            switch (trace.type) {
                case 'bar':
                case 'scatter':
                    if (!Array.isArray(trace.x) || !Array.isArray(trace.y)) {
                        console.error(`${trace.type} chart missing x or y arrays:`, trace);
                        return false;
                    }
                    break;
                case 'pie':
                    if (!Array.isArray(trace.values) || !Array.isArray(trace.labels)) {
                        console.error("Pie chart missing values or labels arrays:", trace);
                        return false;
                    }
                    break;
                default:
                    // For other chart types, just make sure it has some data
                    console.log(`Using chart type: ${trace.type}`);
            }
        }

        return true;
    }, []);

    // Helper function to create default layout if missing
    const getPlotlyLayout = useCallback((visualization) => {
        // Use provided layout or create a default one
        const defaultLayout = {
            title: visualization.title || 'Visualization',
            autosize: true,
            margin: { l: 50, r: 50, b: 50, t: 50, pad: 4 }
        };

        // If layout exists but is missing properties, merge with defaults
        if (visualization.plotlyLayout) {
            return { ...defaultLayout, ...visualization.plotlyLayout };
        }

        return defaultLayout;
    }, []);

    // Helper function to fix common Plotly data issues
    const sanitizePlotlyData = useCallback((data) => {
        if (!Array.isArray(data)) {
            console.error("Cannot sanitize non-array data:", data);
            return null;
        }

        return data.map(trace => {
            // Create a copy to avoid mutating the original
            const sanitizedTrace = { ...trace };

            // Ensure type is set
            if (!sanitizedTrace.type) {
                sanitizedTrace.type = 'scatter'; // Default to scatter
            }

            // Convert non-array x/y to arrays if needed
            if (sanitizedTrace.type === 'scatter' || sanitizedTrace.type === 'bar') {
                if (sanitizedTrace.x && !Array.isArray(sanitizedTrace.x)) {
                    sanitizedTrace.x = [sanitizedTrace.x];
                }
                if (sanitizedTrace.y && !Array.isArray(sanitizedTrace.y)) {
                    sanitizedTrace.y = [sanitizedTrace.y];
                }
            }

            // Ensure mode is set for scatter plots
            if (sanitizedTrace.type === 'scatter' && !sanitizedTrace.mode) {
                sanitizedTrace.mode = 'lines+markers';
            }

            return sanitizedTrace;
        });
    }, []);

    // Function to manually retry visualization generation
    const handleRetryVisualization = useCallback(async () => {
        if (!visualization || !visualization.sourceText) {
            console.error("Cannot retry: No source text available");
            return;
        }

        setIsRetrying(true);
        setRetryCount(prev => prev + 1);

        try {
            const formData = new FormData();
            formData.append('text', visualization.sourceText);

            console.log('Sending manual retry request to server...');

            const response = await axios.post('http://localhost:8000/api/retry-visualization', formData, {
                timeout: 60000,
            });

            console.log('Manual retry response:', response.data);

            // Reset error state if successful
            if (response.data.visualizations && response.data.visualizations.length > 0) {
                setPlotlyError(null);

                // Replace the current visualization with the new one
                // This is a bit of a hack since we can't directly update the parent's state
                // The parent component will need to handle this properly
                window.dispatchEvent(new CustomEvent('visualization-updated', {
                    detail: response.data
                }));
            } else {
                setPlotlyError("Retry failed to generate valid visualizations");
            }
        } catch (error) {
            console.error("Error retrying visualization:", error);
            setPlotlyError(`Retry error: ${error.message}`);
        } finally {
            setIsRetrying(false);
        }
    }, [visualization]);

    // Render line chart using D3
    const renderLineChart = useCallback((svg, visualization, width, height, margin) => {
        const data = visualization.data;
        console.log("Line chart data structure:", data);

        // For time series data with months
        if (data.length > 0 && data[0].Month) {
            renderTimeSeriesLineChart(svg, visualization, width, height, margin);
            return;
        }

        // For numeric x/y data
        const xKey = visualization.xAxis || 'x';
        const yKey = visualization.yAxis || 'y';

        // Create scales
        const x = d3.scaleLinear()
            .domain(d3.extent(data, d => {
                const xValue = typeof d[xKey] === 'number' ? d[xKey] : d.x;
                console.log("X value:", xValue);
                return xValue;
            }))
            .range([margin.left, width - margin.right]);

        const y = d3.scaleLinear()
            .domain([0, d3.max(data, d => {
                const yValue = typeof d[yKey] === 'number' ? d[yKey] : d.y;
                console.log("Y value:", yValue);
                return yValue;
            })])
            .nice()
            .range([height - margin.bottom, margin.top]);

        // Add x-axis
        svg.append('g')
            .attr('transform', `translate(0,${height - margin.bottom})`)
            .call(d3.axisBottom(x));

        // Add y-axis
        svg.append('g')
            .attr('transform', `translate(${margin.left},0)`)
            .call(d3.axisLeft(y));

        // Add the line
        svg.append('path')
            .datum(data)
            .attr('fill', 'none')
            .attr('stroke', '#4682b4')
            .attr('stroke-width', 2)
            .attr('d', d3.line()
                .x(d => x(typeof d[xKey] === 'number' ? d[xKey] : d.x))
                .y(d => y(typeof d[yKey] === 'number' ? d[yKey] : d.y))
            );

        // Add data points
        svg.selectAll('circle')
            .data(data)
            .join('circle')
            .attr('cx', d => x(typeof d[xKey] === 'number' ? d[xKey] : d.x))
            .attr('cy', d => y(typeof d[yKey] === 'number' ? d[yKey] : d.y))
            .attr('r', 4)
            .attr('fill', '#4682b4');

        // Add axis labels
        svg.append('text')
            .attr('x', width / 2)
            .attr('y', height - 10)
            .attr('text-anchor', 'middle')
            .text(xKey);

        svg.append('text')
            .attr('transform', 'rotate(-90)')
            .attr('x', -(height / 2))
            .attr('y', margin.left / 3)
            .attr('text-anchor', 'middle')
            .text(yKey);
    }, []);

    // Special handler for time series data with months
    const renderTimeSeriesLineChart = useCallback((svg, visualization, width, height, margin) => {
        const data = visualization.data;
        console.log("Time series data:", data);

        // Get all available metrics (columns) excluding Month
        const metrics = Object.keys(data[0]).filter(key => key !== 'Month');
        console.log("Available metrics:", metrics);

        // Create color scale for multiple lines
        const color = d3.scaleOrdinal()
            .domain(metrics)
            .range(d3.schemeCategory10);

        // Create scales
        const x = d3.scaleBand()
            .domain(data.map(d => d.Month))
            .range([margin.left, width - margin.right])
            .padding(0.1);

        const y = d3.scaleLinear()
            .domain([0, d3.max(data, d => Math.max(...metrics.map(metric => +d[metric])))])
            .nice()
            .range([height - margin.bottom, margin.top]);

        // Add x-axis
        svg.append('g')
            .attr('transform', `translate(0,${height - margin.bottom})`)
            .call(d3.axisBottom(x))
            .selectAll('text')
            .attr('transform', 'rotate(-45)')
            .style('text-anchor', 'end');

        // Add y-axis
        svg.append('g')
            .attr('transform', `translate(${margin.left},0)`)
            .call(d3.axisLeft(y));

        // Create line generator
        const line = d3.line()
            .x(d => x(d.Month) + x.bandwidth() / 2)
            .y(d => y(d.value))
            .curve(d3.curveMonotoneX);

        // Draw a line for each metric
        metrics.forEach(metric => {
            // Prepare data for this metric
            const metricData = data.map(d => ({
                Month: d.Month,
                value: +d[metric]
            }));

            // Add the line
            svg.append('path')
                .datum(metricData)
                .attr('fill', 'none')
                .attr('stroke', color(metric))
                .attr('stroke-width', 2)
                .attr('d', line);

            // Add data points
            svg.selectAll(`.circle-${metric}`)
                .data(metricData)
                .join('circle')
                .attr('class', `circle-${metric}`)
                .attr('cx', d => x(d.Month) + x.bandwidth() / 2)
                .attr('cy', d => y(d.value))
                .attr('r', 4)
                .attr('fill', color(metric));
        });

        // Add axis labels
        svg.append('text')
            .attr('x', width / 2)
            .attr('y', height - 10)
            .attr('text-anchor', 'middle')
            .text('Month');

        svg.append('text')
            .attr('transform', 'rotate(-90)')
            .attr('x', -(height / 2))
            .attr('y', margin.left / 3)
            .attr('text-anchor', 'middle')
            .text('Value');

        // Add legend
        const legend = svg.append('g')
            .attr('transform', `translate(${width - 120}, 20)`)
            .selectAll('.legend')
            .data(metrics)
            .join('g')
            .attr('class', 'legend')
            .attr('transform', (d, i) => `translate(0, ${i * 20})`);

        legend.append('rect')
            .attr('width', 15)
            .attr('height', 15)
            .attr('fill', d => color(d));

        legend.append('text')
            .attr('x', 20)
            .attr('y', 12)
            .text(d => d)
            .style('font-size', '12px');
    }, []);

    // Render bar chart using D3
    const renderBarChart = useCallback((svg, visualization, width, height, margin) => {
        const data = visualization.data;
        const xKey = visualization.xAxis || 'category';
        const yKey = visualization.yAxis || 'value';

        // Check if data has the right format
        console.log("Bar chart data:", data);

        // Create scales
        const x = d3.scaleBand()
            .domain(data.map(d => d[xKey]))
            .range([margin.left, width - margin.right])
            .padding(0.1);

        const y = d3.scaleLinear()
            .domain([0, d3.max(data, d => d[yKey])])
            .nice()
            .range([height - margin.bottom, margin.top]);

        // Add x-axis
        svg.append('g')
            .attr('transform', `translate(0,${height - margin.bottom})`)
            .call(d3.axisBottom(x))
            .selectAll('text')
            .attr('transform', 'rotate(-45)')
            .style('text-anchor', 'end');

        // Add y-axis
        svg.append('g')
            .attr('transform', `translate(${margin.left},0)`)
            .call(d3.axisLeft(y));

        // Add bars
        svg.selectAll('rect')
            .data(data)
            .join('rect')
            .attr('x', d => x(d[xKey]))
            .attr('y', d => y(d[yKey]))
            .attr('height', d => y(0) - y(d[yKey]))
            .attr('width', x.bandwidth())
            .attr('fill', '#4682b4');

        // Add axis labels
        svg.append('text')
            .attr('x', width / 2)
            .attr('y', height - margin.bottom / 3)
            .attr('text-anchor', 'middle')
            .text(xKey);

        svg.append('text')
            .attr('transform', 'rotate(-90)')
            .attr('x', -(height / 2))
            .attr('y', margin.left / 3)
            .attr('text-anchor', 'middle')
            .text(yKey);
    }, []);

    // Render pie chart using D3
    const renderPieChart = useCallback((svg, visualization, width, height) => {
        const data = visualization.data;
        console.log("Pie chart data:", data);

        // Define pie chart properties
        const radius = Math.min(width, height) / 2 - 40;
        const labelKey = visualization.labelKey || 'label';
        const valueKey = visualization.valueKey || 'value';

        // Create pie layout
        const pie = d3.pie()
            .value(d => d[valueKey])
            .sort(null);

        // Create arc generator
        const arc = d3.arc()
            .innerRadius(0)
            .outerRadius(radius);

        // Create color scale
        const color = d3.scaleOrdinal(d3.schemeCategory10);

        // Create group element for the pie chart
        const g = svg.append('g')
            .attr('transform', `translate(${width / 2}, ${height / 2})`);

        // Create pie slices
        const slices = g.selectAll('path')
            .data(pie(data))
            .join('path')
            .attr('d', arc)
            .attr('fill', (d, i) => color(i))
            .attr('stroke', 'white')
            .style('stroke-width', '2px');

        // Add labels
        const labelArc = d3.arc()
            .innerRadius(radius * 0.6)
            .outerRadius(radius * 0.6);

        g.selectAll('text')
            .data(pie(data))
            .join('text')
            .attr('transform', d => `translate(${labelArc.centroid(d)})`)
            .attr('dy', '0.35em')
            .attr('text-anchor', 'middle')
            .text(d => d.data[labelKey])
            .style('font-size', '12px')
            .style('fill', 'white');

        // Add title
        svg.append('text')
            .attr('x', width / 2)
            .attr('y', 30)
            .attr('text-anchor', 'middle')
            .style('font-size', '16px')
            .text(visualization.title || 'Pie Chart');
    }, []);

    // Render scatter plot using D3
    const renderScatterPlot = useCallback((svg, visualization, width, height, margin) => {
        const data = visualization.data;
        console.log("Scatter plot data:", data);

        const xKey = visualization.xAxis || 'x';
        const yKey = visualization.yAxis || 'y';

        // Create scales
        const x = d3.scaleLinear()
            .domain(d3.extent(data, d => d[xKey]))
            .nice()
            .range([margin.left, width - margin.right]);

        const y = d3.scaleLinear()
            .domain(d3.extent(data, d => d[yKey]))
            .nice()
            .range([height - margin.bottom, margin.top]);

        // Add x-axis
        svg.append('g')
            .attr('transform', `translate(0,${height - margin.bottom})`)
            .call(d3.axisBottom(x));

        // Add y-axis
        svg.append('g')
            .attr('transform', `translate(${margin.left},0)`)
            .call(d3.axisLeft(y));

        // Add data points
        svg.selectAll('circle')
            .data(data)
            .join('circle')
            .attr('cx', d => x(d[xKey]))
            .attr('cy', d => y(d[yKey]))
            .attr('r', 5)
            .attr('fill', '#4682b4')
            .attr('opacity', 0.7);

        // Add axis labels
        svg.append('text')
            .attr('x', width / 2)
            .attr('y', height - margin.bottom / 3)
            .attr('text-anchor', 'middle')
            .text(xKey);

        svg.append('text')
            .attr('transform', 'rotate(-90)')
            .attr('x', -(height / 2))
            .attr('y', margin.left / 3)
            .attr('text-anchor', 'middle')
            .text(yKey);
    }, []);

    // Render D3 visualization based on type
    const renderD3Visualization = useCallback((type, svg, visualization, width, height, margin) => {
        // Clear previous visualization
        d3.select(svg).selectAll("*").remove();

        switch (type) {
            case 'line':
                renderLineChart(svg, visualization, width, height, margin);
                break;
            case 'bar':
                renderBarChart(svg, visualization, width, height, margin);
                break;
            case 'pie':
                renderPieChart(svg, visualization, width, height);
                break;
            case 'scatter':
                renderScatterPlot(svg, visualization, width, height, margin);
                break;
            default:
                console.error(`Unsupported visualization type: ${type}`);
                break;
        }
    }, [renderLineChart, renderBarChart, renderPieChart, renderScatterPlot]);

    // Effect for rendering D3 visualizations
    useEffect(() => {
        if (!visualization || visualization.type === 'plotly') return;

        const svg = svgRef.current;
        if (!svg) return;

        try {
            const width = 600;
            const height = 400;
            const margin = { top: 50, right: 50, bottom: 50, left: 50 };

            renderD3Visualization(visualization.type, svg, visualization, width, height, margin);
        } catch (error) {
            console.error('Error rendering visualization:', error);
        }
    }, [visualization, renderD3Visualization]);

    // If no visualization is provided, show a message
    if (!visualization) {
        return (
            <div className="visualization-container center-align">
                <h2>No Visualization</h2>
                <p>No visualization data available</p>
            </div>
        );
    }

    // If there's an error in the visualization data
    if (visualization.error) {
        return (
            <div className="visualization-container error">
                <h2 className="red-text">Error Rendering Visualization</h2>
                <p>{visualization.error}</p>
            </div>
        );
    }

    // For Plotly visualizations
    if (visualization.type === 'plotly') {
        console.log("Rendering Plotly visualization:", visualization);

        // Check if plotlyData exists and is valid
        if (!visualization.plotlyData) {
            return (
                <div className="visualization-container error">
                    <h2 className="red-text">Error Rendering Visualization</h2>
                    <p>Missing Plotly data in visualization</p>
                </div>
            );
        }

        // Validate and sanitize data
        if (!isValidPlotlyData(visualization.plotlyData)) {
            console.error("Invalid Plotly data structure:", visualization.plotlyData);
            return (
                <div className="visualization-container error">
                    <h2 className="red-text">Error Rendering Visualization</h2>
                    <p>Invalid data structure for Plotly visualization. Check console for details.</p>
                </div>
            );
        }

        // Get layout with defaults
        const layout = getPlotlyLayout(visualization);

        // Sanitize data to fix common issues
        const sanitizedData = sanitizePlotlyData(visualization.plotlyData);

        if (!sanitizedData) {
            return (
                <div className="visualization-container error">
                    <h2 className="red-text">Error Rendering Visualization</h2>
                    <p>Failed to process visualization data</p>
                </div>
            );
        }

        return (
            <div className="visualization-container">
                <h2>{visualization.title || 'Visualization'}</h2>
                {plotlyError ? (
                    <div className="error-message">
                        <p className="red-text">{plotlyError}</p>
                        <button
                            onClick={handleRetryVisualization}
                            disabled={isRetrying}
                            className={isRetrying ? "retry-button loading" : "retry-button"}
                        >
                            {isRetrying ? "Retrying..." : "Retry Visualization"}
                        </button>
                        {retryCount > 0 && (
                            <p className="retry-count grey-text">Retry attempts: {retryCount}</p>
                        )}
                    </div>
                ) : (
                    <Plot
                        data={sanitizedData}
                        layout={layout}
                        style={{ width: '100%', height: '500px' }}
                        useResizeHandler={true}
                        onError={(err) => {
                            console.error("Plotly rendering error:", err);
                            setPlotlyError(`Plotly error: ${err.message || 'Unknown error'}`);
                        }}
                        onInitialized={(figure) => {
                            console.log("Plotly initialized successfully", figure);
                        }}
                    />
                )}
            </div>
        );
    }

    // For D3 visualizations
    return (
        <div className="visualization-container">
            <h2>{visualization.title}</h2>
            <svg ref={svgRef} width="100%" height="500" preserveAspectRatio="xMidYMid meet" viewBox="0 0 600 400" />
        </div>
    );
};

export default VisualizationDisplay;