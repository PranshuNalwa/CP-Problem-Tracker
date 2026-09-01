from flask import Blueprint,request
from CP.models import USER,TOKEN_BLOCKLIST
from flask_jwt_extended import create_access_token,jwt_required,get_jwt
from werkzeug.security import check_password_hash,generate_password_hash
from CP import db,jwt

users=Blueprint("users",__name__)

@users.route('/signin',methods=['POST'])
def signin():
    data=request.get_json()
    username=data.get("username")
    password=data.get("password")
    cf_username=data.get("cf_username")
    if username is None or password is None or cf_username is None:
        return {"error": "missing required fields"}, 400
    hash_password=generate_password_hash(password,method='pbkdf2:sha256')
    statement=db.select(USER).filter_by(username=username)
    check=db.session.execute(statement).scalar_one_or_none()
    if check is None:
        user=USER(username=username,password=hash_password,cf_username=cf_username)
        db.session.add(user)
        db.session.commit()
        access_token=create_access_token(identity=str(user.id))
        return {"Token": access_token} , 200
    else:
        return {"error": "user already exist"}, 409

@users.route('/login',methods=['POST'])
def login():
    data=request.get_json()
    username=data.get("username")
    password=data.get("password")
    if username is None or password is None:
        return {"error": "missing required fields"}, 400
    statement=db.select(USER).filter_by(username=username)
    user=db.session.execute(statement).scalar_one_or_none()
    if user is not None:
        if check_password_hash(user.password,password):
            access_token=create_access_token(identity=str(user.id))
            return {"Token": access_token} , 200
    return {"error":"password or username wrong"}, 401

@users.route('/logout',methods=['POST'])
@jwt_required()
def logout():
    jti=get_jwt()['jti']
    expire_token=TOKEN_BLOCKLIST(jti=jti)
    db.session.add(expire_token)
    db.session.commit()
    return {"message":"logout succesful"}, 200
