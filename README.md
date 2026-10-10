# EV Manufacturing Traceability Simulator

This is a polished, locally runnable Digital Product Passport (DPP) and Manufacturing Traceability Simulator for EV modules. Built with Flask and SQLite, it tracks product lifecycles, test results, and defects across multiple stations on an assembly line.

## Features
- **Dashboard & KPIs**: Real-time insights into production performance, pass/fail rates, OEE, and active stations.
- **Digital Product Passport**: Detailed product view showing lifecycle timeline, test history, and rule-based failure diagnosis.
- **Reporting & PDF Export**: Generate a clean, structured PDF report for any completed product.
- **Demo Simulation Engine**: Automatically simulate a manufacturing run (10-20 products) with realistic pass rates and failure modes.
- **Traceability**: End-to-end tracking from Registration to Final QA.
- **Role-Based Access**: Secure login and role-based permissions (Admin, Production Engineer, Quality Engineer).

## Limitations
- **Local Environment Only**: Uses SQLite for data storage and is not configured for distributed or cloud-scale production without migrating to a scalable relational database (e.g., PostgreSQL).
- **Hardcoded Rules**: Some failure rules and demo parameters are currently hardcoded for the simulation.
- **No hardware integration**: Currently does not ingest real PLC/SCADA or IoT data, acting only as a simulator and manual entry system.

## Setup Steps
1. Make sure Python 3.9+ is installed on your machine.
2. Install the required dependencies:
   ```bash
   pip install flask flask-sqlalchemy flask-login werkzeug fpdf2
   ```
3. Initialize the database and seed it with demo data:
   ```bash
   python seed.py
   ```
4. Run the Flask application:
   ```bash
   flask run
   # or
   python -m flask run
   ```
5. Open your browser and navigate to `http://127.0.0.1:5000`.

## Login Credentials
| Username   | Password   | Role                  |
|------------|------------|-----------------------|
| `admin`    | `admin123` | Admin                 |
| `prod_eng` | `prod123`  | Production Engineer   |
| `qual_eng` | `qual123`  | Quality Engineer      |

## Demo Scenario
1. Log in as `admin`.
2. Go to **Batches** and create a new batch.
3. Navigate to **Reports**, go to the **Demo Simulation Mode** section.
4. Select the batch you just created, enter the number of products (10-20), and click **Start Simulation**.
5. Once complete, navigate to **Dashboard** to see the updated KPIs.
6. Go to **Products** and click **View** on a REJECTED product to explore the **Digital Product Passport** and the Failure Diagnosis.
7. Go to **Reports**, select a completed product (Pass or Fail), and click **Generate Report** to download its PDF summary.
