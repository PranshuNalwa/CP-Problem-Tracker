from CP import db,jwt

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

@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload) :
    jti = jwt_payload["jti"]
    statement=db.select(TOKEN_BLOCKLIST).filter_by(jti=jti)
    token = db.session.execute(statement).scalar_one_or_none()
    return token is not None

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return {"Error":"User is logged out"},400
