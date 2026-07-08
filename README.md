# GarageNET 🚗🔧

**GarageNET** is a peer-to-peer (P2P) collaborative workshop management network designed for independent auto garages. It streamlines inventory tracking, coordinates repair job cards, logs step-by-step activities, and enables garages to search and source spare parts from neighboring workshops in real time.

---

## 🌟 Key Features

### 1. Collaborative B2B Part Search (Haversine Formula) 📍
* **Geographical Sourcing**: If a garage is out of stock for a critical part, they can query the GarageNET network.
* **Proximity Sorting**: Calculates the absolute distance between workshops in real-time utilizing the **Haversine formula** optimized directly within Django ORM SQL query annotations.
* **Configurable Radius**: Filter spare parts from peer garages within a custom search radius (e.g., 50 km).

### 2. Job Card & Repair Workflow Management 📋
* **Lifecycle Tracking**: Monitor vehicles flowing through stages: `Received` ➡️ `In-Progress` ➡️ `Waiting-for-Parts` ➡️ `Ready`.
* **Line-Item Snapshots**: Add components from local inventory to job cards. Subtractions are locked transactionally (`select_for_update`) to prevent overselling.
* **Stock Replenishment**: Deleting a part line-item or deleting/canceling a job card automatically restores stock levels in the ledger.

### 3. Append-Only Activity Log (Audit Trail) 🛡️
* Every job card maintains a granular event log (`JobCardActivity`).
* Automatically records: job card creation, parts added/removed, labor charges added/removed, status updates, and invoice generation.

### 4. Interactive & Visual Dashboard 📊
* High-level metrics for active job cards, low-stock items, and total inventory items.
* **Dynamic SVG Donut Chart**: Renders status distribution (`In-Progress`, `Ready`, `Others`) using clean SVG calculations without external heavy JavaScript libraries.

### 5. Detailed Invoicing & Additional Charges 🧾
* Manage additional non-part charges (e.g. labor, diagnostics, consumable fees).
* Generates clean, printer-friendly billing layouts (`job_card_bill.html`).

---

## 🛠️ Tech Stack

* **Backend**: Django 5.0 (Python 3.10+)
* **Database**: SQLite (local dev), PostgreSQL (production-ready)
* **Frontend**: HTML5, Vanilla CSS (Modern CSS layout & variables, responsive design, SVG dashboard charts)
* **Environment Management**: Python Dotenv

---

## 📂 Project Structure

```text
GarageNET_NEW/
├── garagenet/               # Django project configurations
│   ├── settings.py          # Core settings
│   └── urls.py              # Global URL routing
├── workshop/                # Workshop application
│   ├── models.py            # Workshop, Inventory, JobCard, LineItem schemas
│   ├── views.py             # Dashboard, inventory ledger, P2P search, invoicing logic
│   ├── urls.py              # Application URL routing
│   ├── forms.py             # Form definitions for registration, profiles, job cards, charges
│   ├── utils.py             # Distance helpers (Haversine)
│   └── tests.py             # Unit & integration test suites
├── templates/               # Project-wide HTML templates
│   ├── workshop/            # Dashboard, inventory, search, billing, job card detail pages
│   └── registration/        # Signup and login pages
├── seed_db.py               # Database seeder script
├── manage.py                # Django CLI entrypoint
└── requirements.txt         # Project dependencies
```

---

## 🚀 Installation & Setup

Follow these steps to run GarageNET locally:

### 1. Clone & Navigate to the Repository
```bash
git clone <repository-url>
cd GarageNET_NEW
```

### 2. Set Up Virtual Environment
Create and activate a Python virtual environment:
```powershell
# Windows PowerShell
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file in the root directory (based on `.env.example`):
```env
DEBUG=True
SECRET_KEY=your-django-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
# Configure DATABASE_URL if using PostgreSQL, otherwise defaults to local SQLite
```

### 5. Database Migrations
Run the migrations to set up database schemas:
```bash
python manage.py migrate
```

### 6. Seed Demo Data
Populate the database with pre-configured workshops (Pune, Mumbai, Nashik, and Demo Shop), inventory, and job cards:
```bash
python seed_db.py
```

### 7. Start Development Server
```bash
python manage.py runserver
```
Visit the application at `http://127.0.0.1:8000/`.

---

## 🔑 Demo Login Credentials

The `seed_db.py` script registers a demo shop you can log in with:
* **Username**: `demo_user`
* **Password**: `password123`

---

## 🧪 Running Tests

A comprehensive suite of unit and integration tests is included to verify core operations (e.g., transactional stock deductions, Haversine search, and billing details).

Run the tests using the virtual environment interpreter:
```bash
python manage.py test
```
