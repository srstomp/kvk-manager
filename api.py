from kvk import KVKClient
from flask import (
    Flask,
    request,
    jsonify,
)

app = Flask(__name__)

@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404

@app.route('/api/v1/reggy/companies/search', methods=['GET'])
def search():
    query_parameters = request.args
    company_name = query_parameters.get('company', '', type=str)
    kvk = query_parameters.get('kvk', '', type=str)
    street = query_parameters.get('street', '', type=str)
    postal_code = query_parameters.get('postal_code', '', type=str)
    house_number = query_parameters.get('house_number', '', type=str)
    city = query_parameters.get('city', '', type=str)

    client = KVKClient()
    return jsonify(client.search_company(company_name, kvk, street, postal_code, house_number, city))

if __name__ == '__main__':
    app.run(debug=True)
