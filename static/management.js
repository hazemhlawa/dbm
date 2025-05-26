document.addEventListener('DOMContentLoaded', function () {
    const addDatabaseForm = document.getElementById('addDatabaseForm');
    const databasesList = document.getElementById('databasesList');
    const alertContainer = document.getElementById('alert-container');

    // Function to create a new list item for a database
    function createDatabaseListItem(db, index) {
        const listItem = document.createElement('li');
        listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
        
        const dbInfo = document.createElement('span');
        dbInfo.textContent = `${db.host}:${db.port} - ${db.database}`;
        
        const buttonGroup = document.createElement('div');
        buttonGroup.className = 'btn-group';
        
        // Start button
        const startForm = document.createElement('form');
        startForm.action = '/management/start_database';
        startForm.method = 'post';
        const startHostInput = document.createElement('input');
        startHostInput.type = 'hidden';
        startHostInput.name = 'host';
        startHostInput.value = db.host;
        const startPortInput = document.createElement('input');
        startPortInput.type = 'hidden';
        startPortInput.name = 'port';
        startPortInput.value = db.port;
        const startButton = document.createElement('button');
        startButton.type = 'submit';
        startButton.className = 'btn btn-success btn-sm';
        startButton.textContent = 'Start';
        startForm.appendChild(startHostInput);
        startForm.appendChild(startPortInput);
        startForm.appendChild(startButton);
        buttonGroup.appendChild(startForm);
        
        // Stop button
        const stopForm = document.createElement('form');
        stopForm.action = '/management/stop_database';
        stopForm.method = 'post';
        const stopHostInput = document.createElement('input');
        stopHostInput.type = 'hidden';
        stopHostInput.name = 'host';
        stopHostInput.value = db.host;
        const stopPortInput = document.createElement('input');
        stopPortInput.type = 'hidden';
        stopPortInput.name = 'port';
        stopPortInput.value = db.port;
        const stopButton = document.createElement('button');
        stopButton.type = 'submit';
        stopButton.className = 'btn btn-danger btn-sm';
        stopButton.textContent = 'Stop';
        stopForm.appendChild(stopHostInput);
        stopForm.appendChild(stopPortInput);
        stopForm.appendChild(stopButton);
        buttonGroup.appendChild(stopForm);
        
        // Restart button
        const restartForm = document.createElement('form');
        restartForm.action = '/management/restart_database';
        restartForm.method = 'post';
        const restartHostInput = document.createElement('input');
        restartHostInput.type = 'hidden';
        restartHostInput.name = 'host';
        restartHostInput.value = db.host;
        const restartPortInput = document.createElement('input');
        restartPortInput.type = 'hidden';
        restartPortInput.name = 'port';
        restartPortInput.value = db.port;
        const restartButton = document.createElement('button');
        restartButton.type = 'submit';
        restartButton.className = 'btn btn-warning btn-sm';
        restartButton.textContent = 'Restart';
        restartForm.appendChild(restartHostInput);
        restartForm.appendChild(restartPortInput);
        restartForm.appendChild(restartButton);
        buttonGroup.appendChild(restartForm);
        
        // Remove button
        const removeForm = document.createElement('form');
        removeForm.action = '/management/remove_database';
        removeForm.method = 'post';
        const removeInput = document.createElement('input');
        removeInput.type = 'hidden';
        removeInput.name = 'index';
        removeInput.value = index;
        const removeButton = document.createElement('button');
        removeButton.type = 'submit';
        removeButton.className = 'btn btn-secondary btn-sm';
        removeButton.textContent = 'Remove';
        removeForm.appendChild(removeInput);
        removeForm.appendChild(removeButton);
        buttonGroup.appendChild(removeForm);
        
        listItem.appendChild(dbInfo);
        listItem.appendChild(buttonGroup);
        
        return listItem;
    }

    // Function to create an alert
    function createAlert(message, type) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.setAttribute('role', 'alert');
        alert.textContent = message;

        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'close';
        button.setAttribute('data-dismiss', 'alert');
        button.setAttribute('aria-label', 'Close');

        const span = document.createElement('span');
        span.setAttribute('aria-hidden', 'true');
        span.innerHTML = '&times;';

        button.appendChild(span);
        alert.appendChild(button);

        alertContainer.appendChild(alert);

        setTimeout(() => {
            alert.classList.remove('show');
            alert.classList.add('fade');
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);
    }

    // Add database form submission
    addDatabaseForm.addEventListener('submit', function (event) {
        event.preventDefault();
        
        const formData = new FormData(addDatabaseForm);
        const db = {
            host: formData.get('host'),
            port: formData.get('port'),
            user: formData.get('user'),
            password: formData.get('password'),
            database: formData.get('database')
        };

        fetch('/management/add_database', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const index = databasesList.childElementCount;
                const listItem = createDatabaseListItem(db, index);
                databasesList.appendChild(listItem);
                addDatabaseForm.reset();
                createAlert('Database added successfully!', 'success');
            } else {
                createAlert('Failed to add database: ' + data.message, 'danger');
            }
        })
        .catch(error => console.error('Error:', error));
    });

    // Handle form submissions for start, stop, restart, and remove actions
    databasesList.addEventListener('submit', function (event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);

        fetch(form.action, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                createAlert(data.message, 'success');
                if (form.action.endsWith('/remove_database')) {
                    form.closest('li').remove();
                }
            } else {
                createAlert(data.message, 'danger');
            }
        })
        .catch(error => console.error('Error:', error));
    });
});
