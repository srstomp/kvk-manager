from kvk import KVKClient
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    Markup
)
from urllib.parse import quote

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
    # urlencodedString = quote(request.query_string)
    company = query_parameters.get('company', '', type=str)
    kvk = query_parameters.get('kvk', '', type=str)

    client = KVKClient()
    return jsonify(client.search_company(company, kvk))


if __name__ == '__main__':
    app.run(debug=True)
