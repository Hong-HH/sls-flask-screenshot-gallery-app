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
    def post(self, photo_id) : 
        user_id = get_jwt_identity()
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




class TextResource(Resource) :
    
    @jwt_required() 
    def post(self, photo_id) : 
        return {'error' : 200}


