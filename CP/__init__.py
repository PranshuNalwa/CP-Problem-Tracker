import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

db=SQLAlchemy()
jwt=JWTManager()


def create_app():
    app = Flask(__name__)

    load_dotenv()
    app.config['SECRET_KEY']=os.getenv("SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")

    db.init_app(app)
    jwt.init_app(app)

    from CP.users.auth import users
    from CP.edit_problems.problems import edit_problems
    from CP.view_problems.problems import view_problems

    app.register_blueprint(users)
    app.register_blueprint(edit_problems)
    app.register_blueprint(view_problems)

    with app.app_context():
        db.create_all()

    return app