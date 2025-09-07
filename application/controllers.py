from flask import Flask, render_template, redirect, request
from flask import current_app as app  # if u directly import the app, it leadds to cirular loop and go to erroer
#current_app refers to app object(app.py)
#everywhere we can use as app
from .models import *
from .database import db
from sqlalchemy import or_
# Importing the models to use in the controllers
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

@app.route('/')
def home():
    return render_template('main.html')

@app.route("/index", methods=["GET", "POST"])
def index():
    date = request.form.get("date")
    list_of_users = User.query.filter_by(type='user').all()

    for _ in list_of_users:
        date_by_user = User.parking_timestamp = datetime.utcnow() + timedelta(hours=5, minutes=30)
        if date_by_user == date:
            return render_template("index.html", list_of_users=list_of_users, date=date)
    return render_template("index.html", list_of_users=list_of_users, date=None)



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
            vehicle_num = request.form["vehicle_num"].strip()
            
            # Validate vehicle number
            if not vehicle_num:
                return "Vehicle registration number is required."
            
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

    #GET request
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
            
            parking_duration = reservation.leaving_timestamp - reservation.parking_timestamp
            hours_parked = parking_duration.total_seconds() / 3600
            total_cost = hours_parked * reservation.cost_per_unit_time
            
            return f"Spot {reservation.spot_id} released. Duration is {round(hours_parked, 2)} hours, Cost is ₹{round(total_cost, 2)}, Released is {reservation.leaving_timestamp.strftime('%Y-%m-%d %H:%M')} <a href='/user_dashboard/{user_id}'>Go to Dashboard</a>"
            
        except Exception as e:
            db.session.rollback()
            return f"An error occurred while releasing the spot: {str(e)}"
    
    #GET request
    spot = ParkingSpot.query.get(reservation.spot_id)
    lot = ParkingLot.query.get(spot.lot_id) if spot else None
    
    parking_duration = (datetime.utcnow() + timedelta(hours=5, minutes=30)) - reservation.parking_timestamp
    hours_parked = parking_duration.total_seconds() / 3600
    total_cost = hours_parked * reservation.cost_per_unit_time
    
    return render_template("release_spot.html", this_user=this_user, reservation=reservation, spot=spot, lot=lot, hours_parked=round(hours_parked, 2), total_cost=round(total_cost, 2)) 

@app.route("/user_dashboard/<int:user_id>")
def user_dashboard(user_id):
    this_user = User.query.filter_by(id=user_id).first()
    
    # Get search parameters
    search_query = request.args.get('search_query', '').strip()
    
    # Default: show parking lots in user's pincode
    if not search_query:
        parking_lots = ParkingLot.query.filter_by(pin_code=this_user.pincode).all()
        search_type = 'default'
    else:
        # Auto-detect search type: if query is numeric, search by pincode, otherwise search by location
        if search_query.isdigit():
            # Search by pincode
            parking_lots = ParkingLot.query.filter(ParkingLot.pin_code.ilike(f'%{search_query}%')).all()
            search_type = 'pincode'
        else:
            # Search by location name and address
            parking_lots = ParkingLot.query.filter(
                or_(
                    ParkingLot.prime_location_name.ilike(f'%{search_query}%'),
                    ParkingLot.address.ilike(f'%{search_query}%')
                )
            ).all()
            search_type = 'location'
    
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
            'total_spots': lot.max_spots,
            'pin_code': lot.pin_code
        })
    
    user_reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.parking_timestamp.desc()).all()
    
    updated_reservations = []
    for reservation in user_reservations:
        spot = ParkingSpot.query.get(reservation.spot_id)
        lot = ParkingLot.query.get(spot.lot_id) if spot else None
        
        updated_reservations.append({
            'id': reservation.id,
            'location': lot.prime_location_name if lot else 'Unknown',
            'vehicle_number': reservation.vehicle_num,
            'timestamp': reservation.parking_timestamp.strftime('%Y-%m-%d %H:%M'),
            'status': 'Active' if not reservation.leaving_timestamp else 'Completed',
            'spot_id': reservation.spot_id,
            'lot_id': lot.id if lot else None
        })
    
    return render_template("user_dashboard.html", this_user=this_user, parking_lots=updated_lots, reservations=updated_reservations, search_query=search_query, search_type=search_type)

@app.route("/admin_dashboard")
def admin_dashboard():
    this_user = User.query.filter_by(type='admin').first()
    all_lots = ParkingLot.query.all()

    updated_lots = []
    for lot in all_lots:
        spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
        occupied_count = sum(1 for s in spots if s.status == 'occupied')
        total_spots = len(spots)

        updated_lots.append({
            'id': lot.id,
            'prime_location_name': lot.prime_location_name,
            'address': lot.address,
            'price': lot.price,
            'pin_code': lot.pin_code,
            'max_spots': lot.max_spots,
            'occupied_spots': occupied_count,
            'total_spots': total_spots,
            'spots': [{'id': s.id, 'status': s.status} for s in spots]
        })

    return render_template("admin_dashboard.html", this_user=this_user, parking_lots=updated_lots)

@app.route("/users")
def users():
    this_user = User.query.filter_by(type='admin').first()
    all_users = User.query.filter(User.type != 'admin').all()
    
    return render_template("users.html", this_user=this_user, users=all_users)


@app.route("/search")
def search():
    this_user = User.query.filter_by(type='admin').first()
    search_by = request.args.get('search_by', '')
    search_string = request.args.get('search_string', '')
    
    search_results = {'users': [], 'parking_lots': [], 'parking_spots': [], 'reservations': []}
    
    if search_by and search_string:
        if search_by == 'user_id':
            try:
                search_results['users'] = User.query.filter(User.id == int(search_string), User.type != 'admin').all()
            except ValueError:
                pass
        elif search_by == 'user_name':
            search_results['users'] = User.query.filter(User.type != 'admin', db.or_(User.first_name.ilike(f'%{search_string}%'), User.last_name.ilike(f'%{search_string}%'))).all()
        elif search_by == 'user_email':
            search_results['users'] = User.query.filter(User.type != 'admin', User.email.ilike(f'%{search_string}%')).all()
        elif search_by == 'user_vehicle':
            search_results['users'] = User.query.filter(User.type != 'admin', User.vehicle_reg.ilike(f'%{search_string}%')).all()
        elif search_by == 'parking_lot_id':
            try:
                lots = ParkingLot.query.filter(ParkingLot.id == int(search_string)).all()
                for lot in lots:
                    lot.spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
                    lot.occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='occupied').count()
                search_results['parking_lots'] = lots
            except ValueError:
                pass
        elif search_by == 'parking_lot_name':
            lots = ParkingLot.query.filter(ParkingLot.prime_location_name.ilike(f'%{search_string}%')).all()
            for lot in lots:
                lot.spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
                lot.occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='occupied').count()
            search_results['parking_lots'] = lots
        elif search_by == 'parking_lot_address':
            lots = ParkingLot.query.filter(ParkingLot.address.ilike(f'%{search_string}%')).all()
            for lot in lots:
                lot.spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
                lot.occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='occupied').count()
            search_results['parking_lots'] = lots
        elif search_by == 'parking_lot_pincode':
            lots = ParkingLot.query.filter(ParkingLot.pin_code.ilike(f'%{search_string}%')).all()
            for lot in lots:
                lot.spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
                lot.occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='occupied').count()
            search_results['parking_lots'] = lots
        elif search_by == 'parking_spot_id':
            try:
                search_results['parking_spots'] = ParkingSpot.query.filter(ParkingSpot.id == int(search_string)).all()
            except ValueError:
                pass
        elif search_by == 'parking_spot_status':
            search_results['parking_spots'] = ParkingSpot.query.filter(ParkingSpot.status.ilike(f'%{search_string}%')).all()
        elif search_by == 'reservation_id':
            try:
                search_results['reservations'] = Reservation.query.filter(Reservation.id == int(search_string)).all()
            except ValueError:
                pass
        elif search_by == 'reservation_vehicle':
            search_results['reservations'] = Reservation.query.filter(Reservation.vehicle_num.ilike(f'%{search_string}%')).all()
    
    return render_template("search.html", this_user=this_user, search_results=search_results, search_by=search_by, search_string=search_string)

@app.route("/edit_lot/<int:lot_id>", methods=["GET", "POST"])
def edit_lot(lot_id):
    this_user = User.query.filter_by(type='admin').first()
    lot = ParkingLot.query.get_or_404(lot_id)
    
    if request.method == "POST":
        lot.prime_location_name = request.form.get("prime_location_name")
        lot.address = request.form.get("address")
        lot.pin_code = request.form.get("pin_code")
        lot.price = float(request.form.get("price"))
        new_max_spots = int(request.form.get("max_spots"))

        current_max_spots = lot.max_spots
        lot.max_spots = new_max_spots

        if new_max_spots > current_max_spots:
            for _ in range(current_max_spots, new_max_spots):
                spot = ParkingSpot(lot_id=lot.id, status="available")
                db.session.add(spot)

        elif new_max_spots < current_max_spots:
            spots_to_remove = ParkingSpot.query.filter_by(
                lot_id=lot.id, status="available"
            ).limit(current_max_spots - new_max_spots).all()

            for spot in spots_to_remove:
                db.session.delete(spot)

        db.session.commit()
        return redirect("/admin_dashboard")
    
    return render_template("edit_lot.html", this_user=this_user, lot=lot)

@app.route("/delete_slot/<int:spot_id>", methods=["GET", "POST"])
def delete_slot(spot_id):
    this_user = User.query.filter_by(type='admin').first()
    spot = ParkingSpot.query.get_or_404(spot_id)
    lot = ParkingLot.query.get(spot.lot_id)
    
    if request.method == "POST":
        if spot.status == 'occupied':
            return "Cannot delete occupied spot!"
        else:
            try:
                db.session.delete(spot)
                db.session.commit()
                return redirect("/admin_dashboard")
            except Exception as e:
                db.session.rollback()
                return f"Error deleting spot: {str(e)}"
    
    return render_template("delete_slot.html", this_user=this_user, spot=spot, lot=lot)

@app.route("/delete_lot/<int:lot_id>", methods=["GET", "POST"])
def delete_lot(lot_id):
    this_user = User.query.filter_by(type='admin').first()
    lot = ParkingLot.query.get_or_404(lot_id)
    
    if request.method == "POST":
        occupied_spots = ParkingSpot.query.filter_by(lot_id=lot_id, status='occupied').count()
        if occupied_spots > 0:
            return "Cannot delete lot with occupied spots!"
        else:
            try:
                db.session.delete(lot)
                db.session.commit()
                return redirect("/admin_dashboard")
            except Exception as e:
                db.session.rollback()
                return f"Error deleting lot: {str(e)}"
    
    return render_template("delete_lot.html", this_user=this_user, lot=lot)

@app.route("/edit_profile/<int:user_id>", methods=["GET", "POST"])
def edit_profile(user_id):
    this_user = User.query.filter_by(id=user_id).first()
    if request.method == "POST":
            exist_email = User.query.filter_by(email=request.form["email"]).first()
            if exist_email and exist_email.id != user_id:
                return "Email already registered by another user"
            
            exist_vehicle = User.query.filter_by(vehicle_reg=request.form["vehicle_reg"]).first()
            if exist_vehicle and exist_vehicle.id != user_id:
                return "Vehicle registration number already registered by another user"
            
            exist_phone = User.query.filter_by(phone_number=request.form["phone_number"]).first()
            if exist_phone and exist_phone.id != user_id:
                return "Phone number already registered by another user"
            
            this_user.first_name = request.form["first_name"]
            this_user.last_name = request.form["last_name"]
            this_user.email = request.form["email"]
            this_user.vehicle_reg = request.form["vehicle_reg"]
            this_user.address = request.form["address"]
            this_user.pincode = request.form["pincode"]
            this_user.phone_number = request.form["phone_number"]
            this_user.gender = request.form["gender"]
            this_user.age = int(request.form["age"]) if request.form["age"] else None
            
            db.session.commit()
            
            if this_user.type == "admin":
                return redirect("/admin_dashboard")
            else:
                return redirect(f"/user_dashboard/{user_id}")
    
    return render_template("edit_profile.html", this_user=this_user)

@app.route("/occupied_details/<int:spot_id>")
def occupied_details(spot_id):
    this_user = User.query.filter_by(type='admin').first()
    spot = ParkingSpot.query.get_or_404(spot_id)
    lot = ParkingLot.query.get(spot.lot_id)
    
    if spot.status != 'occupied':
        return "This spot is not occupied!"
    
    reservation = Reservation.query.filter_by(spot_id=spot_id, leaving_timestamp=None).first()
    if not reservation:
        return "No active reservation found for this spot!"
    
    user = User.query.get(reservation.user_id)
    
    return render_template("occupied_details.html", this_user=this_user, spot=spot, lot=lot, reservation=reservation, user=user)

@app.route("/admin_summary")
def admin_summary():
    available_spots = len(ParkingSpot.query.filter_by(status="available").all())
    occupied_spots = len(ParkingSpot.query.filter_by(status="occupied").all())
    total_lots = len(ParkingLot.query.all())
    this_user = User.query.filter_by(type='admin').first() 

    labels = ["Available", "Occupied"]
    sizes = [available_spots, occupied_spots]
    colors = ["green", "red"]

    if sum(sizes) > 0:      # start creating charts only if there are spots
        plt.figure(figsize=(8, 6))
        plt.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90)
        plt.title("Parking Spot Status")
        plt.axis('equal')
        plt.savefig("static/pie_chart.png", dpi=300, bbox_inches='tight')
        plt.clf()
    else:
        plt.figure(figsize=(8, 6)) #empty ones
        plt.pie([1], labels=['No Data'], colors=['gray'], autopct="%1.1f%%")
        plt.title("Parking Spot Status")
        plt.axis('equal')
        plt.savefig("static/pie_chart.png", dpi=300, bbox_inches='tight')
        plt.clf()

    plt.figure(figsize=(10, 6))
    plt.bar(labels, sizes, color=colors)
    plt.xlabel("Parking Spot Status")
    plt.ylabel("Number of Spots")
    plt.title("Parking Spot Distribution")
    plt.savefig("static/bar_chart.png", dpi=300, bbox_inches='tight')
    plt.clf()

    parking_lots = ParkingLot.query.all()
    lot_names = []
    lot_revenues = []

    for lot in parking_lots:
        lot_names.append(lot.prime_location_name)
        completed_reservations = Reservation.query.join(ParkingSpot).filter(
            ParkingSpot.lot_id == lot.id,
            Reservation.leaving_timestamp.isnot(None)
        ).all()

        lot_revenue = 0
        for reservation in completed_reservations:
            try:
                duration = (reservation.leaving_timestamp - reservation.parking_timestamp).total_seconds() / 3600
                if not np.isnan(duration) and duration > 0:
                    lot_revenue += reservation.cost_per_unit_time * duration
            except:
                continue

        lot_revenues.append(round(lot_revenue, 2))

    if lot_names and any(revenue > 0 for revenue in lot_revenues):
        plt.figure(figsize=(12, 6))
        plt.bar(lot_names, lot_revenues, color='blue', alpha=0.7)
        plt.xlabel("Parking Lots")
        plt.ylabel("Revenue in ₹")
        plt.title("Revenue from Each Parking Lot")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig("static/revenue_chart.png", dpi=300, bbox_inches='tight')
        plt.clf()
    else:
        plt.figure(figsize=(12, 6))    #empty ones
        plt.bar(['No Revenue Data'], [1], color='gray', alpha=0.7)
        plt.xlabel("Parking Lots")
        plt.ylabel("Revenue in ₹")
        plt.title("Revenue from Each Parking Lot")
        plt.tight_layout()
        plt.savefig("static/revenue_chart.png", dpi=300, bbox_inches='tight')
        plt.clf()

    return render_template("admin_summary.html", available=available_spots, occupied=occupied_spots, total_lots=total_lots, this_user=this_user) 



@app.route("/user_summary/<int:user_id>")
def user_summary(user_id):
    this_user = User.query.get(user_id)
    if not this_user:
        return "User not found"

    reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.parking_timestamp.desc()).limit(10).all()

    spot_labels = []
    costs = []
    total_cost = 0

    for idx, r in enumerate(reservations[::-1]):
        if r.leaving_timestamp:
            hours = (r.leaving_timestamp - r.parking_timestamp).total_seconds() / 3600
            cost = round(hours * r.cost_per_unit_time, 2)
            costs.append(cost)
            total_cost += cost
            spot_labels.append(f"#{idx + 1}")
        else:
            costs.append(0)
            spot_labels.append(f"#{idx + 1}")

    plt.figure(figsize=(10, 5))
    bars = plt.bar(spot_labels, costs, color='skyblue')
    plt.xlabel("Parking Session")
    plt.ylabel("Cost in ₹")
    plt.title("Previous Parking Session Costs")
    plt.tight_layout()

    for bar, val in zip(bars, costs):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{val}", ha='center', va='bottom')

    static_path = os.path.join(app.root_path, 'static', 'user_bar.png')
    plt.savefig(static_path)
    plt.close()

    return render_template("user_summary.html", this_user=this_user, total_cost=round(total_cost, 2))
