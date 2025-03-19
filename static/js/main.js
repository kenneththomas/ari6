// Connect to SocketIO
var socket = io();

// Listen for metrics updates and update the metrics panel
socket.on('metrics_update', function(data) {
    document.getElementById('total_messages').innerText = data.total_messages;
    document.getElementById('total_reactions').innerText = data.total_reactions;
    document.getElementById('active_users').innerText = data.active_users;
});

// Listen for new messages and update the latest message panel
socket.on('new_message', function(data) {
    let contentDiv = document.getElementById('message_content');
    contentDiv.innerHTML = `
        <div class="avatar-container">
            <img src="${data.avatar}" alt="User Avatar">
            <strong>${data.user}</strong>
        </div>
        <div class="message-details">
            <p><strong>Channel:</strong> ${data.channel}</p>
            <p><strong>Time:</strong> ${new Date(data.timestamp).toLocaleString()}</p>
            <p><strong>Message:</strong> ${data.message}</p>
        </div>
    `;
});

// Functions to hide/show panels dynamically.
function removePanel(panelId) {
    let panel = document.getElementById(panelId);
    if (panel) {
        panel.style.display = 'none';
    }
}

function addPanel(panelId) {
    let panel = document.getElementById(panelId);
    if (panel) {
        panel.style.display = 'block';
    }
} 