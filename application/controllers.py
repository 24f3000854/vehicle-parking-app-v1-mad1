from flask import Flask, render_template, redirect, request
from flask import current_app as app  # if u directly import the app, it leadds to cirular loop and go to erroer
#current_app refers to app object(app.py)
#everywhere we can use as app
from .models import *
# Importing the models to use in the controllers
from datetime import datetime, timedelta

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        pwd = request.form["pwd"] 
        this_user = User.query.filter_by(email = email).first()  #left table is User, right table is form data
        if this_user:
            if this_user.pwd == pwd:
                if this_user.type == "admin":
                    return redirect("/admin_dashboard")
                else:
                    return redirect(f"/user_dashboard/{this_user.id}")
            else:
                return "password is incorrect"
        else:
            return "email(user) does not exist"
    return render_template("login.html")
 
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        confirm_email = request.form["confirm_email"]
        vehicle_reg = request.form["vehicle_reg"]
        address = request.form["address"]
        pincode = request.form["pincode"]
        phone_number = request.form["phone_number"]
        pwd = request.form["pwd"]
        confirm_password = request.form["confirm_pwd"]
        gender = request.form["gender"]
        age = request.form["age"]
        if email != confirm_email:
            return "Email addresses do not match"
        if pwd != confirm_password:
            return "Passwords do not match"
        user_email = User.query.filter_by(email=email).first()
        user_vehicle = User.query.filter_by(vehicle_reg=vehicle_reg).first()
        user_phone = User.query.filter_by(phone_number=phone_number).first()
        if user_email:
            return "Email already registered"
        elif user_vehicle:
            return "Vehicle registration number already registered"
        elif user_phone:
            return "Phone number already registered"
        else:
            new_user = User(first_name=first_name,last_name=last_name, email=email, pwd=pwd, vehicle_reg=vehicle_reg, address=address ,pincode=pincode, phone_number=phone_number, gender=gender, age=age)
            db.session.add(new_user)
            db.session.commit()
        return redirect("/login")
    return render_template("register.html")

@app.route("/new-lot", methods=["GET", "POST"])
def new_lot():
    this_user = User.query.filter_by(type='admin').first()

    if request.method == "POST":
        prime_location_name = request.form.get("prime_location_name")
        price = float(request.form.get("price"))
        address = request.form.get("address")
        pin_code = request.form.get("pin_code")
        max_spots = int(request.form.get("max_spots"))
        new_lot = ParkingLot(prime_location_name=prime_location_name, price=price, address=address, pin_code=pin_code, max_spots=max_spots)
        db.session.add(new_lot)
        db.session.commit()
        
        for i in range(max_spots):  #creates parking spots 0 to max_spots-1
            spot = ParkingSpot(lot_id=new_lot.id, status="available")
            db.session.add(spot)
            db.session.commit()
    
        return redirect("/admin_dashboard")

    return render_template("new-lot.html", this_user=this_user)


@app.route("/book-spot/<int:user_id>/<int:lot_id>", methods=["GET", "POST"])
def book_spot(user_id, lot_id):
    this_user = User.query.get(user_id)

    if request.method == "POST":
        try:
            spot_id = int(request.form["spot_id"])
            lot_id = int(request.form["lot_id"])
            vehicle_num = request.form["vehicle_num"]
            spot = ParkingSpot.query.get(spot_id)
            lot = ParkingLot.query.get(lot_id)
            spot.status = 'occupied'
            ist_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
            new_reservation = Reservation(spot_id=spot_id, user_id=user_id, parking_timestamp=ist_time, cost_per_unit_time=lot.price, vehicle_num=vehicle_num)
            db.session.add(new_reservation)
            db.session.commit()

            return redirect(f"/user_dashboard/{user_id}")

        except ValueError:
            return "Invalid form data provided."
        except Exception as e:
            db.session.rollback()
            return f"An error occurred: {str(e)}"

    # GET request
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        return "Parking lot not found."
    
    available_spots = ParkingSpot.query.filter_by(status='available', lot_id=lot_id).all()
    
    if not available_spots:
        return "No available spots in this parking lot."

    return render_template("book_spot.html", this_user=this_user, available_spots=available_spots, lot_id=lot_id, lot_price=lot.price)


@app.route("/release-spot/<int:user_id>/<int:reservation_id>", methods=["GET", "POST"])
def release_spot(user_id, reservation_id):
    this_user = User.query.get(user_id)
    
    reservation = Reservation.query.get(reservation_id)
    if not reservation or reservation.user_id != user_id:
        return "Invalid reservation!..."
    
    if request.method == "POST":
        try:
            reservation.leaving_timestamp = datetime.utcnow() + timedelta(hours=5, minutes=30)
            spot = ParkingSpot.query.get(reservation.spot_id) #make it available
            if spot:
                spot.status = 'available'
            db.session.commit()
            
            # Calculate final cost
            parking_duration = reservation.leaving_timestamp - reservation.parking_timestamp
            hours_parked = parking_duration.total_seconds() / 3600
            total_cost = hours_parked * reservation.cost_per_unit_time
            
            return f"Spot {reservation.spot_id} released. Duration is {round(hours_parked, 2)} hours, Cost is ₹{round(total_cost, 2)}, Released is {reservation.leaving_timestamp.strftime('%Y-%m-%d %H:%M')} <a href='/user_dashboard/{user_id}'>Go to Dashboard</a>"
            
        except Exception as e:
            db.session.rollback()
            return f"An error occurred while releasing the spot: {str(e)}"
    
    # GET request
    spot = ParkingSpot.query.get(reservation.spot_id)
    lot = ParkingLot.query.get(spot.lot_id) if spot else None
    
    parking_duration = (datetime.utcnow() + timedelta(hours=5, minutes=30)) - reservation.parking_timestamp
    hours_parked = parking_duration.total_seconds() / 3600
    total_cost = hours_parked * reservation.cost_per_unit_time
    
    return render_template("release_spot.html", this_user=this_user, reservation=reservation, spot=spot, lot=lot, hours_parked=round(hours_parked, 2), total_cost=round(total_cost, 2)) 

@app.route("/user_dashboard/<int:user_id>")
def user_dashboard(user_id):
    this_user = User.query.filter_by(id=user_id).first()
    # Geting parking's pin_code
    parking_lots = ParkingLot.query.filter_by(pin_code=this_user.pincode).all()
    
    updated_lots = []
    for lot in parking_lots:
        available_count = ParkingSpot.query.filter_by(lot_id=lot.id, status='available').count()
        occupied_count = ParkingSpot.query.filter_by(lot_id=lot.id, status='occupied').count()
        updated_lots.append({
            'id': lot.id,
            'address': lot.address,
            'prime_location_name': lot.prime_location_name,
            'price': lot.price,
            'available_spots': available_count,
            'occupied_spots': occupied_count,
            'total_spots': lot.max_spots
        })
    
    user_reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.parking_timestamp.desc()).all()
    
    updated_reservations = []
    for reservation in user_reservations:
        spot = ParkingSpot.query.get(reservation.spot_id)
        lot = ParkingLot.query.get(spot.lot_id) if spot else None
        
        updated_reservations.append({
            'id': reservation.id,
            'location': lot.prime_location_name if lot else 'Unknown',
            'vehicle_number': this_user.vehicle_reg,
            'timestamp': reservation.parking_timestamp.strftime('%Y-%m-%d %H:%M'),
            'status': 'Active' if not reservation.leaving_timestamp else 'Completed',
            'spot_id': reservation.spot_id,
            'lot_id': lot.id if lot else None
        })
    
    return render_template("user_dashboard.html", this_user=this_user, parking_lots=updated_lots, reservations=updated_reservations)

@app.route("/admin_dashboard")
def admin_dashboard():
    this_user = User.query.filter_by(type='admin').first()
    all_lots = ParkingLot.query.all()

    updated_lots = []
    for lot in all_lots:
        spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
        occupied_count = sum(1 for s in spots if s.status == 'occupied')

        updated_lots.append({
            'id': lot.id,
            'prime_location_name': lot.prime_location_name,
            'address': lot.address,
            'price': lot.price,
            'pin_code': lot.pin_code,
            'max_spots': lot.max_spots,
            'occupied_spots': occupied_count,
            'spots': [{'id': s.id, 'status': s.status} for s in spots]
        })

    return render_template("admin_dashboard.html", this_user=this_user, parking_lots=updated_lots)
