from flask import request
from flask_restful import Resource
from http import HTTPStatus
from mysql.connector.errors import Error
# 내가만든 커넥션 함수 임포트
from mysql_connection import get_connection
from email_validator import validate_email, EmailNotValidError

from flask_jwt_extended import create_access_token

from utils import hash_password
import datetime

class UserRegisterResource(Resource) :
    def post(self) :
        # 1. 클라이언트가 보내준, 회원정보 받아온다.
        data = request.get_json()

        # 2. 이메일 주소가 제대로 된 주소인지 확인하는 코드
        #    잘못된 이메일 주소면, 잘못되었다고 응답한다.
        try:
            # Validate.
            validate_email(data['email'])

        except EmailNotValidError as e:
            # email is not valid, exception message is human-readable
            print(str(e))
            return {'error' : 400 , 'result' : '이메일 주소가 잘못되었습니다.'} , HTTPStatus.BAD_REQUEST


        # 3. 비밀번호 길이 같은 조건이 있는지 확인하는 코드
        #    잘못되었으면, 클라이언트에 응답한다.
        if len(data['password']) < 4 or  len(data['password']) > 13 :
            return {'error' : 400, 'result' : '비밀번호의 길이를 확인하세요'}, HTTPStatus.BAD_REQUEST

        # 4. 비밀번호를 암호화한다.
        hashed_password = hash_password(data['password'])
        
        print('암호화된 비번길이 : ', str(len(data['password'])) )
        
        
        try : 
            # 1. DB에 연결
            connection = get_connection()

        except Error as e:
            print('Error', e)

            return {'error' : 500 , 'result' : 'db연결에 실패했습니다.'} , HTTPStatus.INTERNAL_SERVER_ERROR
        
        # 이메일이 중복인지 확인하기
        try :
            print("connection is connected")
            query = '''select * 
                        from user
                        where email = %s; '''
            
            param = (data["email"], )
            
            cursor = connection.cursor(dictionary = True)

            cursor.execute(query, param)

            # select 문은 아래 내용이 필요하다.
            record_list = cursor.fetchall()
            print(record_list)

            if len( record_list ) == 1 :
                return {'error' : 400 , 'result' : '이미 계정이 있습니다.'}, HTTPStatus.BAD_REQUEST
    
            
        # 위의 코드를 실행하다가, 문제가 생기면, except를 실행하라는 뜻.
        except Error as e :
            print('Error while connecting to MySQL', e)
            return {'error' : 500, 'result' : str(e)} , HTTPStatus.INTERNAL_SERVER_ERROR
        
        

        # 5. 데이터를 db에 저장한다.
        try :
            query = '''insert into user
                (email, password)
                values
                (%s,%s);'''
            # 파이썬에서, 튜플만들때, 데이터가 1개인 경우에는 콤마를 꼭 써주자.
            record = [ data['email'], hashed_password]
            # 3. 커넥션으로부터 커서를 가져온다.
            cursor = connection.cursor()

            # 4. 쿼리문을 커서에 넣어서 실행한다. // 실제로 실행하는 것은 커서가 해준다.
            # 레코드는 직접입력말고 변수로 넣었을때 실행
            cursor.execute(query, record)

            # 5. 커넥션을 커밋한다. => 디비에 영구적으로 반영하라는 뜻.
            connection.commit()
            # 디비에 저장된 유저의 아이디를 가져온다.
            user_id = cursor.lastrowid

            print(user_id)

        except Error as e:
            print('Error', e)
            return {'error' : 500, 'result' : str(e)} , HTTPStatus.INTERNAL_SERVER_ERROR
        
        # finally는 필수는 아니다.
        finally :
            if connection.is_connected():
                cursor.close()
                connection.close()
            else :
                print('MySQL connection is closed')

        # 7. JWT 토큰을 발행한다.
        ### DB에 저장된 유저 아이디 값으로 토큰을 발행한다!
        # 계속 로그인상태로 만들수도 어느 기준을 잡아 로그아웃이 되게 할 수 도 있다!
        expires = datetime.timedelta(days=10)
        access_token = create_access_token(user_id, expires_delta=expires)


        # 8. 모든것이 정상이면, 회원가입 잘 되었다고 응답한다. 
        return {'error' : 200 , 'result' : access_token}, HTTPStatus.OK