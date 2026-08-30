from flask import Flask ,request
from flask_sqlalchemy import SQLAlchemy

app=Flask(__name__)
db= SQLAlchemy()
app.config['SECRET_KEY']='asdfghjklouytdsxcvbnjkitrdxcvbnm'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"

db.init_app(app)

#TODO: update the password security soon!
class USER(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
@app.route('/signin',methods=['POST'])
def signin():
    data=request.get_json()
    username=data["username"]
    password=data["password"]
    statement=db.select(USER).filter_by(username=username)
    check=db.session.execute(statement).scalar_one_or_none()
    if check is None:
        user=USER(username=username,password=password)
        db.session.add(user)
        db.session.commit()
        return {"username": user.username}, 201
    else:
        return {"username already exist": check.username}

@app.route('/login',methods=['POST'])
def login():
    data=request.get_json()
    username=data["username"]
    password=data["password"]
    statement=db.select(USER).filter_by(username=username)
    user=db.session.execute(statement).scalar_one_or_none()
    if user is not None:
        if user.password==password:
            return {"user_id":user.id, "username": user.username , "password":user.password}, 200
    return "password or username wrong"
