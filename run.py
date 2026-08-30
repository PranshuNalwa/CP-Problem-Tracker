from flask import Flask ,request,jsonify
from functools import wraps
from flask_sqlalchemy import SQLAlchemy

app=Flask(__name__)
db= SQLAlchemy()
app.config['SECRET_KEY']='asdfghjklouytdsxcvbnjkitrdxcvbnm'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"

#TODO: add jwt than using manual token
SESSION_TOKEN = "abcdefgh"

db.init_app(app)

#TODO: update the password security soon!
class USER(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    problems = db.relationship('PROBLEMS',backref="author",lazy=True)

class PROBLEMS(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    title= db.Column(db.String(20), nullable=False)
    rating= db.Column(db.Integer,nullable=False)
    tag=db.Column(db.String(20), nullable=False)
    solved=db.Column(db.Boolean, nullable=False)

with app.app_context():
    db.create_all()

def login_required(f):
    @wraps(f)
    def decorator_function(*args,**kwargs):
        auth_header = request.headers.get('Authorization')
        if auth_header != f"Bearer {SESSION_TOKEN}":
            return {"error": "unauthorized"}, 401
        return f(*args,**kwargs)
    return decorator_function

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
        return {"Token": SESSION_TOKEN} , 200
    else:
        return {"error": "user already exist"}, 409

@app.route('/login',methods=['POST'])
def login():
    data=request.get_json()
    username=data["username"]
    password=data["password"]
    statement=db.select(USER).filter_by(username=username)
    user=db.session.execute(statement).scalar_one_or_none()
    if user is not None:
        if user.password==password:
            return {"Token": SESSION_TOKEN} , 200
    return {"error":"password or username wrong"}, 401

#kinda broken right now , fix later after studying auth 
#login_required works!!
@app.route('/logout',methods=['POST'])
@login_required
def logout():
    data=request.get_json()
    check=data["logout"]
    if check=='yes':
        return {"message":"logout succesful"}, 200
    return {"login not done"}

@app.route('/users/<int:id>/problems',methods=['POST'])
@login_required
def log_problem(id):
    data=request.get_json()
    title=data["title"]
    rating=data["rating"]
    tag=data["tag"]
    solved=data["solved"]
    is_solved=False
    if solved:
        is_solved=True
    problem=PROBLEMS(user_id=id,title=title,rating=rating,tag=tag,solved=is_solved)
    db.session.add(problem)
    db.session.commit()
    return {"title" : problem.title,"tag": problem.tag, "rating": problem.rating,"solved": problem.solved}, 201

@app.route('/problems/<int:id>',methods=['PUT'])
@login_required
def update_problem(id):
    data=request.get_json()
    statement=db.select(PROBLEMS).filter_by(id=id)
    problem=db.session.execute(statement).scalar_one_or_none()
    if problem is not None:
        for x in data:
            setattr(problem, x, data[x])
        db.session.commit()
        return {"message":"succesfully updated"}, 200
    return {"error":"problem doesnt exist"}, 404

@app.route('/problems/<int:id>',methods=['GET'])
@login_required
def view_single_problem(id):
    statement=db.select(PROBLEMS).filter_by(id=id)
    problem=db.session.execute(statement).scalar_one_or_none()
    if problem is None:
        return {"error":"Problem Doesnt exist"}, 404
    return jsonify({
            "id":problem.id,
            "title":problem.title,
            "rating":problem.rating,
            "tag":problem.tag,
            "solved":problem.solved
    }),200

@app.route('/problems/<int:id>',methods=['PATCH'])
@login_required
def mark_solved(id):
    data=request.get_json()
    statement=db.select(PROBLEMS).filter_by(id=id)
    problem=db.session.execute(statement).scalar_one_or_none()
    if problem is None:
        return {"error":"id doesnt exist"},404 
    if data['solved'] == problem.solved:
        return{"message":"there were no changes"},204
    solved=data['solved']
    is_solved=False
    if solved:
        is_solved=True
    problem.solved=is_solved
    db.session.commit()
    return jsonify({
                "id":problem.id,
                "title":problem.title,
                "rating":problem.rating,
                "tag":problem.tag,
                "solved":problem.solved
        }),200

@app.route('/problems/<int:id>',methods=['DELETE'])
@login_required
def delete_problem(id):
    statement=db.select(PROBLEMS).filter_by(id=id)
    problem=db.session.execute(statement).scalar_one_or_none()
    if problem is None:
        return {"error":"invalid id"},404
    db.session.delete(problem)
    db.session.commit()
    return {"message":"problem delete succesfully"},200

@app.route('/users/<int:id>/problems',methods=['GET'])
@login_required
def filtering_and_view_all_problems(id):
    min_rating= int(request.args.get('minrating'))
    max_rating= int(request.args.get('maxrating'))
    tag= request.args.get('tag')
    status= request.args.get('status')
    statement=db.select(PROBLEMS).filter_by(user_id=id)
    if tag is not None:
        statement=statement.filter_by(tag=tag)
    if status is not None:
        statement=statement.filter_by(solved=(status=='solved'))
    if min_rating is not None:
        statement=statement.where(PROBLEMS.rating>=min_rating)
    if max_rating is not None:
        statement=statement.where(PROBLEMS.rating<=max_rating)
    problems=db.session.execute(statement).scalars().all()
    if not problems:
        return {"message": "no problem exist of this tag"} ,204
    data=[]
    for problem in problems:
        data.append({
            "id":problem.id,
            "title":problem.title,
            "rating":problem.rating,
            "tag":problem.tag,
            "solved":problem.solved
        })
    return data, 200

@app.route('/users/<int:id>/stats',methods=['GET'])
@login_required
def stats(id):
    statement=db.select(PROBLEMS.rating,db.func.count(PROBLEMS.id).label('total'),
                        db.func.sum(db.case((PROBLEMS.solved == True, 1), else_=0)).label('solved')
                        ).where(PROBLEMS.user_id==id).group_by(PROBLEMS.rating)
    results=db.session.execute(statement).all()
    stats = {}
    for row in results:
        stats[str(row.rating)] = {"total": row.total, "solved": row.solved}
    
    return stats, 200