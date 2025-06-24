# Database Monitor (DBM)
#####HELLOOOOOOOOOOOOOOOO
A real-time database monitoring system built with Python Flask that provides comprehensive monitoring and management capabilities for MySQL databases.

## Features

- Real-time monitoring of database queries and performance metrics
- Database management (start/stop/restart)
- CPU, Memory, Disk, and Network usage monitoring
- Query statistics and visualization
- Database availability tracking
- User authentication
- Responsive dashboard with real-time updates

## Technologies Used

- Backend: Python Flask
- Frontend: HTML, CSS, JavaScript
- Database: MySQL
- Real-time Updates: Socket.IO
- Visualization: Chart.js
- CSS Framework: Bootstrap
- Process Monitoring: psutil

## Prerequisites

- Python 3.12+
- MySQL Server
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/dbm.git
cd dbm
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Update database configurations in `availdb.py`
2. Set the secret key in `app.py`
3. Configure MySQL connection parameters in `utils.py`

## Running the Application

### Local Development

```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Using Docker

1. Build the Docker image:
```bash
docker build -t dbm .
```

2. Run the container:
```bash
docker run -p 5000:5000 dbm
```

## Default Login

- Username: admin
- Password: admin123

## License

[MIT License](LICENSE)

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## Security Notice

This is a monitoring tool that requires access to database servers. Please ensure proper security measures are in place and never expose sensitive credentials.
Test pipeline trigger
Test pipeline trigger update
