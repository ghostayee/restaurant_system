from app import create_app

app = create_app()

with app.app_context():
    from app import db
    try:
        db.engine.connect()
        print("✅ SUCCESS: Database Connected!")
        print("Database URL is working correctly.")
    except Exception as e:
        print("❌ FAILED to connect to database")
        print(e)