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
  activePerspective: string = 'SUPER_ADMIN';

  // Clock properties
  currentTime = '';
  currentDate = '';
  private clockInterval: any;

  // User Management
  usersList: any[] = [];
  searchTerm = '';
  roleFilter = 'ALL';
  specializationFilter = '';

  // Sidebar & Settings
  sidebarOpen = false;
  showSelfProfileModal = false;
  showRegisterPatientModal = false;
  showScheduleMatrixModal = false;
  selfProfileForm = { username: '', email: '', mobile_number: '', password: '' };

  // Directory editing
  showEditStaffModal = false;
  selectedUserForEdit: any = null;
  editStaffForm = {
    username: '',
    email: '',
    mobile_number: '',
    password: '',
    specialization: '',
    qualification: '',
    license_number: '',
    consultation_fee: 0,
    experience_years: 0
  };

  // Doctor Schedule Matrix Grid Properties
  minScheduleDate: string = new Date().toISOString().split('T')[0];
  maxScheduleDate: string = (() => {
    const d = new Date();
    d.setDate(d.getDate() + 7);
    return d.toISOString().split('T')[0];
  })();
  selectedDoctorForSchedule: any = null;
  selectedScheduleDate: string = new Date().toISOString().split('T')[0];
  scheduleHours = ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00'];
  scheduleMinutes = ['00', '15', '30', '45'];

  displayHour(hour24: string): string {
    const h = parseInt(hour24.split(':')[0], 10);
    if (h === 12) return '12 PM';
    if (h > 12) return `${h - 12} PM`;
    return `${h} AM`;
  }

  isBreakSlot(hour24: string, min: string): boolean {
    const timeFormatted = `${hour24.split(':')[0]}:${min}`;
    return timeFormatted === '13:30' || timeFormatted === '13:45' || 
           timeFormatted === '14:00' || timeFormatted === '14:15';
  }

  selectDoctorSchedule(doc: any) {
    this.selectedDoctorForSchedule = doc;
  }

  clearSelectedDoctorSchedule() {
    this.selectedDoctorForSchedule = null;
  }

  getAppointmentForSlot(hour24: string, min: string) {
    const hourNum = hour24.split(':')[0];
    const targetTime = `${hourNum}:${min}`;
    const docId = this.selectedDoctorForSchedule ? (this.selectedDoctorForSchedule.doctor?.id || this.selectedDoctorForSchedule.id) : null;
    const docName = this.selectedDoctorForSchedule ? (this.selectedDoctorForSchedule.username || '').toLowerCase() : null;

    return this.appointmentsList.find(a => {
      const matchDoc = !docName || 
                       (a.doctor_id && a.doctor_id === docId) ||
                       (a.doctorName && a.doctorName.toLowerCase().includes(docName));
      const matchDate = !this.selectedScheduleDate || a.date === this.selectedScheduleDate;
      const apptTime = a.time ? a.time.trim() : '';
      const matchTime = apptTime.includes(targetTime) || apptTime.startsWith(targetTime);
      return matchDoc && matchDate && matchTime;
    });
  }

  get filteredUsers() {
    return this.usersList.filter(user => {
      if (user.role?.name === 'PATIENT' || user.role?.name === 'RECEPTIONIST') {
        return false;
      }
      if (this.activePerspective === 'RECEPTIONIST') {
        if (user.role?.name !== 'DOCTOR' && user.role?.name !== 'LAB_AC') {
          return false;
        }
      }
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
      case 'LAB_AC':
        return { name: 'labassistant', role: 'Lab Assistant (Lab AC)', colorClass: 'bg-emerald-100 text-emerald-700 border-emerald-200' };
      default:
        return { name: 'superadmin', role: 'Super Admin', colorClass: 'bg-purple-100 text-purple-700 border-purple-200' };
    }
  }
  registration = {
    email: '',
    username: '',
    password: '',
    mobile_number: '',
    role_name: 'RECEPTIONIST',
    specialization: '',
    qualification: '',
    license_number: '',
    consultation_fee: null as number | null,
    experience_years: null as number | null
  };

  selectedUserForDetails: any = null;
  showPatientDetailsModal: boolean = false;

  // Mock Patient / Appointment Data for Receptionist (RAC)
  patientsList: any[] = [];
  newPatient = { name: '', age: null, gender: 'Male', phone: '', email: '' };

  appointmentsList: any[] = [];
  newAppointment = { id: '', patientName: '', doctorName: '', time: '', status: 'Scheduled' };
  requestsMode: 'appointments' | 'labTests' = 'appointments';
  labRequestsList: any[] = [];
  selectedDoctorForAppt: { [apptId: string]: string } = {};

  // Mock Consultations / Prescriptions Data for Doctor
  prescriptionsList: any[] = [];
  newPrescription = { patientName: '', diagnosis: '', medication: '', instructions: '' };

  // Mock Notifications and Doctor Requests for Receptionist view
  notificationsList = [
    { id: 'n1', message: 'Dr. Abijith changed status to Active', time: '10 mins ago', read: false },
    { id: 'n2', message: 'Lab report ready for patient John Doe', time: '25 mins ago', read: false },
    { id: 'n3', message: 'New patient registration request from website portal', time: '1 hour ago', read: true }
  ];

  doctorRequestsList = [
    { id: 'r1', doctorName: 'Dr. Abijith', patientName: 'John Doe', requestType: 'Urgent consultation booking request', status: 'Pending', time: '5 mins ago' },
    { id: 'r2', doctorName: 'Dr. Shalini', patientName: 'Mary Smith', requestType: 'Priority vitals collection and scheduling', status: 'Pending', time: '15 mins ago' },
    { id: 'r3', doctorName: 'Dr. Abijith', patientName: 'David Lee', requestType: 'Prepare billing summary for check-out', status: 'Completed', time: '40 mins ago' }
  ];

  get activeDoctors() {
    return this.usersList.filter(u => u.role?.name === 'DOCTOR');
  }

  get activeLabACs() {
    return this.usersList.filter(u => u.role?.name === 'LAB_AC');
  }

  get unreadNotificationsCount() {
    return this.notificationsList.filter(n => !n.read).length;
  }

  get pendingRequestsCount() {
    return this.doctorRequestsList.filter(r => r.status === 'Pending').length;
  }

  markNotificationRead(id: string) {
    const notif = this.notificationsList.find(n => n.id === id);
    if (notif) notif.read = true;
  }

  actionDoctorRequest(id: string, action: string) {
    const req = this.doctorRequestsList.find(r => r.id === id);
    if (req) {
      req.status = action;
      if (action === 'Completed') {
        alert(`Successfully processed request: "${req.requestType}" for ${req.patientName}`);
      } else if (action === 'Declined') {
        alert(`Declined request: "${req.requestType}" for ${req.patientName}`);
      }
    }
  }

  errorMessage = '';
  loading = false;

  constructor(private api: ApiService, private router: Router) { }

  ngOnInit() {
    this.loadUsers();
    this.loadPatients();
    this.loadAppointments();
    this.loadLabRequests();
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

  changePerspective(role: 'SUPER_ADMIN' | 'ADMIN' | 'RECEPTIONIST' | 'DOCTOR' | 'LAB_AC') {
    this.activePerspective = role;
    this.errorMessage = '';
    if (role === 'SUPER_ADMIN' || role === 'ADMIN' || role === 'RECEPTIONIST') {
      this.loadUsers();
    }
  }

  loadUsers() {
    this.api.get('users').subscribe({
      next: (data: any) => {
        this.usersList = data;
      },
      error: (err: any) => {
        console.error('Failed to load users from backend', err);
      }
    });
  }

  loadPatients() {
    this.api.get('clinical/patients').subscribe({
      next: (data: any) => {
        this.patientsList = data;
      },
      error: (err: any) => {
        console.error('Failed to load patients', err);
      }
    });
  }

  loadAppointments() {
    this.api.get('clinical/appointments').subscribe({
      next: (data: any) => {
        this.appointmentsList = data;
      },
      error: (err: any) => {
        console.error('Failed to load appointments', err);
      }
    });
  }

  loadLabRequests() {
    this.api.get('clinical/lab-requests').subscribe({
      next: (data: any) => {
        this.labRequestsList = data;
      },
      error: (err: any) => {
        console.error('Failed to load lab requests', err);
      }
    });
  }

  assignDoctor(appointmentId: string, doctorId: string) {
    if (!doctorId) {
      alert('Please select a doctor to assign.');
      return;
    }
    this.api.patch(`clinical/appointments/${appointmentId}/assign-doctor?doctor_id=${doctorId}`, {}).subscribe({
      next: () => {
        alert('Doctor assigned successfully!');
        this.loadAppointments();
      },
      error: (err: any) => {
        console.error(err);
        alert('Failed to assign doctor: ' + (err.error?.detail || err.message));
      }
    });
  }

  updateLabRequestStatus(reportId: string, status: string) {
    this.api.patch(`clinical/lab-requests/${reportId}/status?status=${status}`, {}).subscribe({
      next: () => {
        alert(`Lab request status updated to ${status}!`);
        this.loadLabRequests();
      },
      error: (err: any) => {
        console.error(err);
        alert('Failed to update status: ' + (err.error?.detail || err.message));
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
      next: (response: any) => {
        this.loading = false;
        alert(`Successfully registered ${this.registration.role_name} user profile!`);
        this.registration = {
          email: '',
          username: '',
          password: '',
          mobile_number: '',
          role_name: 'RECEPTIONIST',
          specialization: '',
          qualification: '',
          license_number: '',
          consultation_fee: null,
          experience_years: null
        };
        this.loadUsers();
      },
      error: (err: any) => {
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
      error: (err: any) => {
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
        error: (err: any) => {
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
        this.showRegisterPatientModal = false;
        this.loadPatients();
      },
      error: (err: any) => {
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
      error: (err: any) => {
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
      error: (err: any) => {
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
        alert(`Prescription submitted to receptionist for report finalization!`);
        this.prescriptionsList.push({ ...this.newPrescription });
        this.newPrescription = { patientName: '', diagnosis: '', medication: '', instructions: '' };
        this.changePerspective('RECEPTIONIST');
      },
      error: (err: any) => {
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

  openSelfProfile() {
    const dbUser = this.usersList.find(u => u.role?.name === this.activePerspective);
    if (dbUser) {
      this.selfProfileForm = {
        username: dbUser.username,
        email: dbUser.email,
        mobile_number: dbUser.mobile_number || '',
        password: ''
      };
      this.showSelfProfileModal = true;
    } else {
      alert('Could not find user profile in database.');
    }
  }

  saveSelfProfile() {
    const dbUser = this.usersList.find(u => u.role?.name === this.activePerspective);
    if (!dbUser) return;
    
    this.loading = true;
    const payload: any = {
      username: this.selfProfileForm.username,
      email: this.selfProfileForm.email,
      mobile_number: this.selfProfileForm.mobile_number
    };
    if (this.selfProfileForm.password && this.selfProfileForm.password.trim() !== '') {
      payload.password = this.selfProfileForm.password;
    }

    (this.api as any).put(`users/${dbUser.id}`, payload).subscribe({
      next: (res: any) => {
        alert('Profile updated successfully!');
        this.showSelfProfileModal = false;
        this.loadUsers();
      },
      error: (err: any) => {
        alert('Failed to update profile: ' + (err.error?.detail || err.message));
        this.loading = false;
      }
    });
  }

  openEditStaff(user: any) {
    this.selectedUserForEdit = user;
    this.editStaffForm = {
      username: user.username,
      email: user.email,
      mobile_number: user.mobile_number || '',
      password: '',
      specialization: user.doctor?.specialization || '',
      qualification: user.lab_ac?.qualification || '',
      license_number: (user.doctor?.license_number || user.lab_ac?.license_number) || '',
      consultation_fee: user.doctor?.consultation_fee || 0,
      experience_years: (user.doctor?.experience_years || user.lab_ac?.experience_years) || 0
    };
    this.showEditStaffModal = true;
  }

  saveEditStaff() {
    if (!this.selectedUserForEdit) return;
    
    this.loading = true;
    const payload: any = {
      username: this.editStaffForm.username,
      email: this.editStaffForm.email,
      mobile_number: this.editStaffForm.mobile_number,
      specialization: this.editStaffForm.specialization,
      qualification: this.editStaffForm.qualification,
      license_number: this.editStaffForm.license_number,
      consultation_fee: this.editStaffForm.consultation_fee,
      experience_years: this.editStaffForm.experience_years
    };
    if (this.editStaffForm.password && this.editStaffForm.password.trim() !== '') {
      payload.password = this.editStaffForm.password;
    }

    (this.api as any).put(`users/${this.selectedUserForEdit.id}`, payload).subscribe({
      next: (res: any) => {
        alert('Staff profile updated successfully!');
        this.showEditStaffModal = false;
        this.selectedUserForEdit = null;
        this.loadUsers();
      },
      error: (err: any) => {
        alert('Failed to update staff profile: ' + (err.error?.detail || err.message));
        this.loading = false;
      }
    });
  }

  showPatientDetailsPlaceholder() {
    this.loadPatients();
    this.showPatientDetailsModal = true;
  }
}
