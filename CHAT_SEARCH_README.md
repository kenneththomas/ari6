# Chat Log Search Interface

A sleek, modern web interface for searching through your Discord chat logs stored in `logs/gato.db`.

## Features

- **Modern UI**: Beautiful gradient design with glassmorphism effects
- **Advanced Search**: Search through messages, senders, and channels
- **Multiple Filters**: Filter by sender, channel, and date range
- **Real-time Stats**: View total messages, unique users, and channels
- **Pagination**: Navigate through large result sets
- **Search Highlighting**: Search terms are highlighted in results
- **Responsive Design**: Works on desktop and mobile devices
- **Auto-search**: Results update automatically as you type (with debouncing)

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements_chat_search.txt
   ```

2. **Run the Application**:
   ```bash
   python chat_search.py
   ```

3. **Open in Browser**:
   Navigate to `http://localhost:5001`

## Usage

### Search Options

- **Search Messages**: Enter any text to search through message content, sender names, or channel names
- **Sender Filter**: Filter results to show only messages from specific users
- **Channel Filter**: Filter results to show only messages from specific channels
- **Date Range**: Set a date range to search within specific time periods
- **Results Limit**: Choose how many results to display per page (50, 100, 250, or 500)

### Features

- **Auto-search**: Results update automatically as you type (with a 500ms delay)
- **Pagination**: Navigate through large result sets with Previous/Next buttons
- **Clear Filters**: Reset all search criteria with one click
- **Statistics**: View total messages, unique users, and channels at the top
- **Search Highlighting**: Search terms are highlighted in yellow in the results

### Keyboard Shortcuts

- **Enter**: Perform search (when focused on search input)
- **Tab**: Navigate between form fields

## Database Schema

The application expects a SQLite database at `logs/gato.db` with the following table structure:

```sql
CREATE TABLE logs (
    sender text,
    channel text, 
    timestamp text,
    date text,
    hour text,
    message text
);
```

## API Endpoints

- `GET /` - Main search interface
- `GET /api/search` - Search API with query parameters
- `GET /api/stats` - Statistics API

## Customization

### Styling
- Edit `static/css/chat_search.css` to customize the appearance
- The design uses CSS custom properties for easy color customization

### Functionality
- Edit `static/js/chat_search.js` to modify search behavior
- Edit `chat_search.py` to add new API endpoints or modify search logic

## Troubleshooting

### Common Issues

1. **Database not found**: Ensure `logs/gato.db` exists and is readable
2. **Port already in use**: Change the port in `chat_search.py` line 108
3. **No results**: Check that your database contains data and search criteria are correct

### Performance Tips

- For large databases, consider adding database indexes on frequently searched columns
- The application uses pagination to handle large result sets efficiently
- Search queries are debounced to prevent excessive API calls

## Browser Compatibility

- Chrome/Chromium (recommended)
- Firefox
- Safari
- Edge

The interface uses modern CSS features like `backdrop-filter` which may not work in older browsers. 