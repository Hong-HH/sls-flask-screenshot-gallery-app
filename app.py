from flask import Flask, request
# JWT 사용을 위한 SECRET_KEY 정보가 들어있는 파일 임포트
from config import Config
from flask.json import jsonify
from http import HTTPStatus

from flask_restful import Api

from flask_jwt_extended import JWTManager

from resources.register import UserRegisterResource
from resources.login import UserLoginResource
from resources.logout import LogoutResource
from resources.blocklist import check_blocklist
from resources.photo import PhotoResource
from resources.photo_change import PhotoChangeResource
from resources.rekognition import TagResource


app = Flask(__name__)

# 환경 변수 세팅
app.config.from_object(Config)

# JWT 토큰 만들기
jwt = JWTManager(app)

@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload) :
    # db 에서 해당 jti 가 있는지 확인한다.
    jti = jwt_payload['jti']
    result = check_blocklist(jti)

    return result


api = Api(app)

# resources 와 연결
api.add_resource(UserRegisterResource, '/v1/user/register')     # 회원가입
api.add_resource(UserLoginResource, '/v1/user/login')           # 로그인
api.add_resource(LogoutResource, '/v1/user/logout')             # 로그아웃
api.add_resource(PhotoResource, '/v1/photo')                    # 사진 업로드 / 조회
api.add_resource(PhotoChangeResource, '/v1/photo/<int:photo_id>')# 사진의 설명 변경, 사진 삭제
api.add_resource(TagResource, '/v1/tag/<int:photo_id>')         # 사진의 태그 및 설명



# 기본 루트 연결 확인 멘트
@app.route('/')
def route_page():
    return "hello!!!!! it is work~"




if __name__ == "__main__" :
    app.run()


