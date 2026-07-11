# Walkthrough: Patient Portal Database Integration & Custom Scheduler

This document details the database integration and custom scheduler controls implemented in the Patient Portal to persist all patient actions (Doctor Consultations and Lab Test requests).

---

## DB Persistence Architecture

Every action a patient takes is linked to their authenticated patient identity and stored in the SQLite database (`cms_db.sqlite`):

### 1. Doctor Consultation Requests
*   **API Endpoint**: `POST /api/v1/clinical/patient-actions/consultation-request`
*   **Database Tables**:
    *   **`appointments`**: Stores the core appointment slot (Date, Time, Patient ID, Doctor ID). If the patient specifies a specialization/department (e.g., *Cardiologist*), the backend automatically looks up or registers a placeholder doctor for that specialization and assigns them. The status is set to `"Requested"`.
    *   **`consultations`**: Stores the symptoms list (as a comma-separated string) and doctor notes (e.g., patient preference policy).
*   **TypeScript Handler**: `submitDoctorConsultation()` computes the 24-hour time representation and posts the payload to the database.

### 2. Lab Test Requests
*   **API Endpoint**: `POST /api/v1/clinical/patient-actions/lab-request`
*   **Database Tables**:
    *   **`laboratory_tests`**: Automatically seeds or retrieves the custom tests catalog for selected options (e.g., *Complete Blood Count*).
    *   **`lab_reports`**: Stores patient request entries (Patient ID, Test ID) initialized with a status of `"Requested/Pending Sample Collection"`.
*   **TypeScript Handler**: `onSendRequest()` collects checked test names and posts them as a batch to the database.

---

## UI Scheduler Features

We refined the Date and Time fields to adhere to the requested specifications:

1.  **Date Picker**:
    *   Uses a standard HTML5 date input with `min` and `max` parameters to restrict selection to a **1-week window** (from today to next week this day).
    *   Clicking anywhere on the input box or the calendar icon triggers `showPicker()`, popping open the native calendar popup.
2.  **Time Selector Dropdowns**:
    *   **Hours Dropdown**: Explicitly limited to **10 AM - 6 PM**.
    *   **Minutes Dropdown**: Configured with options from **00 to 55** in steps of 5.
    *   Validation prevents booking appointments past 6:00 PM (e.g. 6:05 PM is blocked).
