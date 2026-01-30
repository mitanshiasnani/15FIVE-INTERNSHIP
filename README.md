# 15-Five — Employee Check-In & Performance Management System

A web-based performance management system inspired by 15Five, built using **Django**.  
The platform enables organizations to conduct **regular employee check-ins**, track progress, identify blockers, and maintain continuous feedback between employees and admins.

---

##  Features

###  Authentication & Roles
- Custom user model with **Admin** and **Employee** roles
- Secure login & logout
- Role-based access control
- Soft deletion of employees (deactivated users cannot log in)

### Admin Capabilities
- Admin dashboard with key metrics:
  - Total employees
  - Total check-ins
  - Assigned / Submitted / Pending Review / Reviewed counts
- Create **weekly or monthly check-ins**
- Manage **default questions**
- Add **custom questions** per check-in
- Assign check-ins automatically to all active employees
- Review employee submissions
- Add admin comments on reviews
- View employee-wise check-in history
- Remove (deactivate) employees

### Employee Capabilities
- Employee dashboard with:
  - Pending check-ins
  - Recently submitted check-ins
- Fill check-in forms
- Save answers as **Draft**
- Submit completed check-ins
- View past submissions and admin feedback
- Update profile and change password

### Notifications
- Slack DM when:
  - Check-ins are assigned
  - All employees submit a check-in
  - Admin reviews a submission
- Email notification when:
  - Employee account is created

---

## Tech Stack

- **Backend:** Django (Python)
- **Frontend:** Django Templates + Bootstrap 5
- **Database:** SQLite (development)
- **Authentication:** Custom Django User Model
- **Notifications:** Slack API, SMTP (Gmail)
- **Version Control:** Git & GitHub

---


