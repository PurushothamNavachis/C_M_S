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

  loginData = {
    username_or_email: '',
    password: ''
  };

  signupData = {
    username: '',
    email: '',
    mobile_number: '',
    blood_group: '',
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
  }

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

  labTests = [
    {
      category: 'Hematology (Blood Tests)',
      tests: [
        { name: 'Complete Blood Count', description: 'Basic screening for anemia, infection, and overall health.', selected: false },
        { name: 'Erythrocyte Sedimentation Rate', description: 'Checks for inflammation in the body.', selected: false },
        { name: 'Hemoglobin', description: 'Measures the amount of hemoglobin in the blood; checks for anemia.', selected: false },
        { name: 'Blood Grouping & Rh Typing', description: 'Determines the patient\'s blood type (A, B, AB, O) and Rh factor.', selected: false }
      ]
    },
    {
      category: 'Diabetology (Sugar Profiling)',
      tests: [
        { name: 'Fasting Blood Sugar', description: 'Measures blood glucose after an overnight fast.', selected: false },
        { name: 'Post Prandial Blood Sugar', description: 'Measures blood glucose exactly 2 hours after eating.', selected: false },
        { name: 'Random Blood Sugar', description: 'Checks glucose levels at any given time of day.', selected: false },
        { name: 'Glycosylated Hemoglobin', description: 'Provides a 3-month average of blood sugar levels.', selected: false }
      ]
    },
    {
      category: 'Biochemistry & Organ Profiles',
      tests: [
        { name: 'Lipid Profile', description: 'Checks cholesterol levels (HDL, LDL, Triglycerides) for heart health.', selected: false },
        { name: 'Liver Function Test', description: 'Assesses liver health (Bilirubin, SGOT, SGPT).', selected: false },
        { name: 'Kidney Function Test', description: 'Assesses kidney health (Urea, Creatinine, Uric Acid).', selected: false },
        { name: 'Thyroid Profile', description: 'Checks thyroid gland function.', selected: false }
      ]
    },
    {
      category: 'Infectious Diseases (Fever Panels)',
      tests: [
        { name: 'Widal Test', description: 'Screening test for Typhoid fever.', selected: false },
        { name: 'Dengue NS1 Antigen', description: 'Early detection of Dengue virus.', selected: false },
        { name: 'Malaria Parasite Smear', description: 'Microscopic blood test to detect Malaria.', selected: false },
        { name: 'C-Reactive Protein', description: 'General marker for acute inflammation or infection.', selected: false }
      ]
    },
    {
      category: 'Clinical Pathology (Urine & Stool)',
      tests: [
        { name: 'Urine Routine & Microscopy', description: 'General screening for UTI, kidney issues, or diabetes.', selected: false },
        { name: 'Urine Culture', description: 'Identifies specific bacteria causing a Urinary Tract Infection.', selected: false },
        { name: 'Stool Routine', description: 'Checks for gastrointestinal infections or parasites.', selected: false }
      ]
    },
    {
      category: 'Vitamins & Deficiencies',
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

    alert(`Request Sent Successfully!\n\nYou requested the following test(s):\n- ${selectedTests.join('\n- ')}`);
    
    // Reset selections
    this.labTests.forEach(cat => {
      cat.tests.forEach(test => {
        test.selected = false;
      });
    });
    this.bookingSubMode = 'options';
  }

  onBookDoctor() {
    alert('Doctor Appointment Request Sent successfully!');
    this.bookingSubMode = 'options';
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
