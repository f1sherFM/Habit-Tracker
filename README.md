# 🎯 HabitTracker

> **A modern, dark-themed habit tracking web application built with Flask, SQLite, and Tailwind CSS.**

Track your daily habits with a beautiful and intuitive interface that helps you build consistency and achieve your goals.

![Habit Tracker](https://img.shields.io/badge/Status-Active-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-2.0+-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Preview

*Beautiful dark theme with modern glass-morphism design*

## Features

- **Modern Dark UI**: Clean, professional design with slate/zinc color scheme
- **Responsive Design**: Works perfectly on mobile and desktop
- **Habit Management**: Add and delete habits with ease
- **Progress Tracking**: Visual 7-day progress tracking with clickable circles
- **Real-time Updates**: Toggle completion status with smooth animations
- **Progress Bars**: Visual progress indicators for each habit
- **Glass-morphism Design**: Modern frosted glass card effects
- **User Authentication**: Login/Register with email/password or OAuth (Google/GitHub)
- **Personalized Experience**: Each user has their own habits

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login with OAuth support (Authlib)
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Icons**: Font Awesome
- **Frontend**: HTML5, Tailwind CSS, Font Awesome icons
- **JavaScript**: Vanilla JS for interactivity

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Clone/Download the Project

```bash
cd habit-tracker
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure OAuth (Optional)

To enable Google and GitHub login, you need to set up OAuth applications:

#### Google OAuth Setup:
1. Go to [Google Developer Console](https://console.developers.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Set Application type to "Web application"
6. Add authorized redirect URIs: `http://localhost:5000/auth/google`
7. Copy Client ID and Client Secret

#### GitHub OAuth Setup:
1. Go to [GitHub OAuth Apps](https://github.com/settings/applications/new)
2. Fill in application details
3. Set Authorization callback URL: `http://localhost:5000/auth/github`
4. Copy Client ID and Client Secret

#### Configure Environment Variables:
Create a `.env` file in the project root:

```env
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
SECRET_KEY=your_random_secret_key
```

### Step 5: Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

Open your web browser and navigate to:
```
http://localhost:5000
```

## Project Structure

```
habit-tracker/
│   app.py              # Main Flask application
│   requirements.txt    # Python dependencies
│   README.md          # This file
│
├───static/
│   │   style.css      # Additional CSS (if needed)
│   │
│   └───images/
│           hero-bg.jpg # Background images
│
└───templates/
        base.html      # Base template with navigation
        index.html     # Main dashboard template
```

## Usage

### Adding a Habit
1. Click the "Add Habit" button on the dashboard
2. Enter a habit name (required)
3. Optionally add a description
4. Click "Add Habit" to save

### Tracking Progress
1. Each habit card shows the last 7 days as clickable circles
2. Click on any day to toggle completion status
3. Green circles indicate completed days
4. Gray circles indicate incomplete days

### Deleting a Habit
1. Click the trash icon on any habit card
2. Confirm the deletion when prompted

## Database Schema

### Habits Table
- `id`: Primary key
- `name`: Habit name (max 100 characters)
- `description`: Optional description
- `created_at`: Timestamp of creation

### Habit Logs Table
- `id`: Primary key
- `habit_id`: Foreign key to habits table
- `date`: Date of the log entry
- `completed`: Boolean completion status

## Customization

### Changing the Color Scheme

Edit the CSS custom properties in `base.html`:

```css
:root {
    --primary-color: #3b82f6;  /* Change primary color */
    --success-color: #10b981;  /* Change success color */
    --danger-color: #ef4444;   /* Change danger color */
}
```

### Modifying the Database

The database is automatically created on first run. To reset:

1. Stop the application
2. Delete the `instance/habits.db` file
3. Run the application again

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Dashboard with all habits |
| POST | `/add-habit` | Add a new habit |
| POST | `/delete-habit/<id>` | Delete a habit |
| POST | `/toggle-habit/<id>/<date>` | Toggle completion status |

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance Features

- **Lazy Loading**: Habits are loaded efficiently
- **Minimal Dependencies**: Only essential packages
- **Optimized Images**: Compressed assets
- **Fast Database Queries**: Indexed database schema

## Security Features

- CSRF protection via Flask's secret key
- Input validation and sanitization
- SQL injection prevention via SQLAlchemy
- XSS protection through proper templating

## 👨‍💻 Developer

**Main Developer**: Darklord  
**Contact**: [@f1sherFM](https://t.me/f1sherFM) (Telegram)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📄 License

This project is open source and available under the MIT License.

## ⭐ Show your support

Give a ⭐️ if this project helped you!

## Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Change the port in app.py
app.run(debug=True, port=5001)  # Use different port
```

**Database Issues**
```bash
# Delete and recreate database
rm instance/habits.db
python app.py
```

**Missing Dependencies**
```bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the code comments
3. Check browser console for errors
4. Verify Python and dependencies versions

---

**Happy Habit Tracking!** 🎯