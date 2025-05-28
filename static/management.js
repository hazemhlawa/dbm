document.addEventListener('DOMContentLoaded', function() {
    const dbTableBody = document.getElementById('databasesTableBody');
    const addDatabaseForm = document.getElementById('addDatabaseForm');
    const testConnectionBtn = document.getElementById('testConnectionBtn');
    const saveDatabaseBtn = document.getElementById('saveDatabaseBtn');
    const alertContainer = document.getElementById('alert-container');
    
    // Load databases on page load
    loadDatabases();
    
    // Load and display databases
    function loadDatabases() {
        fetch('/management/databases')
            .then(response => response.json())
            .then(data => {
                renderDatabases(data.databases, data.current_db);
            })
            .catch(error => showAlert('Error loading databases: ' + error, 'danger'));
    }
    
    // Render databases in the table
    function renderDatabases(databases, currentDb) {
        dbTableBody.innerHTML = '';
        
        databases.forEach(db => {
            const row = document.createElement('tr');
            if (db.active) {
                row.classList.add('table-primary');
            }
            
            row.innerHTML = `
                <td>${db.name}</td>
                <td>${db.user}@${db.host}:${db.port}/${db.database || ''}</td>
                <td>${db.active ? '<span class="badge badge-success">Active</span>' : ''}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        ${!db.active ? 
                          `<button class="btn btn-outline-primary switch-db" data-name="${db.name}">
                              Switch To
                           </button>` : ''}
                        <button class="btn btn-outline-danger remove-db" data-name="${db.name}">
                            Remove
                        </button>
                        <button class="btn btn-outline-secondary service-btn" data-action="start" data-host="${db.host}" data-port="${db.port}">
                            Start
                        </button>
                        <button class="btn btn-outline-secondary service-btn" data-action="stop" data-host="${db.host}" data-port="${db.port}">
                            Stop
                        </button>
                        <button class="btn btn-outline-secondary service-btn" data-action="restart" data-host="${db.host}" data-port="${db.port}">
                            Restart
                        </button>
                    </div>
                </td>
            `;
            
            dbTableBody.appendChild(row);
        });
        
        // Add event listeners
        document.querySelectorAll('.switch-db').forEach(btn => {
            btn.addEventListener('click', switchDatabase);
        });
        
        document.querySelectorAll('.remove-db').forEach(btn => {
            btn.addEventListener('click', removeDatabase);
        });
        
        document.querySelectorAll('.service-btn').forEach(btn => {
            btn.addEventListener('click', manageService);
        });
    }
    
    // Switch database
    function switchDatabase(e) {
        const dbName = e.target.dataset.name;
        
        fetch('/management/databases', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                action: 'switch',
                name: dbName
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showAlert(`Switched to database: ${dbName}`, 'success');
                loadDatabases();
            } else {
                showAlert(data.message, 'danger');
            }
        })
        .catch(error => showAlert('Error switching database: ' + error, 'danger'));
    }
    
    // Remove database
    function removeDatabase(e) {
        const dbName = e.target.dataset.name;
        
        if (!confirm(`Are you sure you want to remove database ${dbName}?`)) {
            return;
        }
        
        fetch('/management/databases', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                action: 'remove',
                name: dbName
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showAlert(`Removed database: ${dbName}`, 'success');
                loadDatabases();
            } else {
                showAlert(data.message, 'danger');
            }
        })
        .catch(error => showAlert('Error removing database: ' + error, 'danger'));
    }
    
    // Test database connection
    testConnectionBtn.addEventListener('click', function() {
        const formData = new FormData(addDatabaseForm);
        const dbConfig = {
            host: formData.get('host'),
            port: formData.get('port'),
            user: formData.get('user'),
            password: formData.get('password'),
            database: formData.get('database')
        };
        
        fetch('/management/test_connection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(dbConfig)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showAlert('Connection successful!', 'success');
            } else {
                showAlert('Connection failed: ' + data.message, 'danger');
            }
        })
        .catch(error => showAlert('Error testing connection: ' + error, 'danger'));
    });
    
    // Save new database
    saveDatabaseBtn.addEventListener('click', function() {
        const formData = new FormData(addDatabaseForm);
        const dbConfig = {
            action: 'add',
            name: formData.get('name'),
            host: formData.get('host'),
            port: formData.get('port'),
            user: formData.get('user'),
            password: formData.get('password'),
            database: formData.get('database')
        };
        
        fetch('/management/databases', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(dbConfig)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showAlert('Database added successfully!', 'success');
                $('#addDatabaseModal').modal('hide');
                addDatabaseForm.reset();
                loadDatabases();
            } else {
                showAlert('Failed to add database: ' + data.message, 'danger');
            }
        })
        .catch(error => showAlert('Error adding database: ' + error, 'danger'));
    });
    
    // Manage database service
    function manageService(e) {
        const action = e.target.dataset.action;
        const host = e.target.dataset.host;
        const port = e.target.dataset.port;
        
        let endpoint;
        switch(action) {
            case 'start': endpoint = '/management/start_database'; break;
            case 'stop': endpoint = '/management/stop_database'; break;
            case 'restart': endpoint = '/management/restart_database'; break;
        }
        
        const formData = new FormData();
        formData.append('host', host);
        formData.append('port', port);
        
        fetch(endpoint, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            showAlert(data.message, data.status === 'success' ? 'success' : 'danger');
        })
        .catch(error => showAlert('Error managing service: ' + error, 'danger'));
    }
    
    // Show alert message
    function showAlert(message, type) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        `;
        
        alertContainer.prepend(alert);
        
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 150);
        }, 5000);
    }
});