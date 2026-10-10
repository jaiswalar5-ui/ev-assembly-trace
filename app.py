from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_login import LoginManager, login_required, current_user
from models import db, User, Batch, Product, ProductionEvent, Station, TestResult, Defect, TestLimit
from auth import auth, role_required
import time
import random
from datetime import datetime, timedelta
from sqlalchemy import func

app = Flask(__name__)
import logging
logging.basicConfig(filename='flask_errors.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
app.config['SECRET_KEY'] = 'dev-secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smart_assembly.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

import traceback
@app.errorhandler(Exception)
def handle_exception(e):
    with open("LAST_ERROR.txt", "w") as f:
        f.write(traceback.format_exc())
    return "Internal Server Error (Check LAST_ERROR.txt)", 500

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(auth)

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    # KPI - Overall
    total_products = Product.query.count()
    passed = Product.query.filter_by(result='APPROVED').count()
    rejected = Product.query.filter_by(result='REJECTED').count()
    in_progress = Product.query.filter(Product.status != 'COMPLETED', Product.status != 'FAILED').count()
    
    pass_rate = round((passed / total_products * 100) if total_products > 0 else 0, 1)
    fail_rate = round((rejected / total_products * 100) if total_products > 0 else 0, 1)
    
    # Simple Cycle Time Estimation
    events = ProductionEvent.query.all()
    avg_cycle_time = "4.2 mins"
    
    # Station KPIs
    stations = Station.query.all()
    station_stats = []
    for s in stations:
        in_station = Product.query.filter_by(current_station=s.name).count()
        defect_count = Defect.query.filter_by(station_id=s.id).count()
        station_stats.append({
            'name': s.name,
            'active': in_station > 0,
            'in_station': in_station,
            'defects': defect_count
        })
        
    active_stations = sum(1 for s in station_stats if s['active'])
    idle_stations = len(stations) - active_stations
    
    # Quality KPIs
    total_defects = Defect.query.count()
    common_defect = db.session.query(Defect.reason, func.count(Defect.id)).group_by(Defect.reason).order_by(func.count(Defect.id).desc()).first()
    common_defect_name = common_defect[0] if common_defect and common_defect[0] else "None"
    
    # OEE
    availability = 92.5
    performance = 88.0
    quality = pass_rate if pass_rate > 0 else 98.2
    overall_oee = round((availability * performance * quality) / 10000, 1)
    
    # Charts Data
    # 1. Production by day
    # Mock data for simplicity
    prod_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    prod_data = [150, 230, 224, 218, 235, 140, 50]
    
    # 2. Pass vs Fail
    pass_fail_data = [passed, rejected]
    
    # 3. Defects by station
    defects_by_station_labels = [s['name'] for s in station_stats]
    defects_by_station_data = [s['defects'] for s in station_stats]
    
    # 4. OEE Trend
    oee_trend_data = [80, 82, 85, 84, 88, overall_oee]
    
    # 5. Defect Categories
    defect_categories = db.session.query(Defect.reason, func.count(Defect.id)).group_by(Defect.reason).all()
    cat_labels = [c[0] if c[0] else 'Other' for c in defect_categories]
    cat_data = [c[1] for c in defect_categories]

    return render_template('dashboard.html', 
        total_products=total_products, passed=passed, rejected=rejected, in_progress=in_progress,
        pass_rate=pass_rate, fail_rate=fail_rate, avg_cycle_time=avg_cycle_time,
        active_stations=active_stations, idle_stations=idle_stations, throughput="45 units/hr",
        total_defects=total_defects, common_defect_name=common_defect_name,
        availability=availability, performance=performance, quality=quality, overall_oee=overall_oee,
        station_stats=station_stats,
        prod_labels=prod_labels, prod_data=prod_data, pass_fail_data=pass_fail_data,
        defects_by_station_labels=defects_by_station_labels, defects_by_station_data=defects_by_station_data,
        oee_trend_data=oee_trend_data, cat_labels=cat_labels, cat_data=cat_data
    )

@app.route('/production_line')
@login_required
def production_line():
    stations = Station.query.all()
    if not stations:
        for name in ['Registration', 'Assembly', 'Inspection', 'Functional Test', 'Final QA']:
            db.session.add(Station(name=name))
        db.session.commit()
        stations = Station.query.all()
    products_in_line = Product.query.filter(Product.status != 'COMPLETED', Product.status != 'FAILED').all()
    
    station_details = []
    for s in stations:
        count = sum(1 for p in products_in_line if p.current_station == s.name)
        status = "Active" if count > 0 else "Idle"
        station_details.append({'name': s.name, 'count': count, 'status': status})
        
    return render_template('production_line.html', stations=station_details, products=products_in_line)

@app.route('/api/simulate/start', methods=['POST'])
@login_required
def simulate_start():
    batch = Batch.query.filter_by(status='Active').first()
    if not batch:
        batch = Batch(batch_number=f"BATCH-{int(time.time())}", product_type="Standard EV Module")
        db.session.add(batch)
        db.session.commit()
        
    last_product = Product.query.order_by(Product.id.desc()).first()
    new_id_num = 1001 if not last_product else int(last_product.serial_number.split('-')[-1]) + 1
    serial_number = f"EV-MOD-{new_id_num}"
    
    product = Product(serial_number=serial_number, batch_id=batch.id, status='REGISTERED', current_station='Registration', result='Pending')
    db.session.add(product)
    db.session.commit()
    
    return jsonify({"product_id": product.id, "serial_number": product.serial_number})

@app.route('/api/simulate/step/<int:product_id>', methods=['POST'])
@login_required
def simulate_step(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    stations = ['Registration', 'Assembly', 'Inspection', 'Functional Test', 'Final QA']
    if product.status == 'COMPLETED':
        return jsonify({"message": "Product is already completed", "status": "COMPLETED"})

    current_index = stations.index(product.current_station) if product.current_station in stations else -1
    if product.status in ['REGISTERED', 'WAITING', 'IDLE', 'COMPLETED']:
        product.status = 'RUNNING'
        station = Station.query.filter_by(name=product.current_station).first()
        event = ProductionEvent(
            product_id=product.id,
            station_id=station.id,
            user_id=current_user.id,
            status='STARTED'
        )
        db.session.add(event)
        db.session.commit()
        return jsonify({
            "message": f"Started at {product.current_station}",
            "status": product.status,
            "station": product.current_station,
            "wait_time": random.randint(2, 5)
        })

    elif product.status == 'RUNNING':
        station = Station.query.filter_by(name=product.current_station).first()
        event = ProductionEvent(
            product_id=product.id,
            station_id=station.id,
            user_id=current_user.id,
            status='COMPLETED'
        )
        db.session.add(event)

        if product.current_station == 'Functional Test':
            limits = TestLimit.query.all()
            for limit in limits:
                if random.random() < 0.9:
                    value = random.uniform(limit.min_value or 0, limit.max_value or 100)
                elif random.random() < 0.5 and limit.min_value is not None:
                    value = limit.min_value - random.uniform(1, 10)
                else:
                    value = (limit.max_value or 100) + random.uniform(1, 10)

                passed = True
                reason = None
                if limit.min_value is not None and value < limit.min_value:
                    passed = False
                    reason = 'Under-voltage' if limit.parameter == 'Voltage' else 'Below minimum'
                if limit.max_value is not None and value > limit.max_value:
                    passed = False
                    if limit.parameter == 'Voltage':
                        reason = 'Over-voltage'
                    elif limit.parameter == 'Temperature':
                        reason = 'Overheating'
                    elif limit.parameter == 'Cell Balance':
                        reason = 'Cell imbalance'
                    else:
                        reason = 'Above maximum'
                if limit.parameter == 'Insulation Resistance' and not passed:
                    reason = 'Insulation failure'

                db.session.add(TestResult(
                    product_id=product.id,
                    parameter=limit.parameter,
                    value=value,
                    passed=passed
                ))
                if not passed:
                    db.session.add(Defect(
                        product_id=product.id,
                        batch_id=product.batch_id,
                        station_id=station.id,
                        parameter=limit.parameter,
                        actual_value=str(round(value, 2)),
                        expected_value=f"{limit.min_value} - {limit.max_value}",
                        reason=reason,
                        description=f"Test failed for {limit.parameter}",
                        severity='High' if limit.parameter in ['Voltage', 'Insulation Resistance'] else 'Medium'
                    ))

        elif product.current_station == 'Assembly' and random.random() < 0.05:
            db.session.add(Defect(
                product_id=product.id,
                batch_id=product.batch_id,
                station_id=station.id,
                parameter='Assembly',
                actual_value='Mismatched Parts',
                expected_value='Correct Parts',
                reason='Assembly mismatch',
                description='Incorrect components assembled.',
                severity='Medium'
            ))

        if current_index + 1 < len(stations):
            product.current_station = stations[current_index + 1]
            product.status = 'WAITING'
        else:
            product.status = 'COMPLETED'
            defects = Defect.query.filter_by(product_id=product.id).all()
            product.result = 'REJECTED' if defects else 'APPROVED'

        db.session.commit()
        return jsonify({
            "message": f"Moved to {product.current_station}",
            "status": product.status,
            "station": product.current_station,
            "wait_time": 0
        })

@app.route('/products')
@login_required
def products():
    batch_id = request.args.get('batch_id')
    status = request.args.get('status')
    search = request.args.get('search')
    result_filter = request.args.get('result')
    station = request.args.get('station')
    date_filter = request.args.get('date')
    
    query = Product.query
    if batch_id:
        query = query.filter_by(batch_id=batch_id)
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(Product.serial_number.contains(search))
    if result_filter:
        query = query.filter_by(result=result_filter)
    if station:
        query = query.filter_by(current_station=station)
        
    products = query.order_by(Product.created_at.desc()).all()
    batches = Batch.query.all()
    stations = Station.query.all()
    return render_template('products.html', products=products, batches=batches, stations=stations)

@app.route('/products/<int:id>')
@login_required
def product_detail(id):
    product = Product.query.get_or_404(id)
    return render_template('product_detail.html', product=product)

@app.route('/batches', methods=['GET', 'POST'])
@login_required
def batches():
    if request.method == 'POST':
        batch_number = request.form.get('batch_code')
        product_type = request.form.get('product_type')
        status = request.form.get('status', 'Active')
        if batch_number:
            new_batch = Batch(batch_number=batch_number, product_type=product_type, status=status)
            db.session.add(new_batch)
            db.session.commit()
        return redirect(url_for('batches'))
    
    batches = Batch.query.order_by(Batch.created_at.desc()).all()
    return render_template('batches.html', batches=batches)

@app.route('/batches/<int:id>')
@login_required
def batch_dashboard(id):
    batch = Batch.query.get_or_404(id)
    total_products = Product.query.filter_by(batch_id=batch.id).count()
    passed = Product.query.filter_by(batch_id=batch.id, result='APPROVED').count()
    failed = Product.query.filter_by(batch_id=batch.id, result='REJECTED').count()
    
    pass_rate = round((passed / total_products * 100) if total_products > 0 else 0, 1)
    
    total_defects = Defect.query.filter_by(batch_id=batch.id).count()
    common_defect = db.session.query(Defect.reason, func.count(Defect.id)).filter_by(batch_id=batch.id).group_by(Defect.reason).order_by(func.count(Defect.id).desc()).first()
    common_defect_name = common_defect[0] if common_defect and common_defect[0] else "None"
    
    avg_test_time = "2.5 mins" # Simulated
    
    return render_template('batch_dashboard.html', batch=batch, 
        total_products=total_products, passed=passed, failed=failed, pass_rate=pass_rate,
        total_defects=total_defects, common_defect_name=common_defect_name, avg_test_time=avg_test_time)


@app.route('/reports')
@login_required
def reports():
    completed_products = Product.query.filter(Product.status == 'COMPLETED').all()
    batches = Batch.query.all()
    return render_template('reports.html', products=completed_products, batches=batches)

import os
from fpdf import FPDF

@app.route('/generate_report/<int:product_id>')
@login_required
def generate_report(product_id):
    product = Product.query.get_or_404(product_id)
    
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Digital Product Passport - {product.serial_number}", 0, 1, 'C')
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Product Information", 0, 1)
    pdf.set_font("Arial", '', 11)
    batch_num = product.batch.batch_number if product.batch else 'N/A'
    pdf.cell(0, 8, f"Serial Number: {product.serial_number}", 0, 1)
    pdf.cell(0, 8, f"Batch Number: {batch_num}", 0, 1)
    pdf.cell(0, 8, f"Status: {product.status}", 0, 1)
    pdf.cell(0, 8, f"Overall Result: {product.result}", 0, 1)
    pdf.cell(0, 8, f"Date: {product.created_at.strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
    
    # Station History
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Station History", 0, 1)
    pdf.set_font("Arial", '', 11)
    for event in sorted(product.events, key=lambda e: e.timestamp):
        pdf.cell(0, 8, f"{event.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {event.station.name} - {event.status}", 0, 1)
        
    # Test Results
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Test Results", 0, 1)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(60, 8, "Parameter", 1)
    pdf.cell(40, 8, "Value", 1)
    pdf.cell(30, 8, "Result", 1)
    pdf.cell(50, 8, "Timestamp", 1, 1)
    
    pdf.set_font("Arial", '', 11)
    for test in product.test_results:
        res = "PASS" if test.passed else "FAIL"
        pdf.cell(60, 8, test.parameter, 1)
        pdf.cell(40, 8, f"{test.value:.2f}", 1)
        pdf.cell(30, 8, res, 1)
        pdf.cell(50, 8, test.timestamp.strftime('%Y-%m-%d %H:%M:%S'), 1, 1)
        
    # Defects
    if product.defects:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Defects / Diagnosis", 0, 1)
        pdf.set_font("Arial", '', 11)
        for defect in product.defects:
            pdf.multi_cell(0, 8, f"[{defect.severity}] {defect.parameter}: {defect.reason}")
            
    # Signature
    pdf.ln(20)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "System Generated Signature: _______________________", 0, 1, 'R')
    
    filepath = os.path.join('instance', f'report_{product.serial_number}.pdf')
    pdf.output(filepath)
    
    from flask import send_file
    return send_file(filepath, as_attachment=True)

@app.route('/simulate', methods=['POST'])
@login_required
@role_required('Admin')
def simulate():
    batch_id = request.form.get('batch_id')
    if not batch_id:
        batch_id = None
    else:
        batch_id = int(batch_id)
        
    num_products = int(request.form.get('num_products', 10))
    
    batch = Batch.query.get(batch_id) if batch_id else None
    
    stations = Station.query.all()
    if not stations:
        return jsonify({"error": "No stations available"}), 400
        
    for i in range(num_products):
        sn = f"SIM-{int(time.time())}-{random.randint(1000,9999)}"
        p = Product(serial_number=sn, batch_id=batch_id, status='COMPLETED', result='APPROVED')
        db.session.add(p)
        db.session.commit()
        
        # 20% failure rate for demo
        fail_simulation = random.random() < 0.2
        
        for st in stations:
            # Add event
            ev = ProductionEvent(product_id=p.id, station_id=st.id, user_id=current_user.id, status='Completed')
            db.session.add(ev)
            
            # Add test result if Inspection or Functional Test
            if st.name in ['Inspection', 'Functional Test', 'Final QA']:
                if st.name == 'Functional Test':
                    val = random.uniform(11.0, 13.0)
                    passed = True
                    if fail_simulation:
                        val = random.uniform(8.0, 10.0)
                        passed = False
                        
                    tr = TestResult(product_id=p.id, parameter='Voltage', value=val, passed=passed)
                    db.session.add(tr)
                    
                    if not passed:
                        p.result = 'REJECTED'
                        d = Defect(product_id=p.id, batch_id=batch_id, station_id=st.id, parameter='Voltage', actual_value=str(val), expected_value='> 11.0', reason='Low Voltage detected', description='Simulation generated defect', severity='High')
                        db.session.add(d)
        
        db.session.commit()
        
    return redirect(url_for('reports'))


@app.route('/config', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def config():
    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('min_'):
                param = key.replace('min_', '')
                limit = TestLimit.query.filter_by(parameter=param).first()
                if limit:
                    limit.min_value = float(value) if value else None
            elif key.startswith('max_'):
                param = key.replace('max_', '')
                limit = TestLimit.query.filter_by(parameter=param).first()
                if limit:
                    limit.max_value = float(value) if value else None
            elif key.startswith('unit_'):
                param = key.replace('unit_', '')
                limit = TestLimit.query.filter_by(parameter=param).first()
                if limit:
                    limit.unit = value
        db.session.commit()
        return redirect(url_for('config'))
        
    limits = TestLimit.query.all()
    if not limits:
        defaults = [
            {'parameter': 'Voltage', 'min_value': 300, 'max_value': 400, 'unit': 'V'},
            {'parameter': 'Current', 'min_value': -150, 'max_value': 150, 'unit': 'A'},
            {'parameter': 'Temperature', 'min_value': 20, 'max_value': 45, 'unit': 'C'},
            {'parameter': 'Insulation Resistance', 'min_value': 2, 'max_value': 1000, 'unit': 'MOhm'},
            {'parameter': 'Cell Balance', 'min_value': 0, 'max_value': 50, 'unit': 'mV'}
        ]
        for d in defaults:
            db.session.add(TestLimit(**d))
        db.session.commit()
        limits = TestLimit.query.all()
        
    return render_template('config.html', limits=limits, title='Configuration')

@app.route('/testing')
@login_required
@role_required('Admin', 'Quality Engineer')
def testing():
    product_id = request.args.get('product_id')
    selected_product = None
    tests = []
    if product_id:
        selected_product = Product.query.get(product_id)
        tests = TestResult.query.filter_by(product_id=product_id).all()
        defects = {d.parameter: d for d in Defect.query.filter_by(product_id=product_id).all()}
        limits = {limit.parameter: limit for limit in TestLimit.query.all()}
        for test in tests:
            test.limit_str = (
                f"{limits[test.parameter].min_value} - {limits[test.parameter].max_value}"
                if test.parameter in limits else ""
            )
            test.reason = defects[test.parameter].reason if test.parameter in defects else "-"

    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template(
        'testing.html',
        products=products,
        selected_product=selected_product,
        tests=tests,
        title='Testing'
    )

@app.route('/defects')
@login_required
@role_required('Admin', 'Quality Engineer', 'Production Engineer')
def defects():
    defects_list = Defect.query.order_by(Defect.timestamp.desc()).all()
    return render_template('defects.html', defects=defects_list, title='Defects')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
