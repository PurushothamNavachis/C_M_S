import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-administration',
  templateUrl: './administration.page.html',
  styleUrls: ['./administration.page.scss'],
  standalone: false,
})
export class AdministrationPage implements OnInit, OnDestroy {
  // Current active role perspective for testing
  activePerspective: 'SUPER_ADMIN' | 'ADMIN' | 'RECEPTIONIST' | 'DOCTOR' = 'SUPER_ADMIN';

  // Clock properties
  currentTime = '';
  currentDate = '';
  private clockInterval: any;

  // User Management
  usersList: any[] = [];
  searchTerm = '';
  roleFilter = 'ALL';
  specializationFilter = '';

  get filteredUsers() {
    return this.usersList.filter(user => {
      const matchesSearch = !this.searchTerm || 
                            user.username.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
                            user.email.toLowerCase().includes(this.searchTerm.toLowerCase());
      
      const matchesRole = this.roleFilter === 'ALL' || user.role?.name === this.roleFilter;
      
      const matchesSpec = !this.specializationFilter ||
                          (user.role?.name === 'DOCTOR' && 
                           user.doctor?.specialization?.toLowerCase().includes(this.specializationFilter.toLowerCase()));
      
      return matchesSearch && matchesRole && matchesSpec;
    });
  }

  get activeSessionUser() {
    switch (this.activePerspective) {
      case 'SUPER_ADMIN':
        return { name: 'superadmin', role: 'Super Admin', colorClass: 'bg-purple-100 text-purple-700 border-purple-200' };
      case 'ADMIN':
        return { name: 'admin', role: 'Admin', colorClass: 'bg-blue-100 text-blue-700 border-blue-200' };
      case 'RECEPTIONIST':
        return { name: 'receptionist', role: 'Receptionist (RAC)', colorClass: 'bg-green-100 text-green-700 border-green-200' };
      case 'DOCTOR':
        return { name: 'doctor', role: 'Doctor', colorClass: 'bg-teal-100 text-teal-700 border-teal-200' };
    }
  }
  registration = {
    email: '',
    username: '',
    password: '',
    role_name: 'RECEPTIONIST',
    specialization: '',
    license_number: '',
    consultation_fee: null as number | null,
    experience_years: null as number | null
  };

  selectedUserForDetails: any = null;

  // Mock Patient / Appointment Data for Receptionist (RAC)
  patientsList: any[] = [];
  newPatient = { name: '', age: null, gender: 'Male', phone: '', email: '' };

  appointmentsList: any[] = [];
  newAppointment = { id: '', patientName: '', doctorName: '', time: '', status: 'Scheduled' };

  // Mock Consultations / Prescriptions Data for Doctor
  prescriptionsList: any[] = [];
  newPrescription = { patientName: '', diagnosis: '', medication: '', instructions: '' };

  errorMessage = '';
  loading = false;

  constructor(private api: ApiService, private router: Router) { }

  ngOnInit() {
    this.loadUsers();
    this.loadPatients();
    this.loadAppointments();
    this.startClock();
  }

  ngOnDestroy() {
    if (this.clockInterval) {
      clearInterval(this.clockInterval);
    }
  }

  startClock() {
    const updateTime = () => {
      const now = new Date();
      // Format time: HH:MM:SS
      this.currentTime = now.toLocaleTimeString([], { hour12: false });
      
      // Format date: DD Month YYYY (e.g. 08 July 2026)
      const day = String(now.getDate()).padStart(2, '0');
      const month = now.toLocaleString('en-US', { month: 'long' });
      const year = now.getFullYear();
      this.currentDate = `${day} ${month} ${year}`;
    };
    updateTime();
    this.clockInterval = setInterval(updateTime, 1000);
  }

  changePerspective(role: 'SUPER_ADMIN' | 'ADMIN' | 'RECEPTIONIST' | 'DOCTOR') {
    this.activePerspective = role;
    this.errorMessage = '';
    if (role === 'SUPER_ADMIN' || role === 'ADMIN') {
      this.loadUsers();
    }
  }

  loadUsers() {
    this.api.get('users').subscribe({
      next: (data) => {
        this.usersList = data;
      },
      error: (err) => {
        console.error('Failed to load users from backend', err);
      }
    });
  }

  loadPatients() {
    this.api.get('clinical/patients').subscribe({
      next: (data: any) => {
        this.patientsList = data;
      },
      error: (err) => {
        console.error('Failed to load patients', err);
      }
    });
  }

  loadAppointments() {
    this.api.get('clinical/appointments').subscribe({
      next: (data: any) => {
        this.appointmentsList = data;
      },
      error: (err) => {
        console.error('Failed to load appointments', err);
      }
    });
  }

  onStaffRegister() {
    this.errorMessage = '';
    
    if (this.registration.username.length < 3) {
      this.errorMessage = 'Username must be at least 3 characters long.';
      return;
    }
    if (this.registration.password.length < 6) {
      this.errorMessage = 'Password must be at least 6 characters long.';
      return;
    }

    this.loading = true;
    this.api.post('users', this.registration).subscribe({
      next: (response) => {
        this.loading = false;
        alert(`Successfully registered ${this.registration.role_name} user profile!`);
        this.registration = {
          email: '',
          username: '',
          password: '',
          role_name: 'RECEPTIONIST',
          specialization: '',
          license_number: '',
          consultation_fee: null,
          experience_years: null
        };
        this.loadUsers();
      },
      error: (err) => {
        this.loading = false;
        const detail = err.error?.detail;
        if (Array.isArray(detail)) {
          this.errorMessage = detail.map(e => `${e.loc[e.loc.length - 1]}: ${e.msg}`).join(', ');
        } else if (typeof detail === 'string') {
          this.errorMessage = detail;
        } else {
          this.errorMessage = 'Staff registration failed.';
        }
      }
    });
  }

  toggleUserActive(userId: string) {
    this.api.patch(`users/${userId}/toggle-active`, {}).subscribe({
      next: () => {
        this.loadUsers();
      },
      error: (err) => {
        console.error('Toggle active failed', err);
      }
    });
  }

  deleteUser(userId: string) {
    if (confirm('Are you sure you want to delete this user account?')) {
      this.api.delete(`users/${userId}`).subscribe({
        next: () => {
          this.loadUsers();
        },
        error: (err) => {
          console.error('Delete user failed', err);
        }
      });
    }
  }

  // Receptionist (RAC) Actions
  registerPatient() {
    if (!this.newPatient.name || !this.newPatient.email) {
      alert('Patient name and email are required.');
      return;
    }
    this.api.post('clinical/patients', this.newPatient).subscribe({
      next: () => {
        alert(`Patient ${this.newPatient.name} registered successfully!`);
        this.newPatient = { name: '', age: null, gender: 'Male', phone: '', email: '' };
        this.loadPatients();
      },
      error: (err) => {
        console.error('Register patient failed', err);
        alert('Failed to register patient: ' + (err.error?.detail || err.message));
      }
    });
  }

  scheduleAppointment() {
    if (!this.newAppointment.patientName || !this.newAppointment.doctorName || !this.newAppointment.time) {
      alert('All appointment fields are required.');
      return;
    }
    const payload = {
      patient_name: this.newAppointment.patientName,
      doctor_name: this.newAppointment.doctorName,
      time_slot: this.newAppointment.time
    };
    this.api.post('clinical/appointments', payload).subscribe({
      next: () => {
        alert(`Appointment scheduled successfully for ${this.newAppointment.patientName}!`);
        this.newAppointment = { id: '', patientName: '', doctorName: '', time: '', status: 'Scheduled' };
        this.loadAppointments();
      },
      error: (err) => {
        console.error('Schedule appointment failed', err);
        alert('Failed to schedule appointment: ' + (err.error?.detail || err.message));
      }
    });
  }

  updateAppointmentStatus(appointmentId: string, status: string) {
    this.api.patch(`clinical/appointments/${appointmentId}/status?status=${status}`, {}).subscribe({
      next: () => {
        this.loadAppointments();
      },
      error: (err) => {
        console.error('Update appointment status failed', err);
      }
    });
  }

  // Doctor Actions
  savePrescription() {
    if (!this.newPrescription.diagnosis || !this.newPrescription.medication) {
      alert('Diagnosis and medication are required.');
      return;
    }
    const activeApt = this.appointmentsList.find(
      a => a.patientName.toLowerCase() === this.newPrescription.patientName.toLowerCase() && a.status !== 'Completed'
    );
    if (!activeApt) {
      alert(`No active scheduled appointment found for patient ${this.newPrescription.patientName}. Please schedule one first.`);
      return;
    }

    const payload = {
      appointment_id: activeApt.id,
      symptoms: 'Patient reports symptoms of consultation.',
      diagnosis: this.newPrescription.diagnosis,
      doctor_notes: this.newPrescription.instructions,
      prescription_notes: this.newPrescription.medication
    };

    this.api.post('clinical/consultations', payload).subscribe({
      next: () => {
        alert(`Prescription saved for patient ${this.newPrescription.patientName}!`);
        this.prescriptionsList.push({ ...this.newPrescription });
        this.newPrescription = { patientName: '', diagnosis: '', medication: '', instructions: '' };
        this.loadAppointments();
      },
      error: (err) => {
        console.error('Save consultation failed', err);
        alert('Failed to save consultation: ' + (err.error?.detail || err.message));
      }
    });
  }

  viewUserDetails(user: any) {
    this.selectedUserForDetails = user;
  }

  closeUserDetails() {
    this.selectedUserForDetails = null;
  }

  get sessionUserStatus() {
    const sessionUser = this.activeSessionUser;
    if (!sessionUser || this.activePerspective === 'SUPER_ADMIN') {
      return null;
    }
    const dbUser = this.usersList.find(u => u.role?.name === this.activePerspective);
    return dbUser ? dbUser.is_active : false;
  }

  toggleSelfActive() {
    const sessionUser = this.activeSessionUser;
    if (!sessionUser || this.activePerspective === 'SUPER_ADMIN') {
      return;
    }
    const dbUser = this.usersList.find(u => u.role?.name === this.activePerspective);
    if (dbUser) {
      this.toggleUserActive(dbUser.id);
    }
  }
}
