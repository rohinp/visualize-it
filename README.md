# Visualize-It

Visualize-It is an LLM-driven data visualization tool that automatically generates appropriate visualizations based on your data. Simply upload your data or paste text, and let the AI create beautiful, interactive visualizations that provide meaningful insights.

## Features

- **AI-Powered Visualization**: Uses Ollama (local LLM) to analyze data and generate appropriate visualizations
- **Intelligent Visualization Selection**: Automatically determines the most meaningful visualization types based on data characteristics
- **Data-Driven Approach**: Generates up to 8 visualizations, prioritizing quality and relevance over quantity
- **Multiple Input Methods**: Upload CSV files or paste text data
- **Interactive Visualizations**: Built with Plotly.js for interactive, responsive charts
- **Customization Options**: Edit visualization parameters and settings
- **Modern UI**: Clean interface built with React and Materialize CSS
- **Comprehensive Logging**: Detailed logging system for both client and server-side operations

## Technology Stack

### Frontend
- React 18
- Plotly.js for visualizations
- Materialize CSS for styling
- Axios for API communication

### Backend
- FastAPI (Python)
- Modular architecture with services, routes, models, and utilities
- Ollama for local LLM processing with AsyncClient for improved performance
- Pandas for data manipulation
- Intelligent fallback visualization generation when LLM is unavailable

## Getting Started

### Prerequisites

- Node.js (v14+)
- Python (v3.8+)
- Ollama installed locally ([Ollama Installation Guide](https://ollama.ai/))
- A code-focused LLM model (recommended: DeepSeek Coder v2)

### Installation

#### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install fastapi uvicorn pandas requests ollama-python asyncio pydantic
   ```

4. Start the backend server:
   ```
   uvicorn main:app --reload
   ```
   The server will run on http://localhost:8000

#### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm start
   ```
   The application will open in your browser at http://localhost:3000

## Usage

1. **Upload Data**: Use the file upload button to select a CSV file or paste text data
2. **Generate Visualizations**: Click "Generate Visualizations" to analyze your data
3. **Explore Results**: Navigate through the generated visualizations (up to 8 meaningful visualizations will be created)
4. **Customize**: Use the editor to modify visualization parameters if needed
5. **Download**: Use Plotly's built-in tools to download visualizations in various formats
6. **View Logs**: Access the logs section to view detailed information about application operations

## Development

### Logging System

The application includes a comprehensive logging system:
- Server logs are stored in `backend.log`
- Client logs are stored in `client.log`
- Logs can be viewed and cleared through the UI

### Project Structure

```
visualize-it/
├── backend/                # FastAPI backend
│   ├── main.py            # Main application entry point
│   ├── models/            # Data models
│   │   ├── settings.py    # Application configuration
│   │   └── visualization.py # Visualization data models
│   ├── routes/            # API routes
│   │   ├── api_routes.py  # Visualization API endpoints
│   │   └── logging_routes.py # Logging endpoints
│   ├── services/          # Business logic services
│   │   ├── ollama_service.py # Ollama API integration
│   │   ├── visualization_service.py # Visualization generation
│   │   └── logging_service.py # Logging functionality
│   ├── utils/             # Utility functions
│   │   ├── data_utils.py  # Data processing utilities
│   │   ├── visualization_utils.py # Visualization helpers
│   │   └── config_utils.py # Configuration utilities
│   └── backend.log        # Server-side logs
├── frontend/              # React frontend
│   ├── public/            # Static files
│   ├── src/               # React components and services
│   │   ├── components/    # UI components
│   │   └── services/      # Service modules including LoggingService
│   └── client.log         # Client-side logs
├── .gitignore             # Git ignore file
└── LICENSE                # MIT License
```

## Configuration

### Environment Variables

The application uses the following environment variables:

- `OLLAMA_API_URL`: URL for the Ollama API (default: http://localhost:11434)
- `OLLAMA_HOST`: Host for the Ollama AsyncClient (derived from OLLAMA_API_URL)
- `OLLAMA_API_TIMEOUT`: Timeout for Ollama API requests (default: 60 seconds)

### Recommended LLM Models

For optimal visualization generation, we recommend using code-focused LLM models:

- **DeepSeek Coder v2**: Excellent for generating code-based visualizations with Plotly
  ```bash
  # Pull the model with Ollama
  ollama pull deepseek-coder:latest
  ```

- **Other options**: CodeLlama, WizardCoder, or any other code-specialized model available in Ollama

These code-focused models perform better at generating structured JSON and understanding data visualization patterns compared to general-purpose models.

## Architecture

### Modular Backend Design

The backend has been refactored into a modular architecture to improve maintainability, testability, and separation of concerns:

- **Models**: Define data structures and application settings
  - `Settings`: Application configuration loaded from environment variables
  - `Visualization`: Data models for visualization requests and responses

- **Services**: Implement core business logic
  - `OllamaService`: Handles communication with the Ollama API
  - `VisualizationService`: Manages visualization generation from various data sources
  - `LoggingService`: Centralizes logging functionality

- **Routes**: Define API endpoints
  - `api_routes`: Visualization-related endpoints
  - `logging_routes`: Logging-related endpoints

- **Utils**: Provide helper functions
  - `DataUtils`: Data processing and transformation
  - `VisualizationUtils`: Visualization generation helpers
  - `ConfigUtils`: Configuration management

This architecture makes the codebase more maintainable and easier to extend with new features.

## Advanced Features

### Intelligent Visualization Selection

The application analyzes data characteristics to determine the most appropriate visualizations:

- Automatically identifies numeric, categorical, and date columns
- Evaluates cardinality of categorical data
- Considers row count and data distribution
- Selects from various visualization types including bar charts, scatter plots, pie charts, line charts, histograms, box plots, heatmaps, and bubble charts

### Fallback Mechanism

If the Ollama API is unavailable, the application falls back to a built-in visualization generator that:

1. Analyzes data characteristics
2. Determines appropriate visualization types
3. Generates visualizations using Plotly directly

This ensures the application remains functional even when the LLM service is down.

## Sample Datasets

Here are some sample datasets you can use to test the application:

### 1. Sales Data
```
Month,Sales,Expenses,Profit
January,45000,32000,13000
February,48000,33000,15000
March,51000,34000,17000
April,53000,36000,17000
May,58000,35000,23000
June,62000,37000,25000
July,65000,39000,26000
August,67000,41000,26000
September,70000,40000,30000
October,72000,42000,30000
November,75000,43000,32000
December,78000,45000,33000
```

### 2. Website Traffic Data
```
The website traffic analysis for Q1 2025 shows the following metrics:
- Total visitors: 125,000
- Unique visitors: 87,500
- Page views: 310,000
- Average time on site: 3.2 minutes
- Bounce rate: 42%

Traffic sources breakdown:
- Organic search: 45%
- Direct: 25%
- Social media: 18%
- Referral: 8%
- Email campaigns: 4%

Device distribution:
- Mobile: 58%
- Desktop: 32%
- Tablet: 10%

Top performing pages:
1. Homepage: 85,000 views
2. Product page: 65,000 views
3. Blog: 45,000 views
4. About us: 25,000 views
5. Contact: 15,000 views
```

### 3. Weather Data
```
Date,City,Temperature,Humidity,Precipitation
2025-03-01,London,12,78,0.2
2025-03-02,London,13,75,0.0
2025-03-03,London,11,80,0.5
2025-03-04,London,10,82,0.7
2025-03-05,London,9,85,1.2
2025-03-06,London,8,88,1.5
2025-03-07,London,10,84,0.8
2025-03-08,London,12,80,0.3
2025-03-09,London,14,75,0.0
2025-03-10,London,15,72,0.0
2025-03-01,Paris,14,70,0.0
2025-03-02,Paris,15,68,0.0
2025-03-03,Paris,16,65,0.0
2025-03-04,Paris,14,72,0.2
2025-03-05,Paris,13,75,0.4
2025-03-06,Paris,12,78,0.6
2025-03-07,Paris,13,76,0.3
2025-03-08,Paris,15,70,0.0
2025-03-09,Paris,17,65,0.0
2025-03-10,Paris,18,62,0.0
```

### 4. Regional Sales Data
```
Region,Category,Product,Units,Revenue
North,Electronics,Smartphone,1200,600000
North,Electronics,Laptop,800,720000
North,Electronics,Tablet,600,240000
North,Appliances,Refrigerator,300,150000
North,Appliances,Microwave,450,67500
South,Electronics,Smartphone,1500,750000
South,Electronics,Laptop,950,855000
South,Electronics,Tablet,700,280000
South,Appliances,Refrigerator,400,200000
South,Appliances,Microwave,600,90000
East,Electronics,Smartphone,1100,550000
East,Electronics,Laptop,750,675000
East,Electronics,Tablet,500,200000
East,Appliances,Refrigerator,250,125000
East,Appliances,Microwave,400,60000
West,Electronics,Smartphone,1300,650000
West,Electronics,Laptop,900,810000
West,Electronics,Tablet,650,260000
West,Appliances,Refrigerator,350,175000
West,Appliances,Microwave,500,75000
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.