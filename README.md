

# 15-Five – Employee Check-In & Performance Management System

A **Django-based performance management system** inspired by the 15Five model, designed to enable **regular employee check-ins**, structured feedback, and continuous performance tracking between employees and admins.

---

## 📌 Overview

Traditional annual performance reviews lack real-time visibility and timely feedback.
This project replaces that approach with **weekly/monthly check-ins**, allowing organizations to:

* Track employee progress continuously
* Identify blockers early
* Improve manager–employee communication
* Maintain structured performance data

---

## 🧑‍💼 User Roles

### **Admin**

* Add / deactivate employees
* Create weekly or monthly check-ins
* Manage default and custom questions
* Review employee submissions
* Track overall check-in completion status
* Receive Slack & email notifications

### **Employee**

* View assigned check-ins
* Submit responses or save drafts
* View submission history
* Update profile and password

---

## 🛠️ Tech Stack

* **Backend:** Django
* **Frontend:** HTML, CSS, Bootstrap
* **Database:** SQLite
* **Notifications:** Slack API, Email (SMTP)
* **Version Control:** Git & GitHub

---

## 📁 Project Structure

```
15FIVE-INTERNSHIP/
│
├── accounts/        # Authentication & user management
├── checkins/        # Check-in logic, questions, answers
├── core/            # Dashboards & admin views
├── config/          # Django project configuration
├── static/          # CSS, images
├── manage.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup Instructions (IMPORTANT)

Follow these steps to **run the project locally without confusion**.

### **1. Clone the Repository**

```bash
git clone https://github.com/mitanshiasnani/15FIVE-INTERNSHIP.git
cd 15FIVE-INTERNSHIP
```

---

### **2. Create Virtual Environment**

```bash
python -m venv env
```

Activate it:

* **Windows**

```bash
env\Scripts\activate
```

* **Mac / Linux**

```bash
source env/bin/activate
```

---

### **3. Install Dependencies**

```bash
pip install -r requirements.txt
```

---

### **4. Environment Configuration**

Create a `.env` file in the root directory and add:

```env
SLACK_BOT_TOKEN=your_slack_bot_token
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

> ⚠️ Slack and Email are optional for local testing but recommended.

---

### **5. Apply Migrations**

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### **6. Create Superuser (Admin)**

```bash
python manage.py createsuperuser
```

---

### **7. Run the Server**

```bash
python manage.py runserver
```

---

## 🌐 Access the Application

* **Login Page:**
  [http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/)

* **Admin Dashboard:**
  [http://127.0.0.1:8000/dashboard/admin-dashboard/](http://127.0.0.1:8000/dashboard/admin-dashboard/)

---

## 🔔 Notifications

* **Slack:** Admins receive notifications when check-ins are assigned or fully submitted
* **Email:** Employees receive email updates on reviews and account actions

---

## 🔐 Security & Access Control

* Role-based authentication (Admin / Employee)
* Deactivated employees cannot log in
* Secure password handling and validation
* Session-based authentication

---

## 🚀 Future Enhancements

* Manager hierarchy support
* Cloud deployment (AWS / Render)
* Export reports (PDF / CSV)

---

## 📌 Repository Link

🔗 [https://github.com/mitanshiasnani/15FIVE-INTERNSHIP](https://github.com/mitanshiasnani/15FIVE-INTERNSHIP)

---


