from flask import Flask, request, render_template, session, jsonify, redirect
import sqlite3
import json

# Create a Flask web application instance
app = Flask(__name__)

# Set a secret key for session management
app.secret_key = 'serversecretkey'

# Configure the session type and permanence
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False

def get_db_connection():
    """
    Establish a connection to the SQLite database.

    Returns:
        tuple: A tuple containing the connection object and cursor object.
    """
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    return conn, cur

@app.route("/", methods=["GET", "POST"])
def main_page():
    """
    Main page route for displaying food items and managing the shopping cart.

    If a session cart doesn't exist, it's created.
    If a user has already placed an order, they are redirected to the order status page.
    """
    conn, cur = get_db_connection()
    cur.execute('SELECT * FROM fooditems')
    foods = cur.fetchall()

    cur.execute('SELECT * FROM categories')
    categories = cur.fetchall()

    if 'cart' not in session:  # Check if session has a cart
        session['cart'] = []

    phone = session.get('phone')

    if phone:  # Check if the current session has already ordered
        cur.execute('SELECT * FROM Orders WHERE phonenumb=?', (phone,))
        order_details = cur.fetchone()

        if order_details:
            return redirect("/orderstatus")  # Prevent access to the order page if there's an existing order

    if request.method == "POST":  # Handle POST requests
        if "addfood" in request.form:  # Add food to the cart
            cart_list = session['cart']
            cart_list.append(request.form["addfood"])
            session['cart'] = cart_list

            # Redirect back to the main page after adding the food to the cart
            return redirect('/')

        if "food_id" in request.form:  # Display food details when clicking on a grid item
            cur.execute('SELECT food_name, cost, image, description, food_id FROM fooditems WHERE food_id=?', (request.form["food_id"],))
            foodresults = cur.fetchall()

            return render_template("order.html", foods=foods, categories=categories, showing=True, food=foodresults, foodcart=session['cart'], foodlength=len(session['cart']))

    return render_template("order.html", foods=foods, categories=categories, showing=False, foodcart=session['cart'], foodlength=len(session['cart']))

@app.route("/reviews", methods=["GET", "POST"])
def reviews():
    """
    Route for handling reviews. Supports submitting new reviews and displaying existing ones.
    """
    conn, cur = get_db_connection()

    if request.method == "POST":  # Handle form submission for new reviews
        firstname = request.form["firstname"]
        lastname = request.form["lastname"]
        rating = request.form["rating"]
        ratingmessage = request.form["ratingmessage"]

        cur.execute("INSERT INTO Reviews (firstname, lastname, rating, ratingmessage) VALUES(?, ?, ?, ?)", (firstname, lastname, rating, ratingmessage))
        conn.commit()

        # Redirect back to the same page after processing the form
        return redirect('/reviews')

    # Fetch all reviews from the database
    cur.execute('SELECT * FROM Reviews')
    reviews = cur.fetchall()

    return render_template("reviews.html", reviews=reviews)

@app.route("/orderstatus")
def orderstatus():
    """
    Route for tracking order status. Displays the order details and status.
    """
    conn, cur = get_db_connection()

    # Fetch the phone number from the session
    phone = session.get('phone')

    if phone:
        cur.execute('SELECT * FROM Orders WHERE phonenumb=?', (phone,))
        order_details = cur.fetchone()

        if order_details:
            # Convert the foodlist string back to a list
            food_ids = json.loads(order_details[4])
            
            cur.execute('SELECT food_name, cost, image, description FROM fooditems WHERE food_id IN ({})'.format(','.join(['?']*len(food_ids))), food_ids)
            foods = cur.fetchall()
            return render_template("orderstatus.html", order_status=order_details[5], foods=foods, foodcart=session['cart'], foodlength=len(session['cart']))
        else:
            return render_template("orderstatus.html", order_status=None)
    else:
        return render_template("orderstatus.html", order_status=None)

@app.route("/cart", methods=["GET", "POST"])
def cart():
    """
    Route for managing the shopping cart. Allows adding and removing items from the cart.
    """
    conn, cur = get_db_connection()

    if 'cart' not in session:
        session['cart'] = []

    formattedtbl = []

    if request.method == "POST":
        if "removefood" in request.form:
            cart_list = session['cart']

            if request.form["removefood"] in cart_list:
                cart_list.remove(request.form["removefood"])
                session['cart'] = cart_list

            # Redirect back to the cart page after removing the food from the cart
            return redirect('/cart')

    for i in session['cart']:
        cur.execute('SELECT food_name, cost, image, description, food_id FROM fooditems WHERE food_id=?', (i,))
        foodresults = cur.fetchall()
        formattedtbl.append(foodresults[0])
        # Append food items into the table 

    return render_template('cart.html', foodcart=formattedtbl, foodlength=len(session['cart']))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    """
    Route for admin management. Supports confirming, canceling, marking orders as ready, and deleting orders.
    """
    conn, cur = get_db_connection()

    if request.method == "POST":
        if "confirmorder" in request.form:
            # Update the status of an order to "progress," indicating that it's being prepared.
            cur.execute('UPDATE Orders SET status="progress" WHERE orderid=?', (request.form["confirmorder"],))

        if "cancelorder" in request.form:
            # Delete an order from the database, effectively canceling it.
            cur.execute('DELETE FROM Orders WHERE orderid=?', (request.form["cancelorder"],))

        if "readypickup" in request.form:
            # Update the status of an order to "ready" when it's ready for pickup.
            cur.execute('UPDATE Orders SET status="ready" WHERE orderid=?', (request.form["readypickup"],))

        if "pickedup" in request.form:
            # Delete an order from the database when the customer has picked it up.
            cur.execute('DELETE FROM Orders WHERE orderid=?', (request.form["pickedup"],))

        conn.commit()

        # Redirect back to the admin page after performing the action
        return redirect('admin')

    cur.execute('SELECT * FROM Orders')
    results = cur.fetchall()

    cur.execute('SELECT * FROM fooditems')
    foods = cur.fetchall()

    return render_template("admin.html", order=results, foods=foods)

@app.route("/submitorder")
def submit():
    """
    Route for submitting orders. Adds an order to the database and clears the cart.
    """
    conn, cur = get_db_connection()

    data = request.args
    fname = data.get('fname')  # First name
    lname = data.get('lname')  # Last name
    phone = data.get('phone')  # Phone (identifier)

    foods = json.dumps(session['cart'])

    cur.execute("INSERT INTO Orders (firstname, lastname, phonenumb, foodlist, status) VALUES(?, ?, ?, ?, ?)", (fname, lname, str(phone), foods, 'avail'))
    conn.commit()

    # Store the phone number in the session
    session['phone'] = str(phone)

    session['cart'] = []
    return redirect("/orderstatus")

@app.errorhandler(404)
def page_not_found(e):
    """
    Custom error handler for 404 errors. Redirects to the home page.
    """
    return render_template('404.html'), 404

@app.template_filter('to_dict')
def to_dict(my_string):
    """
    Custom template filter to convert a JSON string to a JSON object.
    """
    return json.loads(my_string)

if __name__ == '__main__':
    app.run(debug=True)
