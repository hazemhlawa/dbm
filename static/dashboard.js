document.addEventListener('DOMContentLoaded', function () {
    const hostChartCtx = document.getElementById('hostChart').getContext('2d');
    const queryStatsChartCtx = document.getElementById('queryStatsChart').getContext('2d');
    const dbAvailabilityContainer = document.getElementById('dbAvailabilityContainer');
    const socket = io();

    socket.on('db_availability', function (availabilityStatus) {
        dbAvailabilityContainer.innerHTML = '';
        for (const host in availabilityStatus) {
            const hostStatus = availabilityStatus[host];
            const hostCard = document.createElement('div');
            hostCard.className = 'card mb-3';
            const hostCardBody = document.createElement('div');
            hostCardBody.className = 'card-body';

            const hostTitle = document.createElement('h5');
            hostTitle.className = 'card-title';
            hostTitle.textContent = host;

            const statusList = document.createElement('ul');
            statusList.className = 'list-group list-group-flush';

            for (const db in hostStatus) {
                const status = hostStatus[db];
                const statusItem = document.createElement('li');
                statusItem.className = 'list-group-item d-flex justify-content-between align-items-center';
                statusItem.textContent = db;

                const statusBadge = document.createElement('span');
                statusBadge.className = `badge ${status === 'Available' ? 'badge-success' : 'badge-danger'} badge-pill`;
                statusBadge.textContent = status;

                statusItem.appendChild(statusBadge);
                statusList.appendChild(statusItem);
            }

            hostCardBody.appendChild(hostTitle);
            hostCard.appendChild(hostCardBody);
            hostCard.appendChild(statusList);
            dbAvailabilityContainer.appendChild(hostCard);
        }
    });

    // Initial fetch for host stats
    fetch('/dashboard/query_history')
        .then(response => response.json())
        .then(queryHistory => {
            const hostStats = {};
            queryHistory.forEach(record => {
                const hostname = record[0];
                hostStats[hostname] = (hostStats[hostname] || 0) + 1;
            });

            const hosts = Object.keys(hostStats);
            const counts = Object.values(hostStats);

            new Chart(hostChartCtx, {
                type: 'bar',
                data: {
                    labels: hosts,
                    datasets: [{
                        label: 'Host Stats',
                        data: counts,
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        });

    // Initial fetch for query statistics
    fetch('/dashboard/query_stats')
        .then(response => response.json())
        .then(dailyQueryStats => {
            const totalQueries = Object.keys(dailyQueryStats).reduce((acc, date) => {
                Object.entries(dailyQueryStats[date]).forEach(([command, count]) => {
                    acc[command] = (acc[command] || 0) + count;
                });
                return acc;
            }, {});

            const labels = Object.keys(totalQueries);
            const sizes = Object.values(totalQueries);

            new Chart(queryStatsChartCtx, {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        data: sizes,
                        backgroundColor: labels.map(() => `rgba(${Math.floor(Math.random() * 256)}, ${Math.floor(Math.random() * 256)}, ${Math.floor(Math.random() * 256)}, 0.2)`),
                        borderColor: labels.map(() => `rgba(${Math.floor(Math.random() * 256)}, ${Math.floor(Math.random() * 256)}, ${Math.floor(Math.random() * 256)}, 1)`),
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top'
                        },
                        datalabels: {
                            color: 'black',
                            formatter: (value, context) => {
                                const sum = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = (value * 100 / sum).toFixed(2) + '%';
                                return percentage;
                            }
                        }
                    }
                },
                plugins: [ChartDataLabels]
            });
        });
});
