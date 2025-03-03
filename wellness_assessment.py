import requests
from flask import Flask, request
import json
from flask_cors import CORS
import os
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = Flask(__name__)




def create_session():
    s = requests.Session()
    url = 'https://c50fca.myshopify.com'
    access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
    s.headers.update({
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    })
    return s
    
def get_customer_id(email):
    sess = create_session()
    url = 'https://c50fca.myshopify.com'
    search_url = url + "/admin/api/2025-01/customers/search.json?query=email:"+email
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
    search_url = url + "/admin/api/2025-01/products.json?title="+name
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
    # Construct the URL for the POST request
    resp, status = get_customer_id(customer_email)
    return resp, status


@app.route("/get-product/<string:product_name>", methods=["GET"])
def get_product(product_name):
    url = 'https://c50fca.myshopify.com'
    product, status_product = get_product_id(product_name)
    productId = product["products"][0]["id"]
    #get_url = url + "/admin/api/2025-01/metafields.json?metafield['owner_id']="+str(customerId)
    #get_url = url + "/admin/api/2025-01/metafields.json?metafield[namespace]=quiz_analysis"
    get_url = url + "/admin/api/2025-01/products/"+str(productId)+"/images.json"
    #get_url = url + "/admin/api/2025-01/customers/"+str(customerId)+"/metafields.json"
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
    retry_attempts = 10  # Number of retry attempts
    retry_delay = 2  # Delay in seconds between attempts

    # Retry loop to wait for customer creation
    for attempt in range(retry_attempts):
        customer, status_customer = get_customer_id(customer_email)
        if status_customer == 200 and customer.get("customers"):
            customerId = customer["customers"][0]["id"]
            break  # Customer exists, exit the loop
        else:
            print(f"Customer not found. Retry {attempt + 1}/{retry_attempts}...")
            time.sleep(retry_delay)
    else:
        # If the loop completes without finding the customer
        return {"error": f"Customer {customer_email} not found after multiple attempts."}, 404

    # Once the customer exists, proceed to get the quiz analysis metafield
    get_url = url + "/admin/api/2025-01/metafields.json?metafield[owner_id]=" + str(customerId) + "&metafield[owner_resource]=customer&metafield[namespace]=quiz_analysis"

    try:
        sess = create_session()
        response = sess.get(get_url)
        response.raise_for_status()
        return response.json(), 200
    except requests.RequestException as e:
        print(e)
        return {"error": str(e)}, 500



@app.route("/update-metafield/<string:customer_email>/<string:date>", methods=["POST"])
def update_metafield(customer_email, date):
    print('update_metafield')
    url = 'https://c50fca.myshopify.com'
    request_data = request.get_json()
    sess = create_session()

    # Step 1: Check if the customer exists
    customer, status = get_customer_id(customer_email)
    if status != 200 or not customer.get("customers"):
        # Step 2: If customer doesn't exist, create a new customer
        print(f"Customer {customer_email} not found. Creating new customer...")
        new_customer_data = {
            "customer": {
                "email": customer_email,
                "accepts_marketing": True,
                "tags": "quiz_user",
                "first_name": "New",  # You can customize this
                "last_name": "Customer"
            }
        }
        create_customer_url = url + "/admin/api/2025-01/customers.json"
        try:
            response = sess.post(create_customer_url, json=new_customer_data)
            response.raise_for_status()
            customer = response.json()
            customer_id = customer["customer"]["id"]
            print(f"New customer created with ID: {customer_id}")
        except requests.RequestException as e:
            print(f"Error creating customer: {e}")
            return {"error": "Failed to create new customer"}, 500
    else:
        customer_id = customer["customers"][0]["id"]
        print(f"Existing customer found with ID: {customer_id}")

    # Step 3: Update the metafield for the customer
    post_url = url + f"/admin/api/2025-01/customers/{customer_id}/metafields.json"
    metafield_data = {
        "metafield": {
            "namespace": "quiz_analysis",
            "key": date,
            "value": json.dumps(request_data["value"]),
            "type": "json_string"
        }
    }
    try:
        response = sess.post(post_url, json=metafield_data)
        response.raise_for_status()
        print("Metafield updated successfully.")
        return response.json(), 200
    except requests.RequestException as e:
        print(f"Error updating metafield: {e}")
        return {"error": str(e)}, 500



@app.route("/add-tags/<string:customer_email>", methods=["POST"])
def add_tags(customer_email):
    print('add_tags')
    url = 'https://c50fca.myshopify.com'
    request_data = request.get_json()
    sess = create_session()

    # Step 1: Check if the customer exists
    customer, status = get_customer_id(customer_email)
    if status != 200 or not customer.get("customers"):
        print(f"Customer {customer_email} not found.")
        return {"error": "Customer not found"}, 404

    customer_id = customer["customers"][0]["id"]
    print(f"Existing customer found with ID: {customer_id}")

    # Step 2: Add tags to the existing customer
    existing_tags = customer["customers"][0].get("tags", "")
    new_tags = request_data.get("tags", [])
    updated_tags = existing_tags.split(",") + new_tags
    updated_tags = ",".join(set(updated_tags))  # Remove duplicates

    update_customer_url = url + f"/admin/api/2025-01/customers/{customer_id}.json"
    customer_data = {
        "customer": {
            "id": customer_id,
            "tags": updated_tags
        }
    }
    try:
        response = sess.put(update_customer_url, json=customer_data)
        response.raise_for_status()
        print("Tags updated successfully.")
        return response.json(), 200
    except requests.RequestException as e:
        print(f"Error updating tags: {e}")
        return {"error": str(e)}, 500
    



@app.route("/remove-quiz-tags", methods=["POST"])
def remove_quiz_tags():
    print('remove_quiz_tags triggered')
    url = 'https://c50fca.myshopify.com'
    request_data = request.get_json()
    
    customer_email = request_data.get("email")
    if not customer_email:
        return {"error": "Email is required"}, 400

    sess = create_session()

    # Step 1: Check if the customer exists
    customer, status = get_customer_id(customer_email)
    if status != 200 or not customer.get("customers"):
        print(f"Customer {customer_email} not found.")
        return {"error": "Customer not found"}, 404

    customer_id = customer["customers"][0]["id"]
    existing_tags = customer["customers"][0].get("tags", "")

    # Step 2: Remove all tags that start with "quiz_"
    updated_tags = [tag for tag in existing_tags.split(",") if not tag.strip().startswith("quiz")]
    updated_tags = ",".join(updated_tags)  # Convert back to string

    update_customer_url = url + f"/admin/api/2025-01/customers/{customer_id}.json"
    customer_data = {
        "customer": {
            "id": customer_id,
            "tags": updated_tags
        }
    }

    try:
        response = sess.put(update_customer_url, json=customer_data)
        response.raise_for_status()
        print(f"Removed quiz tags from {customer_email}: {updated_tags}")
        return {"message": "Quiz tags removed successfully", "remaining_tags": updated_tags}, 200
    except requests.RequestException as e:
        print(f"Error removing tags: {e}")
        return {"error": str(e)}, 500




@app.route("/remove-recommendation-tags/<string:customer_email>", methods=["POST"])
def remove_recommendation_tags(customer_email):
    print('remove_recommendation_tags triggered')
    url = 'https://c50fca.myshopify.com'
    request_data = request.get_json()
    

    sess = create_session()

    # Step 1: Check if the customer exists
    customer, status = get_customer_id(customer_email)
    if status != 200 or not customer.get("customers"):
        print(f"Customer {customer_email} not found.")
        return {"error": "Customer not found"}, 404

    customer_id = customer["customers"][0]["id"]
    existing_tags = customer["customers"][0].get("tags", "")

    # Step 2: Remove all tags that start with "quiz_"
    updated_tags = [tag for tag in existing_tags.split(",") if not tag.strip().startswith("recommendation")]
    updated_tags = ",".join(updated_tags)  # Convert back to string

    update_customer_url = url + f"/admin/api/2025-01/customers/{customer_id}.json"
    customer_data = {
        "customer": {
            "id": customer_id,
            "tags": updated_tags
        }
    }

    try:
        response = sess.put(update_customer_url, json=customer_data)
        response.raise_for_status()
        print(f"Removed recommendation tags from {customer_email}: {updated_tags}")
        return {"message": "Recommendation tags removed successfully", "remaining_tags": updated_tags}, 200
    except requests.RequestException as e:
        print(f"Error removing tags: {e}")
        return {"error": str(e)}, 500
    
    
    


    
    
CORS(app)
        
if __name__ == "__main__":
    app.secret_key = 'ItIsASecret'
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
