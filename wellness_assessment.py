import requests
from flask import Flask, request
import json
from flask_cors import CORS
import os

app = Flask(__name__)




def create_session():
    s=requests.Session()
    url = 'https://c50fca.myshopify.com'
    access_token = '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'
    s.headers.update({
        "X-Shopify-Access-Token": access_token,
        "Content-Type" : "application/json"
    })
    return s


def get_customer_id(email):
    sess = create_session()
    url = 'https://c50fca.myshopify.com'
    access_token = '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'
    search_url = url + "/admin/api/2024-01/customers/search.json?query=email:"+email
    try:
        resp = sess.get(search_url)
        resp.raise_for_status()  # This will raise an exception for HTTP errors.
        #print(resp.json())
        return resp.json(), 200  # Return the parsed JSON data and status code.
    except requests.RequestException as e:  # This catches HTTP errors and other Request exceptions.
        print(e)
        return {"error": str(e)}, 500
    
    
def get_product_id(name):
    sess = create_session()
    url = 'https://c50fca.myshopify.com'
    access_token = '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'
    search_url = url + "/admin/api/2024-01/products.json?title="+name
    try:
        resp = sess.get(search_url)
        resp.raise_for_status()  # This will raise an exception for HTTP errors.
        #print(resp.json())
        return resp.json(), 200  # Return the parsed JSON data and status code.
    except requests.RequestException as e:  # This catches HTTP errors and other Request exceptions.
        print(e)
        return {"error": str(e)}, 500
    

@app.route("/customer-id/<string:customer_email>", methods=["GET"])
def get_customer(customer_email):
    url = 'https://c50fca.myshopify.com'
    access_token = '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'
    # Construct the URL for the POST request
    resp, status = get_customer_id(customer_email)
    return resp, status


@app.route("/get-product/<string:product_name>", methods=["GET"])
def get_product(product_name):
    url = 'https://c50fca.myshopify.com'
    access_token = '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'
    product, status_product = get_product_id(product_name)
    productId = product["products"][0]["id"]
    #get_url = url + "/admin/api/2024-01/metafields.json?metafield['owner_id']="+str(customerId)
    #get_url = url + "/admin/api/2024-01/metafields.json?metafield[namespace]=quiz_analysis"
    get_url = url + "/admin/api/2024-01/products/"+str(productId)+"/images.json"
    #get_url = url + "/admin/api/2024-01/customers/"+str(customerId)+"/metafields.json"
    try:
        sess = create_session()
        response = sess.get(get_url)
        response.raise_for_status()  # This will raise an exception for HTTP errors.
        for image in response.json()['images']:
            if image['position']==1:
                resp=image
        #print(resp.json())
        return resp, 200  # Return the parsed JSON data and status code.ß
    except requests.RequestException as e:  # This catches HTTP errors and other Request exceptions.
        print(e)
        return {"error": str(e)}, 500
    
    
    
@app.route("/get_quiz_analysis/<string:customer_email>", methods=["GET"])
def get_quiz_analysis(customer_email):
    url = 'https://c50fca.myshopify.com'
    access_token = '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'
    customer, status_customer = get_customer_id(customer_email)
    customerId = customer["customers"][0]["id"]
    #get_url = url + "/admin/api/2024-01/metafields.json?metafield['owner_id']="+str(customerId)
    #get_url = url + "/admin/api/2024-01/metafields.json?metafield[namespace]=quiz_analysis"
    get_url = url + "/admin/api/2024-01/metafields.json?metafield[owner_id]="+str(customerId)+"&metafield[owner_resource]=customer&metafield[namespace]=quiz_analysis"
    #get_url = url + "/admin/api/2024-01/customers/"+str(customerId)+"/metafields.json"
    try:
        sess = create_session()
        response = sess.get(get_url)
        response.raise_for_status()  # This will raise an exception for HTTP errors.
        #print(resp.json())
        return response.json(), 200  # Return the parsed JSON data and status code.ß
    except requests.RequestException as e:  # This catches HTTP errors and other Request exceptions.
        print(e)
        return {"error": str(e)}, 500


@app.route("/update-metafield/<string:customer_email>/<string:date>", methods=["POST"])
def update_metafield(customer_email,date):
    print('update_metafield')
    url = 'https://c50fca.myshopify.com'
    access_token = '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'
        # Get data from the request's body
    request_data = request.get_json()

    # Create a session with headers
    sess = create_session()

    # Construct the URL for the POST request
    customer, status = get_customer_id(customer_email)
    customerId = customer["customers"][0]["id"]
    
    post_url = url + "/admin/api/2024-01/customers/"+str(customerId)+"/metafields.json"

    # Prepare the data for the metafield update
    metafield_data = {
        "metafield": {
            "namespace": "quiz_analysis",
            "key": date,
            "value": json.dumps(request_data["value"]),
            "type": "json_string",  # Make sure the type matches the type of the value
        }
    }

    # Make the POST request
    response = sess.post(post_url, json=metafield_data)

    # Check the response status and return the result
    if response.status_code == 200 or response.status_code == 201:
        # If the request was successful, return the JSON response from Shopify
        return response.json(), 200
    else:
        # If the request failed, return the status code and error message
        return {"error": response.text}, response.status_code
    
    
CORS(app)
        
if __name__ == "__main__":
    app.secret_key = 'ItIsASecret'
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
