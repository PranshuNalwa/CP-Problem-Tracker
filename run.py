from flask import Flask ,request,jsonify
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import create_access_token,get_jwt_identity,jwt_required,JWTManager,get_jwt
from werkzeug.security import check_password_hash,generate_password_hash

app=Flask(__name__)
db= SQLAlchemy()
jwt=JWTManager(app)

app.config['SECRET_KEY']='asdfghjklouytdsxcvbnjkitrdxcvbnm'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"

db.init_app(app)

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

class TOKEN_BLOCKLIST(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    jti=db.Column(db.String(36),nullable=False,index=True)

with app.app_context():
    db.create_all()

@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload) :
    jti = jwt_payload["jti"]
    statement=db.select(TOKEN_BLOCKLIST).filter_by(jti=jti)
    token = db.session.execute(statement).scalar_one_or_none()
    return token is not None

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return {"Error":"User is logged out"},400


@app.route('/')
@app.route('/signin',methods=['POST'])
def signin():
    data=request.get_json()
    username=data["username"]
    password=data["password"]
    hash_password=generate_password_hash(password,method='pbkdf2:sha256')
    statement=db.select(USER).filter_by(username=username)
    check=db.session.execute(statement).scalar_one_or_none()
    if check is None:
        user=USER(username=username,password=hash_password)
        db.session.add(user)
        db.session.commit()
        access_token=create_access_token(identity=str(user.id))
        return {"Token": access_token} , 200
    else:
        return {"error": "user already exist"}, 409

@app.route('/login',methods=['POST'])
def login():
    data=request.get_json()
    username=data["username"]
    password=data["password"]
    statement=db.select(USER).filter_by(username=username)
    user=db.session.execute(statement).scalar_one_or_none()
    # current_user_id=get_jwt_identity()
    # if int(current_user_id) != user.user_id:
    #     return {"error":"Unauthorized access"},403
    if user is not None:
        if check_password_hash(user.password,password):
            access_token=create_access_token(identity=str(user.id))
            return {"Token": access_token} , 200
    return {"error":"password or username wrong"}, 401

#kinda broken right now , fix later after studying auth 
#login_required works!!
@app.route('/logout',methods=['POST'])
@jwt_required()
def logout():
    data=request.get_json()
    check=data["logout"]
    if check=='yes':
        jti=get_jwt()['jti']
        expire_token=TOKEN_BLOCKLIST(jti=jti)
        db.session.add(expire_token)
        db.session.commit()
        return {"message":"logout succesful"}, 200
    return {"login not done"}

@app.route('/users/<int:id>/problems',methods=['POST'])
@jwt_required()
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
    current_user_id=get_jwt_identity()
    if int(current_user_id) != id:
        return {"error":"Unauthorized access"},403   
    db.session.add(problem)
    db.session.commit()
    return {"title" : problem.title,"tag": problem.tag, "rating": problem.rating,"solved": problem.solved}, 201

@app.route('/problems/<int:id>',methods=['PUT'])
@jwt_required()
def update_problem(id):
    data=request.get_json()
    statement=db.select(PROBLEMS).filter_by(id=id)
    problem=db.session.execute(statement).scalar_one_or_none()
    current_user_id=get_jwt_identity()
    if int(current_user_id) != problem.user_id:
        return {"error":"Unauthorized access"},403
    if problem is not None:
        for x in data:
            setattr(problem, x, data[x])
        db.session.commit()
        return {"message":"succesfully updated"}, 200
    return {"error":"problem doesnt exist"}, 404

@app.route('/problems/<int:id>',methods=['GET'])
@jwt_required()
def view_single_problem(id):
    statement=db.select(PROBLEMS).filter_by(id=id)
    problem=db.session.execute(statement).scalar_one_or_none()
    current_user_id=get_jwt_identity()
    if int(current_user_id) != problem.user_id:
        return {"error":"Unauthorized access"},403
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
@jwt_required()
def mark_solved(id):
    data=request.get_json()
    statement=db.select(PROBLEMS).filter_by(id=id)
    problem=db.session.execute(statement).scalar_one_or_none()
    current_user_id=get_jwt_identity()
    if int(current_user_id) != problem.user_id:
        return {"error":"Unauthorized access"},403
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
@jwt_required()
def delete_problem(id):
    statement=db.select(PROBLEMS).filter_by(id=id)
    problem=db.session.execute(statement).scalar_one_or_none()
    current_user_id=get_jwt_identity()
    if int(current_user_id) != problem.user_id:
        return {"error":"Unauthorized access"},403
    if problem is None:
        return {"error":"invalid id"},404
    db.session.delete(problem)
    db.session.commit()
    return {"message":"problem delete succesfully"},200

@app.route('/users/<int:id>/problems',methods=['GET'])
@jwt_required()
def filtering_and_view_all_problems(id):
    min_rating= int(request.args.get('minrating'))
    max_rating= int(request.args.get('maxrating'))
    tag= request.args.get('tag')
    status= request.args.get('status')
    statement=db.select(PROBLEMS).filter_by(user_id=id)
    current_user_id=get_jwt_identity()
    if int(current_user_id) != id:
        return {"error":"Unauthorized access"},403   
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
@jwt_required()
def stats(id):
    current_user_id=get_jwt_identity()
    if int(current_user_id) != id:
        return {"error":"Unauthorized access"},403   
    statement=db.select(PROBLEMS.rating,db.func.count(PROBLEMS.id).label('total'),
                        db.func.sum(db.case((PROBLEMS.solved == True, 1), else_=0)).label('solved')
                        ).where(PROBLEMS.user_id==id).group_by(PROBLEMS.rating)
    results=db.session.execute(statement).all()
    stats = {}
    for row in results:
        stats[str(row.rating)] = {"total": row.total, "solved": row.solved}
    
    return stats, 200