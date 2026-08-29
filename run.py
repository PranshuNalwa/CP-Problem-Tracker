from flask import Flask ,request
from flask_sqlalchemy import SQLAlchemy

app=Flask(__name__)
db= SQLAlchemy()
app.config['SECRET_KEY']='asdfghjklouytdsxcvbnjkitrdxcvbnm'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"

db.init_app(app)

class USER(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
@app.route('/users',methods=['GET'])
def users():
    return "Welcome"

@app.route('/signin',methods=['POST'])
def signin():
    data=request.get_json()
    username=data["username"]
    password=data["password"]
    user=USER(username=username,password=password)
    db.session.add(user)
    db.session.commit()
    return {"username": user.username}, 201

