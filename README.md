# 🎯 HabitTracker

> **A modern, dark-themed habit tracking web application built with Flask, SQLite, and Tailwind CSS.**

Track your daily habits with a beautiful and intuitive interface that helps you build consistency and achieve your goals.

![Habit Tracker](https://img.shields.io/badge/Status-Active-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-2.0+-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

### 🎨 **Beautiful Modern Interface**
- **Dark Theme**: Professional slate/indigo color scheme with glass-morphism effects
- **Responsive Design**: Perfect experience on mobile, tablet, and desktop
- **Smooth Animations**: Floating elements and hover effects for engaging UX
- **Landing Page**: Professional landing page with feature showcase

### 📊 **Habit Management**
- **Easy Habit Creation**: Add habits with name and optional description
- **7-Day Progress Tracking**: Visual circles showing completion status for the last week
- **Real-time Updates**: Click any day to toggle completion with smooth animations
- **Progress Indicators**: Visual progress bars showing completion rates
- **Habit Deletion**: Remove habits with confirmation

### 🔐 **User Authentication**
- **Email/Password Registration**: Secure account creation and login
- **User Sessions**: Personalized experience with individual habit tracking
- **Password Security**: Hashed passwords using Werkzeug security
- **Session Management**: Secure login sessions with Flask-Login

### 📱 **Complete Website Experience**
- **Landing Page**: Beautiful hero section with feature highlights
- **About Us**: Company information and values
- **Our Mission**: Vision and purpose of the platform
- **Team Page**: Meet the developer (Darklord)
- **Contact Page**: Direct Telegram contact (@f1sherFM)
- **Legal Pages**: Privacy Policy and Terms of Service

## 🛠️ Technology Stack

### Backend
- **Flask** - Python web framework for routing and server logic
- **SQLAlchemy** - ORM for database operations
- **Flask-Login** - User session management
- **SQLite** - Lightweight database for data storage
- **Werkzeug** - Password hashing and security

### Frontend
- **HTML5** - Semantic markup structure
- **Tailwind CSS** - Utility-first CSS framework via CDN
- **JavaScript (Vanilla)** - Interactive functionality and AJAX
- **Font Awesome** - Beautiful icons and graphics
- **Google Fonts (Inter)** - Modern typography

### Design
- **Glass-morphism** - Modern frosted glass card effects
- **Dark Theme** - Professional slate/indigo color palette
- **Responsive Layout** - Mobile-first design approach
- **CSS Animations** - Smooth transitions and hover effects

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Clone the Project

```bash
git clone https://github.com/f1sherFM/Habit-Tracker.git
cd Habit-Tracker
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

### Step 4: Configure Environment (Optional)

Create a `.env` file for custom configuration:

```env
SECRET_KEY=your_random_secret_key_here
# OAuth credentials (currently disabled in UI)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
```

> **Note**: OAuth buttons are currently disabled in the UI. The app works perfectly with email/password authentication.

### Step 5: Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

Open your web browser and navigate to:
```
http://localhost:5000
```

## 📁 Project Structure

```
Habit-Tracker/
│
├── app.py                 # Main Flask application with all routes
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── .gitignore           # Git ignore rules
├── .env                 # Environment variables (create manually)
│
└── templates/           # HTML templates
    ├── landing.html     # Beautiful landing page
    ├── login.html       # User login form
    ├── register.html    # User registration form
    ├── index.html       # Main habit dashboard
    ├── about.html       # About us page
    ├── mission.html     # Our mission page
    ├── team.html        # Team page (featuring Darklord)
    ├── contact.html     # Contact page (@f1sherFM)
    ├── privacy.html     # Privacy policy
    └── terms.html       # Terms of service
```

## 🚀 Usage Guide

### Getting Started
1. **Visit the Landing Page** - Beautiful introduction to HabitTracker
2. **Create Account** - Register with email and password
3. **Login** - Access your personal dashboard
4. **Start Tracking** - Add your first habit and begin your journey

### Managing Habits
- **➕ Add New Habit**: Click "Add Habit" button, enter name and optional description
- **📊 Track Progress**: Click on any day circle to mark habit as complete/incomplete
- **📈 View Statistics**: See completion rates and 7-day progress for each habit
- **🗑️ Delete Habit**: Click trash icon to remove habits you no longer need

### Visual Indicators
- **🟢 Green Circles**: Completed days
- **⚪ Gray Circles**: Incomplete days
- **📊 Progress Bar**: Shows completion percentage for the week
- **🎯 Streak Counter**: Track your consistency over time

### Navigation
- **🏠 Dashboard**: Your main habit tracking interface
- **ℹ️ About**: Learn about HabitTracker's mission and values
- **👥 Team**: Meet the developer behind the project
- **📞 Contact**: Get in touch via Telegram (@f1sherFM)

## 🗄️ Database Schema

### Users Table
- `id`: Primary key (Integer)
- `email`: User email address (Unique, String 120)
- `password_hash`: Hashed password (String 128)
- `name`: User display name (String 100)
- `created_at`: Account creation timestamp (DateTime)

### Habits Table
- `id`: Primary key (Integer)
- `user_id`: Foreign key to users table (Integer)
- `name`: Habit name (String 100, required)
- `description`: Optional habit description (Text)
- `created_at`: Habit creation timestamp (DateTime)

### Habit Logs Table
- `id`: Primary key (Integer)
- `habit_id`: Foreign key to habits table (Integer)
- `date`: Date of the log entry (Date)
- `completed`: Boolean completion status (Boolean)
- **Unique Constraint**: One log per habit per date

## 🎨 Customization

### Color Scheme
The app uses a carefully crafted dark theme with:
- **Primary**: Indigo/Purple gradients (`#6366f1` to `#8b5cf6`)
- **Background**: Dark slate (`#0f172a` to `#1e1b4b`)
- **Cards**: Semi-transparent slate with glass effects
- **Success**: Green (`#10b981`)
- **Text**: Various slate shades for hierarchy

### Modifying Styles
All styles are embedded in HTML templates using Tailwind CSS classes. To customize:
1. Edit the `<style>` sections in template files
2. Modify Tailwind classes in HTML elements
3. Add custom CSS variables for consistent theming

### Database Management
- **Auto-creation**: Database is created automatically on first run
- **Location**: `instance/habits.db` (SQLite file)
- **Reset**: Delete the database file and restart the app
- **Backup**: Copy the `habits.db` file to save your data

## 🛣️ API Endpoints

### Public Routes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Landing page or redirect to dashboard if logged in |
| GET | `/login` | User login form |
| POST | `/login` | Process login credentials |
| GET | `/register` | User registration form |
| POST | `/register` | Create new user account |
| GET | `/about` | About us page |
| GET | `/mission` | Our mission page |
| GET | `/team` | Team page |
| GET | `/contact` | Contact information |
| GET | `/privacy` | Privacy policy |
| GET | `/terms` | Terms of service |

### Protected Routes (Login Required)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard` | Main habit tracking dashboard |
| POST | `/add-habit` | Create a new habit |
| POST | `/delete-habit/<id>` | Delete a specific habit |
| POST | `/toggle-habit/<id>/<date>` | Toggle habit completion for a date |
| GET | `/logout` | Log out current user |

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