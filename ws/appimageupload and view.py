from flask import Flask, request, jsonify, render_template
import firebase_admin
from firebase_admin import credentials, db
import requests  # For making API requests to ImageBB
import os

app = Flask(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("C:/myproject/lokvikas-web-firebase-adminsdk-yoqwd-60271071b2.json")  # Replace with your Firebase private key path
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://lokvikas-web-default-rtdb.firebaseio.com/"  # Replace with your Firebase Realtime Database URL
})

# ImageBB API key
IMAGEBB_API_KEY = "f6230ba4f83a87955248c7ea01f84dd1"

# Route to render admin dashboard
@app.route("/admin", methods=["GET"])
def admin_dashboard():
    return render_template("admin_dashboard.html")

# Route to upload image and save product
@app.route("/admin/add-product", methods=["POST"])
def add_product():
    try:
        # Get form data
        product_name = request.form.get("name")
        price = request.form.get("price")
        stock = request.form.get("stock")
        image = request.files.get("image")

        # Validate fields
        if not (product_name and price and stock and image):
            return jsonify({"success": False, "message": "All fields are required!"})

        # Upload image to ImageBB
        imgbb_response = requests.post(
            f"https://api.imgbb.com/1/upload?key={IMAGEBB_API_KEY}",
            files={"image": image.read()}
        )
        imgbb_data = imgbb_response.json()

        if not imgbb_data.get("success"):
            return jsonify({"success": False, "message": "Image upload failed!"})

        # Get Image URL
        image_url = imgbb_data["data"]["url"]

        # Save product to Firebase
        product_ref = db.reference("products").push()
        product_ref.set({
            "name": product_name,
            "price": price,
            "stock": stock,
            "image_url": image_url
        })

        return jsonify({"success": True, "message": "Product added successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# Route to fetch all products
@app.route("/admin/products", methods=["GET"])
def get_products():
    try:
        products = db.reference("products").get() or {}
        return jsonify({"success": True, "products": products})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# Route to remove a product
@app.route("/admin/remove-product/<product_id>", methods=["DELETE"])
def remove_product(product_id):
    try:
        product_ref = db.reference(f"products/{product_id}")
        if not product_ref.get():
            return jsonify({"success": False, "message": "Product not found!"})

        product_ref.delete()
        return jsonify({"success": True, "message": "Product removed successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
