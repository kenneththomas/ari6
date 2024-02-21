import sqlite3
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Connect to your local SQLite database
conn = sqlite3.connect('logs/gato.db')  # replace with your database file path
cursor = conn.cursor()

# Query to select all messages from the database
cursor.execute("SELECT message FROM logs")  # replace 'your_table_name' with your table name
messages = cursor.fetchall()

# Convert messages to a single string
text = " ".join(message[0] for message in messages)

# List of words to exclude (blacklist)
blacklist = ['https','this','that','they','tenor','just','with','have','good','like','what','when','view']  # Add your own words here

# Generate the word cloud, excluding words less than 3 characters and in the blacklist
wordcloud = WordCloud(width = 800, height = 800, 
                background_color ='white', 
                stopwords = blacklist,
                min_word_length = 6).generate(text)

# Plot the WordCloud image                        
plt.figure(figsize = (8, 8), facecolor = None) 
plt.imshow(wordcloud) 
plt.axis("off") 
plt.tight_layout(pad = 0) 
  
plt.show()