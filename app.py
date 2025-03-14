from flask import Flask, render_template, request, redirect, jsonify, flash, session, url_for
import firebase_admin
from firebase_admin import credentials, db, initialize_app
import requests
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = "lSd4EY2K9VJsNAnsQE2xD9MUxkGIKxZyVYLBQ2Gw"  # Use a secure value in production
# Initialize Firebase Admin SDK
cred = credentials.Certificate("lokvikas-web-firebase-adminsdk-yoqwd-60271071b2.json")  # Update with your Firebase private key path
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://lokvikas-web-default-rtdb.firebaseio.com/"  # Replace with your Firebase Realtime Database URL
})
firebase_json_path = "/etc/secrets/firebase-adminsdk.json"

# Decorator to ensure user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("is_logged_in"):
            flash("Please log in to access this page.", "error")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')


@app.route("/products")
def products():
    """
    Fetches products from the Firebase database and displays them.
    """
    try:
        # Fetch products from Firebase
        products_ref = db.reference("products").get()
        products = []

        # Parse product data into a list
        if products_ref:
            for key, value in products_ref.items():
                product = {
                    "id": key,
                    "name": value.get("name", "Unknown"),
                    "price": value.get("price", "0"),
                    "image_url": value.get("image_url", "https://via.placeholder.com/300"),
                    "stock": int(value.get("stock", 0))
                }
                products.append(product)

        if not products:
            flash("No products available.", "info")

        return render_template("products.html", products=products)
    except Exception as e:
        flash(f"Error fetching products: {str(e)}", "error")
        return render_template("products.html", products=[])


@app.route('/about-us')
def about_us():
    return render_template('aboutus.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        phone = data.get('phone')
        password = data.get('password')

        if not phone or not password:
            return jsonify({"success": False, "error": "Phone number and password are required!"}), 400

        try:
            # Store data in Firebase
            ref = db.reference(f"admins/{phone}")
            ref.set({
                "phone": phone,
                "password": password  # Reminder: Hash the password in production
            })
            return jsonify({"success": True}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']

        # Retrieve admin data from Firebase
        admin_ref = db.reference(f"admins/{phone}")
        admin_data = admin_ref.get()

        if admin_data and admin_data['password'] == password:
            session["is_logged_in"] = True
            session["phone"] = phone
            flash("Login successful!", "success")
            return redirect('/admin-dash')
        else:
            flash("Invalid phone number or password.", "error")
            return redirect('/login')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect('/login')

# ImageBB API key
IMAGEBB_API_KEY = "f6230ba4f83a87955248c7ea01f84dd1"



@app.route("/admin/add-product", methods=["POST"])
@login_required
def add_product():
    try:
        # Get form data
        product_name = request.form.get("name")
        price = request.form.get("price")
        stock = request.form.get("stock")
        image = request.files.get("image")

        # Validate fields
        if not (product_name and price and stock and image):
            return jsonify({"success": False, "message": "All fields are required!"}), 400

        # Upload image to ImageBB
        imgbb_response = requests.post(
            f"https://api.imgbb.com/1/upload?key={IMAGEBB_API_KEY}",
            files={"image": image.read()}
        )
        imgbb_data = imgbb_response.json()

        if not imgbb_data.get("success"):
            return jsonify({"success": False, "message": "Image upload failed!"}), 500

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

        return jsonify({"success": True, "message": "Product added successfully!"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/admin/products", methods=["GET"])
@login_required
def get_products():
    try:
        products = db.reference("products").get() or {}
        return jsonify({"success": True, "products": products}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/admin/remove-product/<product_id>", methods=["DELETE"])
@login_required
def remove_product(product_id):
    try:
        product_ref = db.reference(f"products/{product_id}")
        if not product_ref.get():
            return jsonify({"success": False, "message": "Product not found!"}), 404

        product_ref.delete()
        return jsonify({"success": True, "message": "Product removed successfully!"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
        
# Add Investor Endpoint
@app.route("/admin/add-investor", methods=["POST"])
@login_required
def add_investor():
    try:
        # Get form data
        investor_name = request.form.get("investor_name")
        contribution = request.form.get("contribution")
        role = request.form.get("role")
        contact_details = request.form.get("contact_details")
        photo = request.files.get("photo")

        # Validate fields
        if not (investor_name and contribution and role and contact_details and photo):
            return jsonify({"success": False, "message": "All fields are required!"}), 400

        # Upload image to ImageBB (or other image hosting services)
        imgbb_response = requests.post(
            f"https://api.imgbb.com/1/upload?key={IMAGEBB_API_KEY}",
            files={"image": photo.read()}
        )
        imgbb_data = imgbb_response.json()

        if not imgbb_data.get("success"):
            return jsonify({"success": False, "message": "Image upload failed!"}), 500

        # Get Image URL
        photo_url = imgbb_data["data"]["url"]

        # Save investor to Firebase
        investor_ref = db.reference("investors").push()
        investor_ref.set({
            "investor_name": investor_name,
            "contribution": contribution,
            "role": role,
            "contact_details": contact_details,
            "photo_url": photo_url
        })

        return jsonify({"success": True, "message": "Investor added successfully!"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Get Investors Endpoint
@app.route("/admin/investors", methods=["GET"])
@login_required
def get_investors():
    try:
        investors = db.reference("investors").get() or {}
        return jsonify({"success": True, "investors": investors}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Remove Investor Endpoint
@app.route("/admin/remove-investor/<investor_id>", methods=["DELETE"])
@login_required
def remove_investor(investor_id):
    try:
        # Reference the investor by their ID
        investor_ref = db.reference(f"investors/{investor_id}")

        # Check if investor exists
        if not investor_ref.get():
            return jsonify({"success": False, "message": "Investor not found!"}), 404

        # Remove the investor
        investor_ref.delete()
        return jsonify({"success": True, "message": "Investor removed successfully!"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/investors')
def investors_page():
    try:
        # Fetch investors from Firebase
        investors_ref = db.reference('investors').get()
        
        # Check if data is available
        if not investors_ref:
            flash("No investors found.", "info")
            return render_template('investors.html', investors=[])

        # Format the data for displaying
        investors = []
        for key, value in investors_ref.items():
            investor = {
                "id": key,
                "investor_name": value.get('investor_name'),
                "role": value.get('role'),
                "contribution": value.get('contribution'),
                "contact_details": value.get('contact_details'),
                "photo_url": value.get('photo_url', "https://via.placeholder.com/150")  # Default image if none exists
            }
            investors.append(investor)

        return render_template('investors.html', investors=investors)

    except Exception as e:
        flash(f"Error fetching investors: {str(e)}", "error")
        return render_template('investors.html', investors=[])
        
 
@app.route('/admin-dash')
@login_required
def admin_dashboard():
    try:
        gallery_ref = db.reference("gallery").get()
        gallery_images = [{"url": image["image_url"]} for image in gallery_ref.values()] if gallery_ref else []
        return render_template("admin_dashboard.html", gallery_images=gallery_images)
    except Exception as e:
        flash(f"Error fetching gallery images: {str(e)}", "error")
        return render_template("admin_dashboard.html", gallery_images=[])

IMAGEBB_API_KEY = "f6230ba4f83a87955248c7ea01f84dd1"
@app.route('/vision-mission')
def vision_mission():
    return render_template('vismis.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/overview')
def company_overview():
    return render_template('company_overview.html')

@app.route('/finance')
def finance_overview():
    return render_template('finance.html')
@app.route('/quality')
def quality():
    return render_template('quality.html')



if __name__ == '__main__':
    app.run(debug=True)
    