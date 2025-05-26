document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const dataList = document.getElementById('data-list');

    socket.on('realtime_data', function(data) {
        const newRows = document.createDocumentFragment();
        data.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item[0]}</td>
                <td>${item[1]}</td>
                <td>${item[2]}</td>
                <td>${item[3]}</td>
                <td>${item[4]}</td>
                <td>${item[5]}</td>
                <td>${item[6]}</td>
                <td>${item[7]}</td>
                <td>${item[8]}</td>
                <td>${item[9].replace(/\n/g, "<br>")}</td>
            `;
            newRows.appendChild(row);
        });
        dataList.innerHTML = '';
        dataList.appendChild(newRows);
    });
});
