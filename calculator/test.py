from app import db, User
users = User.query.all()
for user in users:
    print(f"ID: {user.id}, Email: {user.email}")