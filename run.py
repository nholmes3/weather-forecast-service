from app import create_app, scheduler

# create app
app = create_app()

if __name__ == '__main__':
    # Start the scheduler
    scheduler.start()
    app.run(host='0.0.0.0', port=8000, debug=True, use_reloader=False)
