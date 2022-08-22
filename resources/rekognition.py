from distutils.log import error
from flask import request
from flask_restful import Resource
from http import HTTPStatus
from mysql.connector.errors import Error

from flask_jwt_extended import jwt_required, get_jwt_identity
import boto3
from datetime import datetime
import os
import sys
import urllib.request
import json

from config import Config
# 내가만든 커넥션 함수 임포트
from mysql_connection import get_connection


class TagResource(Resource) :
    
    @jwt_required() 
    def post(self) : 
        data = request.get_json()
        # img_url = data['photo_url']
        # img_url_list = img_url.split('/')
        # photo = img_url_list[-1]

        # 바디에서 photo_url 정보 가져오기
        photo = data['photo_url']
        bucket = Config.BUCKET
        
        # 사진 object detection 하기 
        rekognition =boto3.client('rekognition', 'us-east-1', aws_access_key_id = Config.ACCESS_KEY, aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY)
        response = rekognition.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}},MaxLabels=10, MinConfidence=85)
        result = []       
        # 결과중에서 이름만을 추출해 result에 넣기
        for label in response['Labels']:
            # label_dict = {}
            # label_dict['Name'] = label['Name']
            # label_dict['Confidence'] = label['Confidence']
            # result.append(label_dict)
            result.append(label['Name'])

        # result 를 한국어로 번역하기
        client_id = Config.papago_client_id
        client_secret = Config.papago_client_secret
        trans_result = []
        for keyword in result :
            encText = urllib.parse.quote(keyword)
            data = "source=en&target=ko&text=" + encText
            url = "https://openapi.naver.com/v1/papago/n2mt"
            request_trans = urllib.request.Request(url)
            request_trans.add_header("X-Naver-Client-Id",client_id)
            request_trans.add_header("X-Naver-Client-Secret",client_secret)
            response = urllib.request.urlopen(request_trans, data=data.encode("utf-8"))
            rescode = response.getcode()
            if(rescode==200):
                response_body = response.read()
                print(response_body.decode('utf-8'))
                result_dict = json.loads(response_body.decode('utf-8'))
                text = result_dict["message"]["result"]["translatedText"]
                trans_result.append(text)
            else:
                print("Error Code:" + rescode)
        
        print("번역 결과 /////////////////////////////")
        print(trans_result)

            
        return {'error' : 200, 'result' : trans_result}, HTTPStatus.OK


class GetTagResource(Resource) :

    @jwt_required() 
    def get(self, photo_id) :

        try :
            # 클라이언트가 GET 요청하면, 이 함수에서 우리가 코드를 작성해 주면 된다.
            
            # 1. db 접속
            connection = get_connection()

            # 2. 해당 테이블, recipe 테이블에서 select
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
        return {'error' : 200, 'list' : record_list }, HTTPStatus.OK



    @jwt_required() 
    def post(self, photo_id) :
        user_id = get_jwt_identity()
        data = request.get_json()
        tag_list = data['tag']
        try : 
            # 1. DB에 연결
            connection = get_connection()

            for tag in tag_list :
                # 2. 쿼리문 만들기 : mysql workbench 에서 잘 되는것을 확인한 SQL문을 넣어준다.
                query = '''insert into tag
                            (photo_id, tag)
                            values
                            (%s, %s);'''
                # 파이썬에서, 튜플만들때, 데이터가 1개인 경우에는 콤마를 꼭 써주자.
                record = (photo_id, tag)
                # 3. 커넥션으로부터 커서를 가져온다.
                cursor = connection.cursor()

                # 4. 쿼리문을 커서에 넣어서 실행한다. // 실제로 실행하는 것은 커서가 해준다.
                # 레코드는 직접입력말고 변수로 넣었을때 실행
                cursor.execute(query, record)

                # 5. 커넥션을 커밋한다. => 디비에 영구적으로 반영하라는 뜻.
                connection.commit()

        except Error as e:
            print('Error', e)
            return {'error' : 400, 'result' : str(e)}, HTTPStatus.BAD_REQUEST
        # finally는 필수는 아니다.
        finally :
            if connection.is_connected():
                cursor.close()
                connection.close()
                print('MySQL connection is closed')
                return {'error' : 200, 'result' : '잘 저장되었습니다.'}, HTTPStatus.OK





class TextResource(Resource) :
    
    @jwt_required() 
    def post(self, photo_id) : 
        return {'error' : 200}


