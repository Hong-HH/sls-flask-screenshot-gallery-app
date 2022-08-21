from flask_jwt_extended import get_jwt

from flask import request
from flask.json import jsonify
from flask_jwt_extended.view_decorators import jwt_required
from flask_restful import Resource
from http import HTTPStatus

from mysql_connection import get_connection
from mysql.connector.errors import Error

from email_validator import validate_email, EmailNotValidError

from utils import hash_password, check_password

from flask_jwt_extended import create_access_token


# 로그아웃된 토큰을 db에 저장해 준다.
# 로그아웃 한 유저인지 판단한다.


# 로그아웃 클래스 
class LogoutResource(Resource) :
    @jwt_required()
    def post(self) :
        jti = get_jwt()['jti']
        print(jti)

        # 로그아웃된 토큰의 아이디값을, 블랙리스트에 저장한다.
        # DB에 인서트하는 코드

        try : 
            # 1. DB에 연결
            connection = get_connection()
            # 2. 쿼리문 만들기 : mysql workbench 에서 잘 되는것을 확인한 SQL문을 넣어준다.
            # 이렇게 함수를 쓰면 로컬타임으로 가져온다. 하지만 서버에 저장할때는 UTC로 넣어주어야 한다.

            query = '''insert into token
                (jti)
                values
                (%s);'''
            # 파이썬에서, 튜플만들때, 데이터가 1개인 경우에는 콤마를 꼭 써주자.
            record = (jti, )
            # 3. 커넥션으로부터 커서를 가져온다.
            cursor = connection.cursor()

            # 4. 쿼리문을 커서에 넣어서 실행한다. // 실제로 실행하는 것은 커서가 해준다.
            # 레코드는 직접입력말고 변수로 넣었을때 실행
            cursor.execute(query, record)

            # 5. 커넥션을 커밋한다. => 디비에 영구적으로 반영하라는 뜻.
            connection.commit()
           
        except Error as e:
            print('Error', e)
        # 6. username이나 email이 이미 db에 있으면, 
        #    이미 존재하는 회원이라고 클라이언트에 응답한다.
            return {'error' : ''} , HTTPStatus.BAD_REQUEST
        # finally는 필수는 아니다.
        finally :
            if connection.is_connected():
                cursor.close()
                connection.close()
            else :
                print('MySQL connection is closed')

        # 실제는 에러코드를 보낸다. 문자로 소통하지 않음. error 0 는 ok 라던가
        # 대기업의 api를 보고 흉내낼것
        return {'result':'로그아웃 되었습니다.'}