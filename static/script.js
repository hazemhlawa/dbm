document.addEventListener('DOMContentLoaded', function () {
    const socket = io.connect('http://' + document.domain + ':' + location.port);
    let updateInterval = 1000; // Default 1 second
    let lastUpdateTime = Date.now();
    let queryTypes = new Set(['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP', 'SHOW']);
    let typeColors = {
        'SELECT': 'rgba(59, 130, 246, 0.5)',
        'INSERT': 'rgba(16, 185, 129, 0.5)',
        'UPDATE': 'rgba(245, 158, 11, 0.5)',
        'DELETE': 'rgba(239, 68, 68, 0.5)',
        'CREATE': 'rgba(139, 92, 246, 0.5)',
        'ALTER': 'rgba(236, 72, 153, 0.5)',
        'DROP': 'rgba(107, 114, 128, 0.5)',
        'SHOW': 'rgba(217, 119, 6, 0.5)',
        'UNKNOWN': 'rgba(156, 163, 175, 0.5)'
    };

    // Generate random color with opacity
    function getRandomColor() {
        const rgb = Array.from({length: 3}, () => Math.floor(Math.random() * 256));
        return `rgba(${rgb.join(',')}, 0.5)`;
    }

    // Initialize DataTable
    let table = $('#queryTable').DataTable({
        paging: true,
        searching: false,
        ordering: true,
        info: true,
        pageLength: 10,
        columns: [
            { data: 'hostname' },
            { data: 'pid' },
            {
                data: 'query_type',
                render: function (data) {
                    return `<span class="badge" style="background-color: ${typeColors[data]?.replace('0.5', '1') || typeColors['UNKNOWN'].replace('0.5', '1')}">${data}</span>`;
                }
            },
            { data: 'query', render: $.fn.dataTable.render.text() },
            { data: 'executed_tool' },
            { data: 'query_time' },
            { data: 'execution_time_ms' },
            { data: 'user' },
            { data: 'database' },
            {
                data: null,
                render: function () {
                    return '<button class="view-btn text-indigo-500 hover:underline">View Details</button>';
                }
            }
        ],
        order: [[5, 'desc']]
    });

    // Initialize Chart
    let queryStatsChart;
    function initializeChart() {
        const ctx = document.getElementById('queryStatsChart').getContext('2d');
        queryStatsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: { display: true, text: 'Time (HH:MM:SS)' },
                        ticks: { maxRotation: 45, minRotation: 45 }
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        title: { display: true, text: 'Number of Queries' },
                        ticks: { stepSize: 1 }
                    }
                },
                plugins: {
                    legend: { position: 'top' },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y}`;
                            }
                        }
                    },
                    filler: { propagate: true }
                },
                elements: {
                    line: { tension: 0.2, fill: true }
                }
            }
        });
    }
    initializeChart();

    // Update chart datasets
    function updateChartDatasets() {
        const datasets = Array.from(queryTypes).map(type => ({
            label: type,
            data: [],
            backgroundColor: typeColors[type] || (typeColors[type] = getRandomColor()),
            borderColor: typeColors[type]?.replace('0.5', '1'),
            borderWidth: 1
        }));
        queryStatsChart.data.datasets = datasets;
    }
    updateChartDatasets();

    // Socket event handlers
    let pendingData = [];
    socket.on('realtime_data', function (data) {
        pendingData = data;
    });

    socket.on('daily_query_stats', function (stats) {
        console.log('Received daily_query_stats:', stats);
        document.getElementById('chartLoading').style.display = 'none';

        Object.values(stats).forEach(stat => {
            Object.keys(stat).forEach(type => queryTypes.add(type));
        });

        const filter = $('#queryTypeFilter');
        const currentOptions = new Set(filter.find('option').map((_, el) => el.value).get());
        queryTypes.forEach(type => {
            if (type && !currentOptions.has(type)) {
                filter.append(`<option value="${type}">${type}</option>`);
            }
        });

        updateChartDatasets();

        const seconds = Object.keys(stats).filter(key => key.includes(':')).sort();
        if (seconds.length === 0) {
            console.warn('No per-second stats available');
            queryStatsChart.data.labels = [];
            queryStatsChart.data.datasets.forEach(dataset => dataset.data = []);
            queryStatsChart.update();
            return;
        }

        const labels = seconds.slice(-60);
        queryStatsChart.data.labels = labels.map(label => label.split(' ')[1].substring(0, 8));
        queryStatsChart.data.datasets.forEach(dataset => {
            dataset.data = labels.map(second => stats[second][dataset.label] || 0);
        });
        queryStatsChart.update();
    });

    // Update table
    function updateTable() {
        if (pendingData.length > 0) {
            table.clear();
            table.rows.add(pendingData);
            table.draw();
            pendingData = [];
        }
        lastUpdateTime = Date.now();
        setTimeout(updateTable, updateInterval);
    }
    updateTable();

    // Refresh interval
    $('#refreshInterval').on('change', function () {
        updateInterval = parseInt($(this).val());
    });

    // Table row click
    $('#queryTable tbody').on('click', '.view-btn', function () {
        const data = table.row($(this).parents('tr')).data();
        $('#modalHostname').text(data.hostname);
        $('#modalPid').text(data.pid);
        $('#modalQueryType').text(data.query_type);
        $('#modalExecutedTool').text(data.executed_tool);
        $('#modalQuery').text(data.query);
        hljs.highlightElement($('#modalQuery')[0]);
        $('#modalQueryTime').text(data.query_time);
        $('#modalExecutionTime').text(data.execution_time_ms);
        $('#modalUser').text(data.user);
        $('#modalDatabase').text(data.database);
        $('#queryModal').removeClass('hidden');
    });

    $('#closeModal').on('click', function () {
        $('#queryModal').addClass('hidden');
    });

    $('#searchQuery').on('keyup', function () {
        const searchTerm = $(this).val().toLowerCase();
        table.rows().every(function () {
            const rowData = this.data();
            const query = rowData.query.toLowerCase();
            this.nodes().to$().toggle(query.includes(searchTerm));
        });
    });

    $('#queryTypeFilter').on('change', function () {
        const queryType = $(this).val();
        table.rows().every(function () {
            const rowData = this.data();
            const queryTypeUpper = rowData.query_type.toUpperCase();
            if (queryType === '') {
                this.nodes().to$().show();
            } else {
                this.nodes().to$().toggle(queryTypeUpper === queryType);
            }
        });
    });

    $('#darkModeToggle').on('click', function () {
        $('body').toggleClass('dark-mode');
        const icon = $(this).find('i');
        if ($('body').hasClass('dark-mode')) {
            icon.removeClass('fa-moon').addClass('fa-sun');
            $(this).html('<i class="fas fa-sun"></i> Light Mode');
        } else {
            icon.removeClass('fa-sun').addClass('fa-moon');
            $(this).html('<i class="fas fa-moon"></i> Dark Mode');
        }
    });
});