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

// Setup User Activity Chart if the canvas exists
let userActivityChart;
const userActivityCanvas = document.getElementById('userActivityChart');
if (userActivityCanvas) {
    const ctx = userActivityCanvas.getContext('2d');
    userActivityChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [], // usernames
            datasets: [{
                label: 'Messages Sent',
                data: [], // message counts
                backgroundColor: 'rgba(88, 101, 242, 0.8)',
                borderColor: 'rgba(88, 101, 242, 1)',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',  // Horizontal bar chart
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Message Count'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Users'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Messages: ${context.raw}`;
                        }
                    }
                }
            },
            // Add animation configuration
            animation: {
                duration: 1000, // Animation duration in milliseconds
                easing: 'easeInOutQuad' // Smooth easing function
            },
            transitions: {
                active: {
                    animation: {
                        duration: 1000
                    }
                }
            }
        }
    });
}

// Store avatars separately to update them when available
let userAvatars = {};

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
    
    // Update the user activity bar chart (if the chart exists)
    if (userActivityChart && data.user_activity) {
        // Sort the user activity data by message count in descending order
        const sortedUserActivity = [...data.user_activity].sort((a, b) => b.message_count - a.message_count);
        
        // Store the avatar URLs in our mapping
        sortedUserActivity.forEach(user => {
            if (user.avatar) {
                userAvatars[user.username] = user.avatar;
            }
        });
        
        // Update the chart with user data
        userActivityChart.data.labels = sortedUserActivity.map(user => user.username);
        userActivityChart.data.datasets[0].data = sortedUserActivity.map(user => user.message_count);
        
        // Create avatars array matching the order of users in the chart
        const avatars = sortedUserActivity.map(user => user.avatar);
        
        // Update chart plugin data
        userActivityChart.options.plugins.customCanvasBackgroundImage = {
            avatars: avatars
        };
        
        userActivityChart.update();
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
    
    // Update the avatar in our mapping whenever a new message comes in
    userAvatars[data.user] = data.avatar;
});

// Add a plugin to display avatars next to the bars
Chart.register({
    id: 'customCanvasBackgroundImage',
    beforeDraw: (chart) => {
        if (chart.config.type !== 'bar' || chart.options.indexAxis !== 'y') return;
        
        const avatars = chart.options.plugins.customCanvasBackgroundImage?.avatars;
        if (!avatars) return;
        
        const {ctx, chartArea, scales} = chart;
        const yScale = scales.y;
        
        // For each data point
        avatars.forEach((avatar, index) => {
            const y = yScale.getPixelForValue(index);
            
            // Create an image element
            const img = new Image();
            img.src = avatar;
            
            // Draw the image when it's loaded
            img.onload = function() {
                ctx.save();
                // Draw circle avatar to the left of the bar
                ctx.beginPath();
                ctx.arc(chartArea.left - 25, y, 15, 0, Math.PI * 2);
                ctx.closePath();
                ctx.clip();
                ctx.drawImage(img, chartArea.left - 40, y - 15, 30, 30);
                ctx.restore();
            };
        });
    }
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