from elastic_enterprise_search import AppSearch
from elasticsearch import Elasticsearch
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
import os
import urllib3
from datetime import timedelta
from elasticapm.contrib.flask import ElasticAPM

############################# load .env #############################
load_dotenv()
APP_SEARCH_HOST = os.environ.get('APP_SEARCH_HOST')
ELASTICSEARCH_HOST = os.environ.get('ELASTICSEARCH_HOST')
ELASTIC_APM_HOST = os.environ.get('ELASTIC_APM_HOST')
ENGINE_API_KEY = os.environ.get('ENGINE_API_KEY')
ELASTICSEARCH_USER = os.environ.get('ELASTICSEARCH_USER')
ELASTICSEARCH_PASSWORD = os.environ.get('ELASTICSEARCH_PASSWORD')
APM_SECRET_TOKEN = os.environ.get('APM_SECRET_TOKEN')
ENGINE_NAME = os.environ.get('ENGINE_NAME')
APP_SECRET_KEY = os.environ.get('APP_SECRET_KEY')

app = Flask(__name__)
app.secret_key = APP_SECRET_KEY
# app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=10)

################ urllib3 경고 안뜨게 설정 ############################
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
############################## enterprise_search client ##############################

app_search = AppSearch(
    APP_SEARCH_HOST,
    bearer_auth=ENGINE_API_KEY
)
engine_name=ENGINE_NAME

############################## elasticsearch client #############################

client = Elasticsearch(ELASTICSEARCH_HOST, basic_auth=(ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD), verify_certs=None, ssl_show_warn=False)
################################## elastic apm #################################

app.config['ELASTIC_APM'] = {
    'SERVICE_NAME': 'app_search_demo_flask',
    'SERVER_URL': ELASTIC_APM_HOST,
    'SECRET_TOKEN': APM_SECRET_TOKEN,
    'VERIFY_SERVER_CERT': False
}
apm = ElasticAPM(app)

################################################################################

class User:
    def __init__(self, id, password, name):
        self.id = id
        self.password = password
        self.name = name
        
    def get_id(self):
        return self.id
    
    def get_password(self):
        return self.password




#main
@app.route('/')
def index():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    else:
        return render_template('index.html')
    

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        # form 방식으로 받아올 때에는 form에, json 방식으로 받아올 때에는 json에 원하는 정보가 담겨있음
        req_id = request.form.get('id')
        req_password = request.form.get('password')
        
        resp = client.get(index="wnyflix_user", id=req_id)
        resp_user = User(resp['_source']['id'], resp['_source']['password'], resp['_source']['name'])

        if req_password == resp_user.get_password():
            session['user_id'] = resp_user.get_id()
            print('로그인성공 id : '+ session.get('user_id'))
            return redirect(url_for('index'))
        else:
            return render_template('login.html')


#검색
@app.route('/search', methods=['GET'])
def search():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    else:
        term = request.args.get('term')
        #search
        search_result=app_search.search(engine_name=engine_name, page_size=42, query=term, facets={"genres.kor": {"type": "value", "size": 12}}, analytics={"tags": [session.get('user_id')]})
        pass_result = search_result['results']
        pass_facets = search_result["facets"]["genres.kor"][0]["data"]

        #top query
        top_queries=app_search.get_top_queries_analytics(engine_name=engine_name, page_size=11, filters={'results':True})
        pass_top_queries=top_queries['results'][1:12]
        
        #get seen(click)
        res_seen = app_search.get_top_clicks_analytics(engine_name=engine_name, query=term, filters={"tag": session.get('user_id')})
        seen = res_seen['results']
        seen_doc=[]
        for i in range(len(seen)):
            sd = app_search.get_documents(engine_name=engine_name, document_ids=[seen[i]['document_id']])
            seen_doc.append(sd[0])
            print(sd)

        return render_template('search.html', result=pass_result, top_queries=pass_top_queries, term=term, facets=pass_facets, seen=seen_doc)

#자동완성 suggest
@app.route('/suggest', methods=['GET'])
def suggest():
    query = request.args.get('query')
    suggest_li=[]
    suggest_result = app_search.query_suggestion(engine_name=engine_name, query=query, size=5, types={'documents': {'fields': ['title']}})
    for i in range(len(suggest_result['results']['documents'])):
        suggest_word=suggest_result['results']['documents'][i]['suggestion']
        if suggest_word!=query:
            suggest_li.append(suggest_word)
    return suggest_li

#개인화 자동완성
@app.route('/suggestPer', methods=['GET'])
def suggestPer():
    term = request.args.get('query')
    suggest_li=[]
    if term:
        suggest_result = client.search_template(index='logs-app_search.analytics-default', id='as_wnyflix_get_suggest', params={"term": term, "user": session.get('user_id')})
        for i in range(len(suggest_result['hits']['hits'])):
            suggest_word=suggest_result['hits']['hits'][i]['_source']['event']['query_string']
            suggest_li.append(suggest_word)
    return suggest_li
    

#click
@app.route('/click')
def log_click():
    term = request.args.get('term')
    id=request.args.get('id')
    app_search.log_clickthrough(engine_name=engine_name, query=term, document_id=id, tags=session.get('user_id'))
    return 'logging success'

#genre 필터링
@app.route('/filter')
def filtering():

    term = request.args.get('term')
    genres = request.args.getlist('genre')
    if genres :
        search_result=app_search.search(engine_name=engine_name, page_size=20, query=term, filters={"genres.kor": genres}, facets={"genres.kor": {"type": "value", "size": 20}})
        # passre = {
        #     "search_result" : search_result['results'],
        #     "genres" : "dsss"
        # }
        # return passre
        return search_result['results']
    else :
        search_result=app_search.search(engine_name=engine_name, page_size=20, query=term)
        return search_result['results']
    
    
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))
        

if __name__ == '__main__':
    app.run(port=5000,host="0.0.0.0", debug=True)