from distutils.log import error
from flask import request
from flask_restful import Resource
from http import HTTPStatus
from mysql.connector.errors import Error
# 내가만든 커넥션 함수 임포트
from mysql_connection import get_connection

from flask_jwt_extended import jwt_required, get_jwt_identity

import boto3
from config import Config
from datetime import datetime

# 파일 확장자명을 우리가 조정할 수 있다.
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jepg', 'zip'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS


class PhotoResource(Resource) :
    
    @jwt_required() # 이 함수는 optional 파라미터가 False면, 무조건 토큰이 있어야 호출가능
    def post(self) : 
        # 클라이언트의 body로 보낸 json 데이터는
        # request.get_json() 함수로 받는다.
        print('호출되었어요!')

        # 아래는 json으로부터 데이터를 받을 경우이고
        # data = request.get_json()

        # 아래는 form-data 로 데이터를 받을 경우, 아래처럼 처리해야 한다.
        title = request.form['title']
        content = request.form['content']
        photo_time = request.form['photo_time']

        user_id = get_jwt_identity()

        # 아래는 form-data로 사진이 없을때 리턴 에러코드
        if 'photo' not in request.files :
            return {'error' : 400, 'result' : '사진이 없습니다!'}, HTTPStatus.BAD_REQUEST

        
        else :
            file = request.files['photo']

            if file and allowed_file(file.filename) :
                s3 = boto3.client('s3', aws_access_key_id = Config.ACCESS_KEY, aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY)

                filename = datetime.now()
                filename = filename.isoformat()
                filename = filename.replace(':','_')
                filename = str(user_id) + '__' + filename + '.jpg'

                try :
                    s3.upload_fileobj(file, Config.BUCKET, filename, ExtraArgs = {'ACL' : 'public-read', 'ContentType' : file.content_type})
                except Exception as e :
                    return {'error' : 402,'result' : str(e) }, 402
            
            # 디비에 문자열 데이터 저장
            try : 
                # 1. DB에 연결
                connection = get_connection()
                # 2. 쿼리문 만들기 : mysql workbench 에서 잘 되는것을 확인한 SQL문을 넣어준다.
                # 이렇게 함수를 쓰면 로컬타임으로 가져온다. 하지만 서버에 저장할때는 UTC로 넣어주어야 한다.

                query = '''insert into photo
                    (title, content, user_id,photo_time, photo_url)
                    values
                    (%s,%s,%s,%s, %s);'''
                # 파이썬에서, 튜플만들때, 데이터가 1개인 경우에는 콤마를 꼭 써주자.
                record = (title, content, user_id ,photo_time, filename)
                # 3. 커넥션으로부터 커서를 가져온다.
                cursor = connection.cursor()

                # 4. 쿼리문을 커서에 넣어서 실행한다. // 실제로 실행하는 것은 커서가 해준다.
                # 레코드는 직접입력말고 변수로 넣었을때 실행
                cursor.execute(query, record)

                # 5. 커넥션을 커밋한다. => 디비에 영구적으로 반영하라는 뜻.
                connection.commit()

            except Error as e:
                print('Error', e)
                return {'error' : 500, 'result' : str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR
            # finally는 필수는 아니다.
            finally :
                if connection.is_connected():
                    cursor.close()
                    connection.close()
                else :
                    print('MySQL connection is closed')

            
            
            return {'error' : 200, 'result' : '업로드 되었습니다.'}, HTTPStatus.OK


    @jwt_required()
    def get(self) : 
        user_id = get_jwt_identity()
        print(user_id)

        # 쿼리 파라미터 가져오기
        offset = request.args.get('offset')
        limit = request.args.get('limit')

        try :
            # 클라이언트가 GET 요청하면, 이 함수에서 우리가 코드를 작성해 주면 된다.
            
            # 1. db 접속
            connection = get_connection()

            # 2. 해당 테이블, recipe 테이블에서 select
            query = '''select * from photo
                        where user_id=%s
                        order by created_at desc
                        limit '''+ offset +''', '''+ limit + '''; '''
            
            record = (user_id, )
            cursor = connection.cursor(dictionary = True)
            cursor.execute(query, record)
            # select 문은 아래 내용이 필요하다.
            # 커서로 부터 실행한 결과 전부를 받아와라.
            record_list = cursor.fetchall()
            print(record_list)

            ### 중요. 파이썬의 시간은, JSON으로 보내기 위해서
            ### 문자열로 바꿔준다.
            i = 0
            for record in record_list:
                record_list[i]['created_at'] = record['created_at'].isoformat()
                record_list[i]['updated_at'] = record['updated_at'].isoformat()
                record_list[i]['photo_time'] = record['photo_time'].isoformat()
                i = i +1


        # 3. 클라이언트에 보낸다. 
        except Error as e :
            # 뒤의 e는 에러를 찍어라 error를 e로 저장했으니까!
            print('Error while connecting to MySQL', e)
            return {'error' : 500, 'count' : 0, 'list' : []}, HTTPStatus.INTERNAL_SERVER_ERROR
        # finally 는 try에서 에러가 나든 안나든, 무조건 실행하라는 뜻.
        finally : 
            print('finally')
            if connection.is_connected():
                cursor.close()
                connection.close()
                print('MySQL connection is closed')
            else :
                print('connection does not exist')
        return {'error' : 200, 'count' : len(record_list), 'list' : record_list }, HTTPStatus.OK



class PhotoListResource(Resource) :
    @jwt_required()
    def get(self) : 
        user_id = get_jwt_identity()
        print(user_id)

        # 쿼리 파라미터 가져오기
        offset = request.args.get('offset')
        limit = request.args.get('limit')

        photo_id_list = []

        try :
            # 클라이언트가 GET 요청하면, 이 함수에서 우리가 코드를 작성해 주면 된다.
            
            # 1. db 접속
            connection = get_connection()

            # 2. 해당 테이블, recipe 테이블에서 select
            query = '''select * from photo
                        where user_id=%s
                        order by created_at desc
                        limit '''+ offset +''', '''+ limit + '''; '''
            
            record = (user_id, )
            cursor = connection.cursor(dictionary = True)
            cursor.execute(query, record)
            # select 문은 아래 내용이 필요하다.
            # 커서로 부터 실행한 결과 전부를 받아와라.
            record_list = cursor.fetchall()
            print(record_list)

            ### 중요. 파이썬의 시간은, JSON으로 보내기 위해서
            ### 문자열로 바꿔준다.
            i = 0
            for record in record_list:
                record_list[i]['created_at'] = record['created_at'].isoformat()
                record_list[i]['updated_at'] = record['updated_at'].isoformat()
                record_list[i]['photo_time'] = record['photo_time'].isoformat()
                photo_id_list.append(record['id'])
                i = i +1

            photo_list = record_list


        # 3. 클라이언트에 보낸다. 
        except Error as e :
            # 뒤의 e는 에러를 찍어라 error를 e로 저장했으니까!
            print('Error while connecting to MySQL', e)
            return {'error' : 500, 'count' : 0, 'list' : []}, HTTPStatus.INTERNAL_SERVER_ERROR
        # finally 는 try에서 에러가 나든 안나든, 무조건 실행하라는 뜻.

        # 2. 해당 테이블, recipe 테이블에서 select

        
        try :
            for photo_id in photo_id_list :
                count = 0
                query = '''SELECT * FROM tag
                            where photo_id = %s; '''
                
                record = (photo_id, )
                cursor = connection.cursor(dictionary = True)
                cursor.execute(query, record)
                # select 문은 아래 내용이 필요하다.
                # 커서로 부터 실행한 결과 전부를 받아와라.
                record_list = cursor.fetchall()
                print(record_list)

                ### 중요. 파이썬의 시간은, JSON으로 보내기 위해서
                ### 문자열로 바꿔준다.
                i = 0
                for record in record_list:
                    record_list[i]['created_at'] = record['created_at'].isoformat()
                    i = i +1
                
                photo_list[count]["tag"] = record_list
                count = count +1


        # 3. 클라이언트에 보낸다. 
        except Error as e :
            # 뒤의 e는 에러를 찍어라 error를 e로 저장했으니까!
            print('Error while connecting to MySQL', e)
            return {'error' : 500, 'count' : 0, 'list' : []}, HTTPStatus.INTERNAL_SERVER_ERROR
        # finally 는 try에서 에러가 나든 안나든, 무조건 실행하라는 뜻.
        finally : 
            print('finally')
            if connection.is_connected():
                cursor.close()
                connection.close()
                print('MySQL connection is closed')
            else :
                print('connection does not exist')

        

        return {'error' : 200, 'count' : len(photo_list), 'result' : photo_list }, HTTPStatus.OK


