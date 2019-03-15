from kvk import KVKClient
from flask import (
    Flask,
    render_template,
    request,
    jsonify
)

app = Flask(__name__, template_folder='templates')

@app.route('/')
def home():
    return  render_template('home.html')

@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404

@app.route('/api/v1/reggy/companies/search', methods=['GET'])
def search():
    query_parameters = request.args
    keywords = query_parameters.get('keywords')
    #return keywords
    client = KVKClient()
    #return keywords
    return jsonify(client.search_company(keywords))


if __name__ == '__main__':
    app.run(debug=True)
