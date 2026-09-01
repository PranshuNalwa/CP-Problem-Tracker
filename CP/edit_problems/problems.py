from flask import Blueprint,request,jsonify
from CP.models import PROBLEMS,USER
from flask_jwt_extended import jwt_required,get_jwt_identity
from CP import db,jwt
import requests

edit_problems=Blueprint("edit_problems",__name__) 

base_url="https://codeforces.com/api/"

@edit_problems.route('/users/<int:id>/problems',methods=['POST'])
@jwt_required()
def log_problem(id):
    data=request.get_json()
    title=data.get("title")
    rating=data.get("rating")
    tag=data.get("tag")
    solved=data.get("solved")
    if not title or rating is None or not tag or solved is None:
        return {"error": "missing required fields"}, 400
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

@edit_problems.route('/problems/<int:id>',methods=['PUT'])
@jwt_required()
def update_problem(id):
    ALLOWED_FIELDS = {"title", "rating", "tag", "solved"}
    data=request.get_json()
    statement=db.select(PROBLEMS).filter_by(id=id)
    problem=db.session.execute(statement).scalar_one_or_none()
    current_user_id=get_jwt_identity()
    if problem is None:
        return {"error":"problem doesnt exist"}, 404
    if int(current_user_id) != problem.user_id:
        return {"error":"Unauthorized access"},403
    for x in data:
        if x in ALLOWED_FIELDS:
            setattr(problem, x, data[x])
    db.session.commit()
    return {"message":"succesfully updated"}, 200

@edit_problems.route('/problems/<int:id>',methods=['PATCH'])
@jwt_required()
def mark_solved(id):
    data=request.get_json()
    statement=db.select(PROBLEMS).filter_by(id=id)
    problem=db.session.execute(statement).scalar_one_or_none()
    current_user_id=get_jwt_identity()
    if problem is None:
        return {"error":"id doesnt exist"},404 
    if int(current_user_id) != problem.user_id:
        return {"error":"Unauthorized access"},403
    solved=data.get('solved')
    if solved is None:
        return {"error": "missing required fields"}, 400
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

@edit_problems.route('/problems/<int:id>',methods=['DELETE'])
@jwt_required()
def delete_problem(id):
    statement=db.select(PROBLEMS).filter_by(id=id)
    problem=db.session.execute(statement).scalar_one_or_none()
    current_user_id=get_jwt_identity()
    if problem is None:
        return {"error":"invalid id"},404
    if int(current_user_id) != problem.user_id:
        return {"error":"Unauthorized access"},403
    db.session.delete(problem)
    db.session.commit()
    return {"message":"problem delete succesfully"},200

@edit_problems.route('/users/<int:id>/sync',methods=['POST','PATCH'])
@jwt_required()
def sync_problems(id):
    current_user_id=get_jwt_identity()
    if int(current_user_id) != id:
        return {"error":"Unauthorized access"},403
    statement=db.select(USER).filter_by(id=id)
    user=db.session.execute(statement).scalar_one_or_none()
    if user is None:
        return{"error":"invalid id"},404
    handle=user.cf_username
    url=f"{base_url}/user.status?handle={handle}"
    r= requests.get(url)
    if r.status_code != 200:
        return {"error":"Failed to retrive data"},r.status_code
    problems_data= r.json()
    if problems_data["status"] != "OK":
        return {"error":"Error from Codeforces API"},500
    for x in problems_data["result"]:
        p=x.get("problem")
        c_id=str(p.get("contestId"))
        c_id+=str(p.get("index"))
        stmt=db.select(PROBLEMS).filter_by(user_id=id,c_id=c_id)
        single_problem=db.session.execute(stmt).scalar_one_or_none()
        if single_problem is None:
            add_value(x,id)
        else:
            if not single_problem.solved:
                if p.get("verdict")=="OK":
                    single_problem.solved=1
    db.session.commit()
    return {"success":"Problems added"},201

def add_value(x,id):
    p=x["problem"]
    tag=p.get("tags")
    rating=p.get("rating")
    c_id=str(p.get("contestId"))
    c_id+=str(p.get("index"))
    if tag is None:
        tag=[]
    if rating is None:
        rating=0
    title=p["name"]
    solved=0
    if x["verdict"]=="OK":
        solved=1
    problem=PROBLEMS(user_id=id,c_id=c_id,title=title,rating=rating,tag=tag,solved=solved)
    db.session.add(problem)
    return