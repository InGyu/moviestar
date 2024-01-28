from bson import ObjectId
from pymongo import MongoClient

from flask import Flask, render_template, jsonify, request
from flask.json.provider import JSONProvider

import json
import sys
import logging

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.dbjungle


#####################################################################################
# 이 부분은 코드를 건드리지 말고 그냥 두세요. 코드를 이해하지 못해도 상관없는 부분입니다.
#
# ObjectId 타입으로 되어있는 _id 필드는 Flask 의 jsonify 호출시 문제가 된다.
# 이를 처리하기 위해서 기본 JsonEncoder 가 아닌 custom encoder 를 사용한다.
# Custom encoder 는 다른 부분은 모두 기본 encoder 에 동작을 위임하고 ObjectId 타입만 직접 처리한다.
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, cls=CustomJSONEncoder)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)


# 위에 정의되 custom encoder 를 사용하게끔 설정한다.
app.json = CustomJSONProvider(app)

# 여기까지 이해 못해도 그냥 넘어갈 코드입니다.
# #####################################################################################



#####
# 아래의 각각의 @app.route 은 RESTful API 하나에 대응됩니다.
# @app.route() 의 첫번째 인자는 API 경로,
# 생략 가능한 두번째 인자는 해당 경로에 적용 가능한 HTTP method 목록을 의미합니다.

# API #1: HTML 틀(template) 전달
#         틀 안에 데이터를 채워 넣어야 하는데 이는 아래 이어지는 /api/list 를 통해 이루어집니다.
@app.route('/')
def home():
    return render_template('index.html')


# API #2: 휴지통에 버려지지 않은 영화 목록을 반환합니다.
@app.route('/api/list', methods=['GET'])
def show_movies():
    # client 에서 요청한 정렬 방식이 있는지를 확인합니다. 없다면 기본으로 좋아요 순으로 정렬합니다.
    sortMode = request.args.get('sortMode', 'likes')
    print("리스트 정렬모드 : ",sortMode)
    
    if sortMode == 'likes':
        movies = list(db.movies.find({'trashed': False}, {}).sort('likes', -1)) #좋아요 내림차순
    elif sortMode == 'viewers':
        movies = list(db.movies.find({'trashed' : False}, {}).sort('viewers', -1)) #누적관객수 내림차순
    elif sortMode == 'date':
        movies = list(db.movies.find({'trashed' : False}, {}).sort([('open_year', -1),('open_month', -1), ('open_day', -1)])) #날짜 내림차순
    else:
        return jsonify({'result': 'failure'})

    # 2. 성공하면 success 메시지와 함께 movies_list 목록을 클라이언트에 전달합니다.
    return jsonify({'result': 'success', 'movies_list': movies})

# API #3: 휴지통에 버려진 영화 목록을 반환합니다.
@app.route('/api/list/trash', methods=['GET'])
def show_trash_movies():
    # client 에서 요청한 정렬 방식이 있는지를 확인합니다. 없다면 기본으로 좋아요 순으로 정렬합니다.
    sortMode = request.args.get('sortMode')
    print("휴지통 리스트 정렬 모드 : ", sortMode)
    if sortMode == 'likes':
        movies = list(db.movies.find({'trashed': True}, {}).sort('likes', -1))
    elif sortMode == 'viewers':
        movies = list(db.movies.find({'trashed' : True}, {}).sort('viewers', -1))
    elif sortMode == 'date':
        movies = list(db.movies.find({'trashed' : True}, {}).sort([('open_year', -1),('open_month', -1), ('open_day', -1)]))
        
    else:
        return jsonify({'result': 'failure'})

    # 2. 성공하면 success 메시지와 함께 movies_list 목록을 클라이언트에 전달합니다.
    return jsonify({'result': 'success', 'movies_list': movies})

# API #4: 해당 영화를 휴지통으로 보냅니다.
@app.route('/api/update/trash', methods=['POST'])
def trash_movies():
    title = request.form['post_title']
    result = db.movies.update_one({'title' : title}, {'$set' : {'trashed' : True}})
    print(title, "을(를) 휴지통으로 보냄")
    if result.modified_count == 1 : #DB에서 수정된 항목 카운트
        return jsonify({'result' : 'success'})
    else :
        return jsonify({'result' : 'failure'})

# API #5: 해당 영화를 복구합니다.
@app.route('/api/update/restore', methods=['POST'])
def restore_movies():
    title = request.form['post_title']
    result = db.movies.update_one({'title' : title}, {'$set' : {'trashed' : False}})
    print(title, "을(를) 휴지통에서 복구됨")
    if result.modified_count == 1 :
        return jsonify({'result' : 'success'})
    else :
        return jsonify({'result' : 'failure'})
    

# API #6: 해당 영화를 DB에서 완전히 제거합니다.
@app.route('/api/update/delete', methods=['POST'])
def delete_movies():
    title = request.form['post_title']
    result = db.movies.delete_one({'title' : title})
    print(title, "을(를) DB에서 제거")
    if result.deleted_count == 1 : # DB에서 제거된 항목 카운트
        return jsonify({'result' : 'success'})
    else :
        return jsonify({'result' : 'failure'})

# API #7: 영화에 좋아요 숫자를 하나 올립니다.
@app.route('/api/like', methods=['POST'])
def like_movie():
    
    title = request.form['post_title']
    app.logger.info(title)
    movie = db.movies.find_one({'title' : title})
    result = db.movies.update_one({'title' : title}, {'$set': {'likes': movie['likes'] + 1}}) 

    if result.modified_count == 1:
        return jsonify({'result': 'success'})
    else:
        return jsonify({'result': 'failure'})


if __name__ == '__main__':
    print(sys.executable)
    app.run('0.0.0.0', port=5000, debug=True)