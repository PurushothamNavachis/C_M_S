import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-patient',
  templateUrl: './patient.page.html',
  styleUrls: ['./patient.page.scss'],
  standalone: false,
})
export class PatientPage implements OnInit {
  isLoggedIn = false;
  loading = false;
  authMode: 'login' | 'signup' = 'signup';
  errorMessage = '';
  successMessage = '';
  currentUser: any = null;
  activeTab: 'profile' | 'appointments' | 'prescriptions' | 'billing' = 'appointments';
  sidebarOpen = true;

  availableDates: { fullDate: string; dayName: string; dateNum: string; monthName: string }[] = [];
  minDate = '';
  maxDate = '';
  timeSlots = [
    { label: '09:00 AM', value: '09:00 AM', isPM: false },
    { label: '09:30 AM', value: '09:30 AM', isPM: false },
    { label: '10:00 AM', value: '10:00 AM', isPM: false },
    { label: '10:30 AM', value: '10:30 AM', isPM: false },
    { label: '11:00 AM', value: '11:00 AM', isPM: false },
    { label: '11:30 AM', value: '11:30 AM', isPM: false },
    { label: '12:00 PM', value: '12:00 PM', isPM: true },
    { label: '01:00 PM', value: '01:00 PM', isPM: true },
    { label: '02:00 PM', value: '02:00 PM', isPM: true },
    { label: '03:00 PM', value: '03:00 PM', isPM: true },
    { label: '04:00 PM', value: '04:00 PM', isPM: true },
    { label: '05:00 PM', value: '05:00 PM', isPM: true },
    { label: '06:00 PM', value: '06:00 PM', isPM: true }
  ];

  loginData = {
    username_or_email: '',
    password: ''
  };

  signupData = {
    username: '',
    email: '',
    mobile_number: '',
    blood_group: '',
    gender: '',
    password: '',
    password_confirm: ''
  };

  profileData = {
    username: '',
    email: '',
    mobile_number: '',
    blood_group: '',
    password: ''
  };

  constructor(private api: ApiService, private router: Router) { }

  ngOnInit() {
    this.checkAuth();
    
    const today = new Date();
    const oneWeek = new Date();
    oneWeek.setDate(today.getDate() + 7);
    
    const yyyy1 = today.getFullYear();
    const mm1 = String(today.getMonth() + 1).padStart(2, '0');
    const dd1 = String(today.getDate()).padStart(2, '0');
    this.minDate = `${yyyy1}-${mm1}-${dd1}`;

    const yyyy2 = oneWeek.getFullYear();
    const mm2 = String(oneWeek.getMonth() + 1).padStart(2, '0');
    const dd2 = String(oneWeek.getDate()).padStart(2, '0');
    this.maxDate = `${yyyy2}-${mm2}-${dd2}`;
    
    this.bookingForm.date = this.minDate;
  }

  patientConsultations: any[] = [];
  patientLabReports: any[] = [];
  reportsLoading: boolean = false;

  checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) {
      this.isLoggedIn = false;
      this.currentUser = null;
      return;
    }

    this.loading = true;
    this.api.get('users/me').subscribe({
      next: (user) => {
        this.loading = false;
        if (user.role?.name === 'PATIENT') {
          this.isLoggedIn = true;
          this.currentUser = user;
          this.errorMessage = '';

          // Pre-populate profile settings form
          this.profileData = {
            username: user.username,
            email: user.email,
            mobile_number: user.patient?.phone || user.mobile_number || '',
            blood_group: user.patient?.blood_group || '',
            password: ''
          };

          if (user.patient?.id) {
            this.loadPatientReports(user.patient.id);
          }
        } else {
          this.isLoggedIn = false;
          this.currentUser = null;
          this.errorMessage = 'Access Denied: This portal is reserved for patients.';
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
      },
      error: () => {
        this.loading = false;
        this.isLoggedIn = false;
        this.currentUser = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      }
    });
  }

  loadPatientReports(patientId: string) {
    this.reportsLoading = true;
    this.api.get(`clinical/patients/${patientId}/consultations`).subscribe({
      next: (data: any[]) => {
        this.patientConsultations = data.filter(c => c.uploadedFileUrl || c.status === 'Finalized');
      },
      error: (err) => console.error('Failed to fetch consultations for portal', err)
    });

    this.api.get(`clinical/patients/${patientId}/lab-requests`).subscribe({
      next: (data: any[]) => {
        this.patientLabReports = data.filter(r => r.uploadedFileUrl || r.status === 'FINALIZED');
        this.reportsLoading = false;
      },
      error: (err) => {
        console.error('Failed to fetch lab reports for portal', err);
        this.reportsLoading = false;
      }
    });
  }

  onLogin() {
    this.errorMessage = '';
    this.loading = true;
    this.api.post('auth/login', this.loginData).subscribe({
      next: (response) => {
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('refresh_token', response.refresh_token);
        this.checkAuth();
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err.error?.detail || 'Invalid username/email or password.';
      }
    });
  }

  onSignup() {
    this.errorMessage = '';
    if (this.signupData.password !== this.signupData.password_confirm) {
      this.errorMessage = 'Passwords do not match.';
      return;
    }

    this.loading = true;
    this.api.post('auth/register', this.signupData).subscribe({
      next: () => {
        // Auto-login after successful registration
        this.api.post('auth/login', {
          username_or_email: this.signupData.username,
          password: this.signupData.password
        }).subscribe({
          next: (response) => {
            localStorage.setItem('access_token', response.access_token);
            localStorage.setItem('refresh_token', response.refresh_token);
            this.checkAuth();
            alert('Registration Successful! You have been logged in.');
          },
          error: (err) => {
            this.loading = false;
            this.authMode = 'login';
            alert('Registration Successful! Please log in.');
          }
        });
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err.error?.detail || 'Registration failed. Please check details.';
      }
    });
  }

  onUpdateProfile() {
    this.errorMessage = '';
    this.successMessage = '';
    this.loading = true;

    const payload: any = {
      username: this.profileData.username,
      email: this.profileData.email,
      mobile_number: this.profileData.mobile_number,
      blood_group: this.profileData.blood_group
    };

    if (this.profileData.password && this.profileData.password.trim() !== '') {
      payload.password = this.profileData.password;
    }

    this.api.put(`users/${this.currentUser.id}`, payload).subscribe({
      next: (response) => {
        this.loading = false;
        this.successMessage = 'Profile updated successfully!';
        this.checkAuth();
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err.error?.detail || 'Failed to update profile settings.';
      }
    });
  }

  bookingSubMode: 'options' | 'lab_test' | 'doctor' = 'options';
  searchQuery = '';

  getSelectedTestsCount(): number {
    let count = 0;
    this.labTests.forEach(cat => {
      cat.tests.forEach(test => {
        if (test.selected) {
          count++;
        }
      });
    });
    return count;
  }

  getFilteredLabTests() {
    if (!this.searchQuery || this.searchQuery.trim() === '') {
      return this.labTests;
    }
    const query = this.searchQuery.toLowerCase().trim();
    return this.labTests.map(cat => {
      const matched = cat.tests.filter(t => 
        t.name.toLowerCase().includes(query) || 
        t.description.toLowerCase().includes(query)
      );
      return {
        category: cat.category,
        icon: cat.icon,
        tests: matched
      };
    }).filter(cat => cat.tests.length > 0);
  }

  labTests = [
    {
      category: 'Hematology (Blood Tests)',
      icon: '🩸',
      tests: [
        { name: 'Complete Blood Count', description: 'Basic screening for anemia, infection, and overall health.', selected: false },
        { name: 'Erythrocyte Sedimentation Rate', description: 'Checks for inflammation in the body.', selected: false },
        { name: 'Hemoglobin', description: 'Measures the amount of hemoglobin in the blood; checks for anemia.', selected: false },
        { name: 'Blood Grouping & Rh Typing', description: 'Determines the patient\'s blood type (A, B, AB, O) and Rh factor.', selected: false }
      ]
    },
    {
      category: 'Diabetology (Sugar Profiling)',
      icon: '🍬',
      tests: [
        { name: 'Fasting Blood Sugar', description: 'Measures blood glucose after an overnight fast.', selected: false },
        { name: 'Post Prandial Blood Sugar', description: 'Measures blood glucose exactly 2 hours after eating.', selected: false },
        { name: 'Random Blood Sugar', description: 'Checks glucose levels at any given time of day.', selected: false },
        { name: 'Glycosylated Hemoglobin', description: 'Provides a 3-month average of blood sugar levels.', selected: false }
      ]
    },
    {
      category: 'Biochemistry & Organ Profiles',
      icon: '🫀',
      tests: [
        { name: 'Lipid Profile', description: 'Checks cholesterol levels (HDL, LDL, Triglycerides) for heart health.', selected: false },
        { name: 'Liver Function Test', description: 'Assesses liver health (Bilirubin, SGOT, SGPT).', selected: false },
        { name: 'Kidney Function Test', description: 'Assesses kidney health (Urea, Creatinine, Uric Acid).', selected: false },
        { name: 'Thyroid Profile', description: 'Checks thyroid gland function.', selected: false }
      ]
    },
    {
      category: 'Infectious Diseases (Fever Panels)',
      icon: '🌡️',
      tests: [
        { name: 'Widal Test', description: 'Screening test for Typhoid fever.', selected: false },
        { name: 'Dengue NS1 Antigen', description: 'Early detection of Dengue virus.', selected: false },
        { name: 'Malaria Parasite Smear', description: 'Microscopic blood test to detect Malaria.', selected: false },
        { name: 'C-Reactive Protein', description: 'General marker for acute inflammation or infection.', selected: false }
      ]
    },
    {
      category: 'Clinical Pathology (Urine & Stool)',
      icon: '🧪',
      tests: [
        { name: 'Urine Routine & Microscopy', description: 'General screening for UTI, kidney issues, or diabetes.', selected: false },
        { name: 'Urine Culture', description: 'Identifies specific bacteria causing a Urinary Tract Infection.', selected: false },
        { name: 'Stool Routine', description: 'Checks for gastrointestinal infections or parasites.', selected: false }
      ]
    },
    {
      category: 'Vitamins & Deficiencies',
      icon: '💊',
      tests: [
        { name: 'Vitamin D3', description: 'Checks for bone health and immunity deficiencies (very common).', selected: false },
        { name: 'Vitamin B12', description: 'Checks for nerve health and specific types of anemia.', selected: false },
        { name: 'Calcium (Total)', description: 'Measures calcium levels in the blood.', selected: false }
      ]
    }
  ];

  onSendRequest() {
    const selectedTests: string[] = [];
    this.labTests.forEach(cat => {
      cat.tests.forEach(test => {
        if (test.selected) {
          selectedTests.push(test.name);
        }
      });
    });

    if (selectedTests.length === 0) {
      alert('Please select at least one test before sending request.');
      return;
    }

    this.api.post('clinical/patient-actions/lab-request', { tests: selectedTests }).subscribe({
      next: (res) => {
        alert(`Request Sent Successfully!\n\n${res.message}`);
        // Reset selections
        this.labTests.forEach(cat => {
          cat.tests.forEach(test => {
            test.selected = false;
          });
        });
        this.bookingSubMode = 'options';
      },
      error: (err) => {
        console.error(err);
        alert(err.error?.detail || 'Failed to submit lab tests request.');
      }
    });
  }

  showAllSymptoms = false;

  getSymptomSuggestions(): string[] {
    const val = this.bookingForm.customSymptomInput.trim().toLowerCase();
    if (!val) return [];
    const allSymptoms: string[] = [];
    for (const cat of this.symptomCategories) {
      allSymptoms.push(...cat.symptoms);
    }
    return allSymptoms.filter((s: string) => 
      s.toLowerCase().includes(val) && 
      !this.bookingForm.selectedSymptoms.includes(s)
    );
  }

  selectSuggestion(sym: string) {
    if (!this.bookingForm.selectedSymptoms.includes(sym)) {
      this.bookingForm.selectedSymptoms.push(sym);
    }
    this.bookingForm.customSymptomInput = '';
  }

  bookingForm = {
    department: '',
    customSymptomInput: '',
    selectedSymptoms: [] as string[],
    date: '',
    timeHour: '10 AM',
    timeMinute: '00',
    schedulingPreference: 'cancel'
  };

  hoursList = [
    '10 AM',
    '11 AM',
    '12 PM',
    '01 PM',
    '02 PM',
    '03 PM',
    '04 PM',
    '05 PM',
    '06 PM'
  ];

  minutesList = [
    '00', '15', '30', '45'
  ];

  departments = [
    'General Physician',
    'Family Physician',
    'Diabetologist',
    'Pediatrician',
    'Gynecologist / OB-GYN',
    'Cardiologist',
    'Dermatologist',
    'Orthopedic Surgeon',
    'ENT Specialist',
    'Gastroenterologist',
    'Pulmonologist',
    'Dentist',
    'Physiotherapist',
    'Psychiatrist'
  ];

  symptomCategories = [
    {
      name: 'General & Fever',
      symptoms: ['High Fever / Chills', 'Mild Fever / Viral Fever', 'Severe Body Ache (Myalgia)', 'Extreme Fatigue / Weakness', 'Prolonged Fever']
    },
    {
      name: 'Respiratory & ENT',
      symptoms: ['Cold and Congestion', 'Dry Cough', 'Wet / Productive Cough', 'Sore Throat / Difficulty Swallowing', 'Shortness of Breath / Wheezing', 'Ear Ache / Discharge']
    },
    {
      name: 'Gastrointestinal',
      symptoms: ['Stomach Ache / Abdominal Pain', 'Diarrhea / Loose Motions', 'Acidity / Heartburn / GERD', 'Nausea and Vomiting', 'Constipation', 'Indigestion / Bloating']
    },
    {
      name: 'Orthopedic & Musculoskeletal',
      symptoms: ['Lower Back Pain', 'Joint Pain / Knee Pain', 'Muscle Sprain / Strain', 'Neck Pain', 'Bone/Joint Injury or Trauma']
    },
    {
      name: 'Dermatological',
      symptoms: ['Skin Rash / Redness', 'Severe Itching', 'Fungal Infection', 'Acne / Pimples', 'Sudden Hair Fall']
    },
    {
      name: 'Chronic & General',
      symptoms: ['Headache / Migraine', 'Dizziness / Vertigo', 'Unexplained Weight Loss', 'Routine Follow-up', 'General Health Checkup']
    }
  ];

  toggleSymptom(symptom: string) {
    const idx = this.bookingForm.selectedSymptoms.indexOf(symptom);
    if (idx > -1) {
      this.bookingForm.selectedSymptoms.splice(idx, 1);
    } else {
      this.bookingForm.selectedSymptoms.push(symptom);
    }
  }

  addCustomSymptom() {
    const val = this.bookingForm.customSymptomInput.trim();
    if (val && !this.bookingForm.selectedSymptoms.includes(val)) {
      this.bookingForm.selectedSymptoms.push(val);
      this.bookingForm.customSymptomInput = '';
    }
  }

  removeSymptom(symptom: string) {
    const idx = this.bookingForm.selectedSymptoms.indexOf(symptom);
    if (idx > -1) {
      this.bookingForm.selectedSymptoms.splice(idx, 1);
    }
  }

  submitDoctorConsultation() {
    if (!this.bookingForm.date) {
      alert('Please select a date.');
      return;
    }

    // Convert hour/minute to 24h format
    let hourNum = parseInt(this.bookingForm.timeHour);
    const isPM = this.bookingForm.timeHour.includes('PM');
    if (isPM && hourNum !== 12) {
      hourNum += 12;
    } else if (!isPM && hourNum === 12) {
      hourNum = 0;
    }
    const hourStr = String(hourNum).padStart(2, '0');
    const minuteStr = this.bookingForm.timeMinute;
    const timeStr = `${hourStr}:${minuteStr}`;

    // 1. Date Validation (within 1 week)
    const selectedDate = new Date(this.bookingForm.date);
    selectedDate.setHours(0,0,0,0);
    const today = new Date();
    today.setHours(0,0,0,0);
    const oneWeekLater = new Date();
    oneWeekLater.setDate(today.getDate() + 7);
    oneWeekLater.setHours(23,59,59,999);
    
    if (selectedDate < today || selectedDate > oneWeekLater) {
      alert('Selected date must be between today and 1 week from now.');
      return;
    }

    // 2. Time Validation (10am - 6pm)
    const totalMinutes = hourNum * 60 + parseInt(minuteStr);
    const minMinutes = 10 * 60; // 10:00 AM
    const maxMinutes = 18 * 60; // 06:00 PM
    
    if (totalMinutes < minMinutes || totalMinutes > maxMinutes) {
      alert('Preferred time must be between 10:00 AM and 06:00 PM.');
      return;
    }

    if (hourNum === 18 && parseInt(minuteStr) > 0) {
      alert('Appointments cannot be scheduled past 06:00 PM.');
      return;
    }
    
    const payload = {
      department: this.bookingForm.department,
      symptoms: this.bookingForm.selectedSymptoms,
      date: this.bookingForm.date,
      time: timeStr,
      preference: this.bookingForm.schedulingPreference
    };

    this.api.post('clinical/patient-actions/consultation-request', payload).subscribe({
      next: (res) => {
        const summary = `
Consultation Request Details:
-----------------------------
Department: ${this.bookingForm.department || 'General Practice (None Selected)'}
Symptoms: ${this.bookingForm.selectedSymptoms.join(', ') || 'None Selected'}
Requested Slot: ${this.bookingForm.date} at ${this.bookingForm.timeHour}:${this.bookingForm.timeMinute}
Preference: ${this.bookingForm.schedulingPreference === 'cancel' ? 'Cancel if slot unavailable' : 'Book anyway / reschedule'}
        `;
        alert(`Consultation Request Submitted successfully and saved in database!\n\n${summary}`);
        
        // Reset Form
        this.bookingForm = {
          department: '',
          customSymptomInput: '',
          selectedSymptoms: [],
          date: this.minDate,
          timeHour: '10 AM',
          timeMinute: '00',
          schedulingPreference: 'cancel'
        };
        this.bookingSubMode = 'options';
      },
      error: (err) => {
        console.error(err);
        alert(err.error?.detail || 'Failed to submit consultation request.');
      }
    });
  }

  onLogout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    this.isLoggedIn = false;
    this.currentUser = null;
    this.errorMessage = '';
    this.successMessage = '';
  }
}
