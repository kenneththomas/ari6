// Connect to SocketIO
var socket = io();

// Global variable for storing message history for the last 10 minutes
let messageHistory = [];

// Setup Chart.js if the canvas exists
let messageChart;
const chartCanvas = document.getElementById('messageChart');
if (chartCanvas) {
    const ctx = chartCanvas.getContext('2d');
    messageChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [], // timestamps
            datasets: [{
                label: 'Total Messages',
                data: [], // message counts
                borderColor: 'rgba(88, 101, 242, 1)',
                backgroundColor: 'rgba(88, 101, 242, 0.1)',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            scales: {
                // Using a time scale for the x-axis; Chart.js will parse JavaScript Date objects
                x: {
                    type: 'time',
                    time: {
                        unit: 'minute',
                        displayFormats: {
                            minute: 'HH:mm:ss'
                        },
                        tooltipFormat: 'HH:mm:ss'
                    },
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Messages'
                    },
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: true
                }
            }
        }
    });
}

// Listen for metrics updates and update the metrics panel and the line chart.
socket.on('metrics_update', function(data) {
    // Update text values
    document.getElementById('total_messages').innerText = data.total_messages;
    document.getElementById('total_reactions').innerText = data.total_reactions;
    document.getElementById('active_users').innerText = data.active_users;
    
    // Update the message history for the line graph (if the chart exists)
    if (messageChart && data.message_history) {
        // Clear existing data
        messageHistory = [];
        
        // Process the message history data from the server
        data.message_history.forEach(point => {
            messageHistory.push({
                time: new Date(point[0]), // timestamp
                count: point[1]           // message count
            });
        });
        
        // Update the chart: the labels will be the timestamp and the dataset the message count
        messageChart.data.labels = messageHistory.map(point => point.time);
        messageChart.data.datasets[0].data = messageHistory.map(point => point.count);
        
        messageChart.update();
    }
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