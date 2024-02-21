import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# Replace with the path to your database file
db_path = 'logs/gato.db'

# Connect to the SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Query to select timestamp from your messages table
# Replace 'your_table_name' with the actual name of your table
cursor.execute("SELECT timestamp FROM logs")
rows = cursor.fetchall()

# Create a DataFrame with timestamps
df = pd.DataFrame(rows, columns=['Timestamp'])

# Convert 'Timestamp' to datetime and extract date for daily aggregation
df['Timestamp'] = pd.to_datetime(df['Timestamp'])
df['Date'] = df['Timestamp'].dt.date

# Aggregate messages by date to assess daily engagement
daily_engagement = df.groupby('Date').size().reset_index(name='Message Count')

# Plotting daily engagement
plt.figure(figsize=(12, 6))
plt.plot(daily_engagement['Date'], daily_engagement['Message Count'], marker='o', linestyle='-')
plt.title('Daily Messages on Discord Server')
plt.xlabel('Date')
plt.ylabel('Number of Messages')
plt.xticks(rotation=45)
plt.grid(True)
plt.tight_layout()

# Show the plot
plt.show()