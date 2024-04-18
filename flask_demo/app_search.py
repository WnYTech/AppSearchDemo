from elastic_enterprise_search import AppSearch
from flask import Flask
from flask import render_template
from flask import request
from dotenv import load_dotenv
import os
import urllib3

from elasticapm.contrib.flask import ElasticAPM


app = Flask(__name__)

################ urllib3 경고 안뜨게 설정 ############################
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
############################# load .env #############################

load_dotenv()
APP_SEARCH_HOST = os.environ.get('APP_SEARCH_HOST')
ELASTIC_APM_HOST = os.environ.get('ELASTIC_APM_HOST')
API_KEY = os.environ.get('API_KEY')
APM_SECRET_TOKEN = os.environ.get('APM_SECRET_TOKEN')
ENGINE_NAME = os.environ.get('ENGINE_NAME')

############################## enterprise_search client ##############################

app_search = AppSearch(
    APP_SEARCH_HOST,
    bearer_auth=API_KEY
)
engine_name=ENGINE_NAME

################################## elastic apm #################################

app.config['ELASTIC_APM'] = {
    'SERVICE_NAME': 'app_search_demo_flask',
    'SERVER_URL': ELASTIC_APM_HOST,
    'SECRET_TOKEN': APM_SECRET_TOKEN,
    'VERIFY_SERVER_CERT': False
}
apm = ElasticAPM(app)

################################################################################


#main
@app.route('/')
def index():
    return render_template('index.html', number=1)

#검색
@app.route('/search', methods=['GET'])
def search():
    term = request.args.get('term')
    #search
    search_result=app_search.search(engine_name=engine_name, page_size=20, query=term, facets={"genres.kor": {"type": "value", "size": 20}})
    pass_result = search_result['results']
    pass_facets = search_result["facets"]["genres.kor"][0]["data"]

    #top query
    top_queries=app_search.get_top_queries_analytics(engine_name=engine_name, page_size=11, filters={'results':True})
    pass_top_queries=top_queries['results'][1:12]

    return render_template('search.html', result=pass_result, top_queries=pass_top_queries, term=term, facets=pass_facets)

#자동완성 suggest
@app.route('/suggest', methods=['GET'])
def suggest():
    query = request.args.get('query')
    suggest_li=[]
    suggest_result = app_search.query_suggestion(engine_name=engine_name, query=query, size=10, types={'documents': {'fields': ['title']}})
    for i in range(len(suggest_result['results']['documents'])):
        suggest_word=suggest_result['results']['documents'][i]['suggestion']
        if suggest_word!=query:
            suggest_li.append(suggest_word)
    return suggest_li

#click
@app.route('/click')
def log_click():
    term = request.args.get('term')
    id=request.args.get('id')
    app_search.log_clickthrough(engine_name=engine_name, query=term, document_id=id)
    return 'logging success'

#genre 필터링
@app.route('/filter')
def filtering():

    term = request.args.get('term')
    genres = request.args.getlist('genre')
    if genres :
        search_result=app_search.search(engine_name=engine_name, page_size=20, query=term, filters={"genres.kor": genres})
        return search_result['results']
    else :
        search_result=app_search.search(engine_name=engine_name, page_size=20, query=term)
        return search_result['results']
        
    
    


if __name__ == '__main__':
    app.run(port=5001,host="0.0.0.0", debug=True)