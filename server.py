import os, requests
from flask import Flask, request, abort, json, Response
from database import init_db, db_session
from models import Order
from sqlalchemy.exc import OperationalError

app = Flask(__name__)
app.config["ENV"] = "production"
app.config["DEBUG"] = False

def generate_error_message(message):
    return Response(response=json.dumps({"error": message}), status=400, mimetype='application/json')

def is_valid_coordinate(coordinate):
    # check length
    if not isinstance(coordinate, list) or len(coordinate)!=2:
        return False
    # check data type and value range
    for val, (lower_bound, upper_bound) in zip(coordinate, [(-90, 90), (-180, 180)]):
        if not isinstance(val, str): return False
        try:
            val = float(val)
            if not (lower_bound <= val <= upper_bound): return False
        except ValueError:
            return False
    return True

def is_valid_value(val, lower_bound):
    if not isinstance(val, str):
        return False
    try:
        val = int(val)
        if val < lower_bound: return False
    except ValueError:
        return False
    return True

def get_distance(origin, destination):
    origins = ",".join(origin)
    destinations = ",".join(destination)
    params = {
        "origins": origins,
        "destinations": destinations,
        "key": os.environ["APIKEY"]
    }
    response = requests.get("https://maps.googleapis.com/maps/api/distancematrix/json", params=params).json()
    # check if the api key is valid
    if response["status"] != "OK":
        raise Exception(response["error_message"])
    row = response["rows"][0]
    element = row["elements"][0]
    # check if distance can be found
    if element["status"] != "OK":
        raise Exception(element["status"])
    return element["distance"]["value"]


def place_order(data):
    # check if the required arguments exist
    try:
        origin = data["origin"]
        destination = data["destination"]
    except KeyError:
        app.logger.error(f"Missing required arguments: {data}/data")
        return generate_error_message("Missing required arguments.")
    # check if the coordinates are valid
    if not is_valid_coordinate(origin) or not is_valid_coordinate(destination):
        app.logger.error(f"Invalid coordinates: {origin}/origin, {destination}/destination")
        return generate_error_message("Invalid coordinates.")
    # create an order
    try:
        distance = get_distance(origin, destination)
    except Exception as e:
        return generate_error_message(str(e))
    _order = Order(distance, "UNASSIGNED")
    db_session.add(_order)
    db_session.commit()
    message = f"{_order} is created"
    app.logger.info(message)
    return Response(response=json.dumps(_order.to_dict()), status=200, mimetype='application/json')

def get_order_list(args):
    # check if the required arguments exist
    page, limit = args.get("page"), args.get("limit")
    if page is None or limit is None:
        app.logger.error(f"Missing required arguments: {page}/page, {limit}/limit")
        return generate_error_message("Missing required arguments.")
    # check if the values are valid
    is_valid_page = is_valid_value(page, 0)
    is_valid_limit = is_valid_value(limit, 1)
    if not is_valid_limit or not is_valid_page:
        app.logger.error(f"Invalid values: {page}/page, {limit}/limit")
        return generate_error_message("Invalid values.")
    page, limit = int(page), int(limit)
    lower_bound, upper_bound = page*limit, (page+1)*limit
    _orders = db_session.query(Order).filter(Order.id>lower_bound, Order.id<=upper_bound).all()
    return Response(response=json.dumps([_order.to_dict() for _order in _orders]), status=200, mimetype='application/json')

@app.route("/orders", methods = ["POST", "GET"])
def place_get_order():
    if request.method == "POST":
        return place_order(json.loads(request.data))
    elif request.method == "GET":
        app.logger.info(request.url)
        return get_order_list(request.args)

@app.route("/orders/<id>", methods = ["PATCH"])
def take_order(id):
    _order = db_session.query(Order).filter(Order.id==id).first()
    # check if the order exists
    if _order is None:
        return generate_error_message("The order doesn't exist.")
    # check if the order is already taken
    elif _order.status == "TAKEN":
        return generate_error_message("Oops! The order has been taken.")
    try:
        # try to lock the order
        _order = db_session.query(Order).filter(Order.id==id, Order.status=="UNASSIGNED").with_for_update(nowait=True, of=Order).first()
        if _order is None:
            db_session.rollback()
            return generate_error_message("Oops! The order has been taken.")
        else:
            _order.status = "TAKEN"
            db_session.commit()
    except OperationalError:
        # someone has locked the order, assuming this one will be taken
        return generate_error_message("Oops! The order has been taken.")
    message = f"Order {_order.id} is successfully taken."
    app.logger.info(message)
    return Response(response=json.dumps({"status": "SUCCESS"}), status=200, mimetype='application/json')

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)
