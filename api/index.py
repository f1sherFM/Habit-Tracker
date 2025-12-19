from app import app

# This is required for Vercel
def handler(request):
    return app(request.environ, lambda status, headers: None)

# Export the app for Vercel
application = app

if __name__ == "__main__":
    app.run()