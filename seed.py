from app import app
from models import db, User, Station, TestLimit

def seed_data():
    with app.app_context():
        db.create_all()
        
        if User.query.first():
            print("Database already seeded.")
            return

        # Users
        admin = User(username='admin', role='Admin')
        admin.set_password('admin123')
        
        prod_eng = User(username='prod_eng', role='Production Engineer')
        prod_eng.set_password('prod123')
        
        qual_eng = User(username='qual_eng', role='Quality Engineer')
        qual_eng.set_password('qual123')
        
        db.session.add_all([admin, prod_eng, qual_eng])
        
        # Stations
        stations = [
            Station(name='Registration', description='Product registration'),
            Station(name='Assembly', description='Main assembly line'),
            Station(name='Inspection', description='Visual inspection'),
            Station(name='Functional Test', description='Functional testing'),
            Station(name='Final QA', description='Final quality assurance')
        ]
        db.session.add_all(stations)
        
        # Test Limits
        limits = [
            TestLimit(parameter='Voltage', min_value=11.5, max_value=12.5),
            TestLimit(parameter='Current', min_value=0.5, max_value=2.0),
            TestLimit(parameter='Temperature', min_value=20.0, max_value=45.0)
        ]
        db.session.add_all(limits)
        
        db.session.commit()
        print("Database seeded successfully.")

if __name__ == '__main__':
    seed_data()
