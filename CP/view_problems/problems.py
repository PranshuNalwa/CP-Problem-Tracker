from flask import Blueprint,request,jsonify
from CP.models import PROBLEMS
from flask_jwt_extended import jwt_required,get_jwt_identity
from CP import db,jwt

view_problems=Blueprint("view_problems",__name__)

@view_problems.route('/problems/<int:id>',methods=['GET'])
@jwt_required()
def view_single_problem(id):
    statement=db.select(PROBLEMS).filter_by(id=id)
    problem=db.session.execute(statement).scalar_one_or_none()
    current_user_id=get_jwt_identity()
    if problem is None:
        return {"error":"Problem Doesnt exist"}, 404
    if int(current_user_id) != problem.user_id:
        return {"error":"Unauthorized access"},403
    return jsonify({
            "id":problem.id,
            "title":problem.title,
            "rating":problem.rating,
            "tag":problem.tag,
            "solved":problem.solved
    }),200

@view_problems.route('/users/<int:id>/problems',methods=['GET'])
@jwt_required()
def filtering_and_view_all_problems(id):
    current_user_id=get_jwt_identity()
    if int(current_user_id) != id:
        return {"error":"Unauthorized access"},403   
    min_rating= request.args.get('minrating')
    max_rating= request.args.get('maxrating')
    tag= request.args.get('tag')
    status= request.args.get('status')
    statement=db.select(PROBLEMS).filter_by(user_id=id)
    if tag is not None:
        statement=statement.filter_by(tag=tag)
    if status is not None:
        statement=statement.filter_by(solved=(status=='solved'))
    if min_rating is not None:
        statement=statement.where(PROBLEMS.rating>=int(min_rating))
    if max_rating is not None:
        statement=statement.where(PROBLEMS.rating<=int(max_rating))
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

@view_problems.route('/users/<int:id>/stats',methods=['GET'])
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