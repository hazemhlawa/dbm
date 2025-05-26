document.addEventListener('DOMContentLoaded', function () {
    const performanceContainer = document.getElementById('performanceContainer');

    if (!performanceContainer) {
        console.log('This is not the monitor page.');
        return;  // Exit if we are not on the monitor page
    }

    const socket = io();

    const cpuChartCtx = document.getElementById('cpuChart').getContext('2d');
    const memoryChartCtx = document.getElementById('memoryChart').getContext('2d');
    const diskChartCtx = document.getElementById('diskChart').getContext('2d');
    const networkChartCtx = document.getElementById('networkChart').getContext('2d');

    const cpuChart = new Chart(cpuChartCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'CPU Usage (%)',
                data: [],
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                x: {
                    beginAtZero: true
                },
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });

    const memoryChart = new Chart(memoryChartCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Memory Usage (%)',
                data: [],
                backgroundColor: 'rgba(255, 206, 86, 0.2)',
                borderColor: 'rgba(255, 206, 86, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                x: {
                    beginAtZero: true
                },
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });

    const diskChart = new Chart(diskChartCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Disk Usage (%)',
                data: [],
                backgroundColor: 'rgba(153, 102, 255, 0.2)',
                borderColor: 'rgba(153, 102, 255, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                x: {
                    beginAtZero: true
                },
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });

    const networkChart = new Chart(networkChartCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Network Usage (Bytes)',
                data: [],
                backgroundColor: 'rgba(255, 159, 64, 0.2)',
                borderColor: 'rgba(255, 159, 64, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                x: {
                    beginAtZero: true
                },
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    function updateChart(chart, label, data) {
        chart.data.labels.push(label);
        chart.data.datasets.forEach((dataset) => {
            dataset.data.push(data);
        });
        chart.update();
    }

    function fetchPerformanceData() {
        fetch('/monitor/performance_data')
            .then(response => response.json())
            .then(data => {
                const currentTime = new Date().toLocaleTimeString();
                updateChart(cpuChart, currentTime, data.cpu);
                updateChart(memoryChart, currentTime, data.memory);
                updateChart(diskChart, currentTime, data.disk);
                updateChart(networkChart, currentTime, data.network);
            })
            .catch(error => console.error('Error fetching performance data:', error));
    }

    socket.on('realtime_performance', function (data) {
        const currentTime = new Date().toLocaleTimeString();
        updateChart(cpuChart, currentTime, data.cpu);
        updateChart(memoryChart, currentTime, data.memory);
        updateChart(diskChart, currentTime, data.disk);
        updateChart(networkChart, currentTime, data.network);
    });

    // Initial load
    fetchPerformanceData();
    setInterval(fetchPerformanceData, 100000); // Fetch data every 5 seconds
});
