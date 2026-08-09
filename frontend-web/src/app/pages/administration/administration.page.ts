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
  selectedRequestsDate: string = new Date().toISOString().split('T')[0];
  activeDoctorViewSection: string = 'main';

  isDoctorSection(sec: string): boolean {
    if (sec === 'allScheduleMatrix') {
      return this.activeDoctorViewSection === 'allScheduleMatrix' || this.activeDoctorViewSection === 'matrixTable' || this.activeDoctorViewSection === 'matrix';
    }
    return !['allScheduleMatrix', 'matrixTable', 'matrix'].includes(this.activeDoctorViewSection);
  }
  activeReceptionistViewSection: 'dashboard' | 'registerPatient' = 'dashboard';
  scheduleHours = ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00'];
  selectedHourIndex: number = 0;

  get currentSelectedHour(): string {
    return this.scheduleHours[this.selectedHourIndex] || '10:00';
  }

  navigateHour(offset: number) {
    const newIndex = this.selectedHourIndex + offset;
    if (newIndex >= 0 && newIndex < this.scheduleHours.length) {
      this.selectedHourIndex = newIndex;
    }
  }

  navigateScheduleDate(offsetDays: number) {
    const baseDateStr = this.selectedScheduleDate || new Date().toISOString().split('T')[0];
    const parts = baseDateStr.split('-');
    const current = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
    current.setDate(current.getDate() + offsetDays);
    this.selectedScheduleDate = `${current.getFullYear()}-${String(current.getMonth() + 1).padStart(2, '0')}-${String(current.getDate()).padStart(2, '0')}`;
  }

  navigateRequestsDate(offsetDays: number) {
    const baseDateStr = this.selectedRequestsDate || new Date().toISOString().split('T')[0];
    const parts = baseDateStr.split('-');
    const current = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
    current.setDate(current.getDate() + offsetDays);
    this.selectedRequestsDate = `${current.getFullYear()}-${String(current.getMonth() + 1).padStart(2, '0')}-${String(current.getDate()).padStart(2, '0')}`;
  }
  scheduleMinutes = ['00', '15', '30', '45'];

  displayHour(hour24: string): string {
    const h = parseInt(hour24.split(':')[0], 10);
    if (h === 12) return '12 PM';
    if (h > 12) return `${h - 12} PM`;
    return `${h} AM`;
  }

  normalizeTimeTo24Hour(timeStr: string): string {
    if (!timeStr) return '';
    let clean = timeStr.trim().toUpperCase();
    const isPM = clean.includes('PM');
    const isAM = clean.includes('AM');
    clean = clean.replace('AM', '').replace('PM', '').trim();
    const parts = clean.split(':');
    if (parts.length < 2) return '';
    let hours = parseInt(parts[0], 10);
    const minutes = parts[1].substring(0, 2);
    if (isPM && hours < 12) hours += 12;
    if (isAM && hours === 12) hours = 0;
    const hStr = hours < 10 ? `0${hours}` : `${hours}`;
    return `${hStr}:${minutes}`;
  }

  isBreakSlot(hour24: string, min: string): boolean {
    const timeFormatted = `${hour24.split(':')[0]}:${min}`;
    return timeFormatted === '13:30' || timeFormatted === '13:45';
  }

  selectDoctorSchedule(doc: any) {
    this.selectedDoctorForSchedule = doc;
  }

  clearSelectedDoctorSchedule() {
    this.selectedDoctorForSchedule = null;
  }

  getAppointmentForSlot(hour24: string, min: string) {
    const hNum = parseInt(hour24.split(':')[0], 10);
    const hStr = hNum < 10 ? `0${hNum}` : `${hNum}`;
    const target24 = `${hStr}:${min}`;

    let docId = this.selectedDoctorForSchedule ? (this.selectedDoctorForSchedule.doctor?.id || this.selectedDoctorForSchedule.id) : null;
    let docName = this.selectedDoctorForSchedule ? (this.selectedDoctorForSchedule.username || '').toLowerCase() : null;

    if (!docName && this.activePerspective === 'DOCTOR' && (this.currentUserData || this.currentUserName)) {
      docName = (this.currentUserData?.username || this.currentUserName || '').toLowerCase();
      docId = this.currentUserData?.id;
    }

    return this.appointmentsList.find(a => {
      const matchDoc = !docName || 
                       (a.doctor_id && a.doctor_id === docId) ||
                       (a.doctorName && (a.doctorName.toLowerCase().includes(docName) || docName.includes(a.doctorName.toLowerCase())));
      const matchDate = !this.selectedScheduleDate || a.date === this.selectedScheduleDate;
      const appt24 = this.normalizeTimeTo24Hour(a.time || '');
      const matchTime = appt24 === target24 || (a.time && (a.time.includes(target24) || a.time.includes(`${hNum}:${min}`)));
      return matchDoc && matchDate && matchTime;
    });
  }

  get filteredUsers() {
    return this.usersList.filter(user => {
      if (user.role?.name === 'PATIENT') {
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

  get availableRoles(): string[] {
    const rolesSet = new Set<string>(['SUPER_ADMIN', 'ADMIN', 'RECEPTIONIST', 'DOCTOR', 'LAB_AC']);
    if (this.usersList) {
      this.usersList.forEach((u: any) => {
        if (u.role?.name) {
          rolesSet.add(u.role.name.toUpperCase());
        }
      });
    }
    return Array.from(rolesSet);
  }

  defaultSpecializations: string[] = [
    'General Practice / General Physician',
    'Cardiologist (Cardiology)',
    'Pediatrician (Pediatrics)',
    'Orthopedic Surgeon (Orthopedics)',
    'Dermatologist (Dermatology)',
    'Gastroenterologist (Gastroenterology)',
    'Diabetologist / Endocrinologist',
    'Pulmonologist (Pulmonology)',
    'Dentist (Dental Care)',
    'Physiotherapist (Physiotherapy)',
    'Neurologist (Neurology)',
    'Gynecologist & Obstetrician',
    'ENT Specialist (Otolaryngology)',
    'Ophthalmologist (Eye Care)',
    'Psychiatrist (Mental Health)',
    'Oncologist (Cancer Care)',
    'Nephrologist (Kidney Care)',
    'Urologist (Urology)',
    'Radiologist (Radiology)',
    'General Surgeon'
  ];

  get availableSpecializations(): string[] {
    const specSet = new Set<string>(this.defaultSpecializations);
    if (this.usersList) {
      this.usersList.forEach((u: any) => {
        const spec = u.doctor?.specialization || u.specialization;
        if (spec && spec.trim()) {
          specSet.add(spec.trim());
        }
      });
    }
    return Array.from(specSet);
  }

  get activeSessionUser() {
    const displayName = this.currentUserData?.username || this.currentUserName || '';
    switch (this.activePerspective) {
      case 'SUPER_ADMIN':
        return { name: displayName || 'superadmin', role: 'Super Admin', colorClass: 'bg-purple-100 text-purple-700 border-purple-200' };
      case 'ADMIN':
        return { name: displayName || 'admin', role: 'Admin', colorClass: 'bg-blue-100 text-blue-700 border-blue-200' };
      case 'RECEPTIONIST':
        return { name: displayName || 'receptionist', role: 'Receptionist (RAC)', colorClass: 'bg-green-100 text-green-700 border-green-200' };
      case 'DOCTOR':
        return { name: displayName || 'doctor', role: 'Doctor', colorClass: 'bg-teal-100 text-teal-700 border-teal-200' };
      case 'LAB_AC':
        return { name: displayName || 'labassistant', role: 'Lab Assistant (Lab AC)', colorClass: 'bg-emerald-100 text-emerald-700 border-emerald-200' };
      default:
        return { name: displayName || 'superadmin', role: 'Super Admin', colorClass: 'bg-purple-100 text-purple-700 border-purple-200' };
    }
  }
  registration = {
    email: '',
    username: '',
    password: '',
    mobile_number: '',
    role_name: 'RECEPTIONIST',
    custom_role_name: '',
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
  newPatient = { name: '', age: null as number | null, gender: 'Male', phone: '', email: '', blood_group: '', address: '', symptoms: '' };
  selectedTimeForAppt: { [key: string]: string } = {};
  selectedHourForAppt: { [key: string]: string } = {};
  selectedMinuteForAppt: { [key: string]: string } = {};
  selectedDateForAppt: { [key: string]: string } = {};

  hourOptions: string[] = ['10 AM', '11 AM', '12 PM', '01 PM', '02 PM', '03 PM', '04 PM', '05 PM'];
  minuteOptions: string[] = [':00', ':15', ':30', ':45'];

  getCombinedTimeSlot(aptId: string): string {
    const hr = this.selectedHourForAppt[aptId];
    const min = this.selectedMinuteForAppt[aptId] || ':00';
    if (!hr) return '';
    const parts = hr.split(' ');
    return `${parts[0]}${min} ${parts[1] || ''}`.trim();
  }

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

  showSymptomDropdown: boolean = false;

  get allSymptomsList(): string[] {
    const list: string[] = [];
    this.symptomCategories.forEach(cat => {
      cat.symptoms.forEach(sym => {
        if (!list.includes(sym)) list.push(sym);
      });
    });
    return list;
  }

  get filteredSymptomSuggestions(): string[] {
    if (!this.newPatient.symptoms || !this.newPatient.symptoms.trim()) {
      return this.allSymptomsList;
    }
    const query = this.newPatient.symptoms.toLowerCase().trim();
    return this.allSymptomsList.filter(sym => sym.toLowerCase().includes(query));
  }

  selectSuggestedSymptom(symptom: string) {
    this.newPatient.symptoms = symptom;
    this.showSymptomDropdown = false;
  }

  get todaysDate(): string {
    return new Date().toISOString().split('T')[0];
  }

  normalizeDateString(dateStr: string): string {
    if (!dateStr) return '';
    const clean = dateStr.trim();
    if (clean.includes('|')) {
      return this.normalizeDateString(clean.split('|')[0]);
    }
    const parts = clean.split('-');
    if (parts.length === 3) {
      if (parts[0].length === 4) {
        return `${parts[0]}-${parts[1].padStart(2, '0')}-${parts[2].padStart(2, '0')}`;
      } else if (parts[2].length === 4) {
        return `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
      }
    }
    return clean;
  }

  get todaysDateNormalized(): string {
    return this.normalizeDateString(this.todaysDate);
  }

  get todaysAppointments(): any[] {
    const targetDate = this.normalizeDateString(this.selectedScheduleDate || this.todaysDate);
    let docId = this.currentUserData ? this.currentUserData.id : null;
    let docName = (this.currentUserData?.username || this.currentUserName || '').toLowerCase();

    return this.appointmentsList.filter(a => {
      if (this.activePerspective === 'DOCTOR' && docName) {
        const matchDoc = (a.doctor_id && a.doctor_id === docId) ||
                         (a.doctorName && (a.doctorName.toLowerCase().includes(docName) || docName.includes(a.doctorName.toLowerCase())));
        if (!matchDoc) return false;
      }
      const apptDate = this.normalizeDateString(a.date);
      return apptDate === targetDate;
    });
  }

  get canNavigateNextDay(): boolean {
    if (!this.selectedScheduleDate) return false;
    const current = this.normalizeDateString(this.selectedScheduleDate);
    const today = this.normalizeDateString(this.todaysDate);
    return current < today;
  }

  get canNavigateNextRequestsDay(): boolean {
    if (!this.selectedRequestsDate) return false;
    const current = this.normalizeDateString(this.selectedRequestsDate);
    const today = this.normalizeDateString(this.todaysDate);
    return current < today;
  }

  get todaysReceptionistRequests(): any[] {
    const targetDate = this.normalizeDateString(this.selectedRequestsDate || this.todaysDate);
    return this.appointmentsList.filter(a => {
      if (a.status === 'Cancelled') return false;
      const rDate = this.normalizeDateString(a.requestedDate || a.date);
      return rDate === targetDate;
    });
  }

  get todaysRemainingBookingsCount(): number {
    return this.todaysAppointments.filter(a => a.status !== 'Completed' && a.status !== 'Doctor Completed' && a.status !== 'Cancelled').length;
  }

  get overallDoctorAppointments(): any[] {
    let docId = this.currentUserData ? this.currentUserData.id : null;
    let docName = (this.currentUserData?.username || this.currentUserName || '').toLowerCase();
    
    return this.appointmentsList.filter(a => {
      if (this.activePerspective === 'DOCTOR' && docName) {
        const matchDoc = (a.doctor_id && a.doctor_id === docId) ||
                         (a.doctorName && (a.doctorName.toLowerCase().includes(docName) || docName.includes(a.doctorName.toLowerCase())));
        if (!matchDoc) return false;
      }
      return true;
    });
  }

  get totalOverallBookingsCount(): number {
    return this.overallDoctorAppointments.length;
  }

  get totalOverallRemainingBookingsCount(): number {
    return this.overallDoctorAppointments.filter(a => a.status !== 'Completed' && a.status !== 'Doctor Completed' && a.status !== 'Cancelled').length;
  }

  doctorPatientFilter: 'treated' | 'all' = 'treated';
  doctorPatientSearch: string = '';

  get treatedPatientsList(): any[] {
    let docId = this.currentUserData ? this.currentUserData.id : null;
    let docName = (this.currentUserData?.username || this.currentUserName || '').toLowerCase();

    const treatedAppts = this.appointmentsList.filter(a => {
      const matchDoc = (a.doctor_id && a.doctor_id === docId) ||
                       (a.doctorName && (a.doctorName.toLowerCase().includes(docName) || docName.includes(a.doctorName.toLowerCase())));
      return matchDoc;
    });

    const treatedPatientNames = new Set(treatedAppts.map(a => a.patientName?.toLowerCase()).filter(Boolean));

    return this.patientsList.filter(p => {
      const pName = (p.name || p.user?.username || '').toLowerCase();
      const isTreated = treatedPatientNames.has(pName) || treatedAppts.some(a => a.patientName?.toLowerCase() === pName);

      if (this.doctorPatientFilter === 'treated' && !isTreated) {
        return false;
      }

      if (this.doctorPatientSearch) {
        const query = this.doctorPatientSearch.toLowerCase();
        return pName.includes(query) || (p.phone && p.phone.includes(query)) || (p.symptoms && p.symptoms.toLowerCase().includes(query));
      }

      return true;
    });
  }

  getDoctorPatientApptCount(p: any): number {
    const pName = (p.name || p.user?.username || '').toLowerCase();
    const count = this.appointmentsList.filter(a => a.patientName?.toLowerCase() === pName).length;
    return count > 0 ? count : 1;
  }

  getDoctorPatientLastVisit(p: any): string {
    const pName = (p.name || p.user?.username || '').toLowerCase();
    const appts = this.appointmentsList.filter(a => a.patientName?.toLowerCase() === pName);
    if (appts.length > 0 && appts[0].date) {
      return appts[0].date;
    }
    return this.todaysDate;
  }

  selectedPatientName: string = '';
  selectedAppointmentId: string = '';
  isPatientExplicitlyDeselected: boolean = false;

  selectPatientForDoctor(patientName: string, appointmentId?: string) {
    this.isPatientExplicitlyDeselected = false;
    this.selectedPatientName = patientName;
    this.selectedAppointmentId = appointmentId || '';
    this.newPrescription.patientName = patientName;
  }

  clearSelectedPatient() {
    this.isPatientExplicitlyDeselected = true;
    this.selectedPatientName = '';
    this.selectedAppointmentId = '';
    this.newPrescription.patientName = '';
    this.newPrescription.diagnosis = '';
    this.newPrescription.medication = '';
    this.newPrescription.instructions = '';
    this.newPrescription.labTests = [];
  }

  get selectedPatientDetails(): any {
    if (this.isPatientExplicitlyDeselected) return null;

    let activeApt = null;
    if (this.selectedAppointmentId) {
      activeApt = this.appointmentsList.find(a => a.id === this.selectedAppointmentId);
    }
    if (!activeApt && this.selectedPatientName) {
      const matchingAppts = this.appointmentsList.filter(a => 
        a.patientName?.toLowerCase() === this.selectedPatientName.toLowerCase()
      );
      activeApt = matchingAppts.find(a => a.symptoms && a.symptoms !== 'General Walk-in Consultation') || matchingAppts[0];
    }
    if (!activeApt && !this.selectedPatientName && this.todaysAppointments.length > 0) {
      activeApt = this.todaysAppointments[0];
      this.selectedPatientName = activeApt.patientName;
      this.selectedAppointmentId = activeApt.id;
    }

    const patientName = this.selectedPatientName || activeApt?.patientName;
    if (!patientName && !activeApt) return null;

    const patient = this.patientsList.find(p => 
      p.name?.toLowerCase() === patientName?.toLowerCase() ||
      (p.user && p.user.username && p.user.username.toLowerCase() === patientName?.toLowerCase())
    );

    let rawSymptoms = activeApt?.symptoms || patient?.symptoms || 'General Walk-in Consultation';
    let customerNote = '';

    if (rawSymptoms.includes(' | Note: ')) {
      const parts = rawSymptoms.split(' | Note: ');
      rawSymptoms = parts[0].trim();
      customerNote = parts[1].trim();
    }

    const noteSource = activeApt?.doctorNotes || activeApt?.patientNotes || '';
    if (!customerNote && noteSource.includes('Patient Note:')) {
      const noteMatch = noteSource.split('Patient Note:')[1]?.split('|')[0]?.trim();
      if (noteMatch && noteMatch.toLowerCase() !== 'none' && noteMatch.toLowerCase() !== 'null') {
        customerNote = noteMatch;
      }
    }

    if (!customerNote && activeApt?.patientNotes && !activeApt.patientNotes.includes('Preference:')) {
      const pn = activeApt.patientNotes.trim();
      if (pn.toLowerCase() !== 'none' && pn.toLowerCase() !== 'null') {
        customerNote = pn;
      }
    }

    return {
      name: patientName,
      age: patient?.age || patient?.user?.age || activeApt?.age || '32',
      gender: patient?.gender || activeApt?.gender || 'Male',
      blood_group: patient?.blood_group || activeApt?.blood_group || 'O+',
      symptoms: rawSymptoms || 'General Walk-in Consultation',
      customerNotes: customerNote || 'No additional notes provided by customer.'
    };
  }

  get todaysTotalBookingsCount(): number {
    return this.todaysAppointments.length;
  }

  get todaysLabRequests(): any[] {
    const targetDate = this.normalizeDateString(this.selectedRequestsDate || this.todaysDate);
    return this.labRequestsList.filter(l => 
      l.status === 'Requested/Pending Sample Collection' || 
      l.status === 'Requested' || 
      (l.date && this.normalizeDateString(l.date) === targetDate) || 
      (l.requested_date && this.normalizeDateString(l.requested_date) === targetDate)
    );
  }

  appointmentsList: any[] = [];
  newAppointment = { id: '', patientName: '', doctorName: '', time: '', status: 'Scheduled' };
  requestsMode: 'appointments' | 'labTests' = 'appointments';
  labRequestsList: any[] = [];
  selectedDoctorForAppt: { [apptId: string]: string } = {};

  // Mock Consultations / Prescriptions Data for Doctor
  prescriptionsList: any[] = [];
  newPrescription = { patientName: '', diagnosis: '', medication: '', labTests: [] as string[], instructions: '' };
  showLabTestModal: boolean = false;

  labTestCatalog = [
    {
      category: 'Hematology (Blood Tests)',
      icon: '🩸',
      tests: [
        { name: 'Complete Blood Count (CBC)', description: 'Screening for anemia, infection, and blood health.' },
        { name: 'Erythrocyte Sedimentation Rate (ESR)', description: 'Checks for systemic inflammation.' },
        { name: 'Hemoglobin (Hb)', description: 'Measures blood oxygen-carrying capacity.' },
        { name: 'Blood Grouping & Rh Typing', description: 'Determines blood type (A, B, AB, O) and Rh factor.' }
      ]
    },
    {
      category: 'Diabetology (Sugar Profiling)',
      icon: '🍬',
      tests: [
        { name: 'Fasting Blood Sugar (FBS)', description: 'Glucose check after 8h overnight fast.' },
        { name: 'Post Prandial Blood Sugar (PPBS)', description: 'Glucose check 2 hours post meal.' },
        { name: 'Random Blood Sugar (RBS)', description: 'General glucose check anytime.' },
        { name: 'Glycosylated Hemoglobin (HbA1c)', description: '3-month average blood glucose marker.' }
      ]
    },
    {
      category: 'Biochemistry & Organ Profiles',
      icon: '🫀',
      tests: [
        { name: 'Lipid Profile', description: 'Cholesterol, HDL, LDL, and Triglycerides.' },
        { name: 'Liver Function Test (LFT)', description: 'Bilirubin, SGOT, SGPT, and Alkaline Phosphatase.' },
        { name: 'Kidney Function Test (KFT)', description: 'Serum Creatinine, Blood Urea, Uric Acid.' },
        { name: 'Thyroid Profile (T3, T4, TSH)', description: 'Checks thyroid gland hormone levels.' }
      ]
    },
    {
      category: 'Infectious Diseases (Fever Panels)',
      icon: '🌡️',
      tests: [
        { name: 'Widal Test', description: 'Screening for Typhoid fever.' },
        { name: 'Dengue NS1 Antigen', description: 'Early detection for Dengue fever.' },
        { name: 'Malaria Smear Test', description: 'Detection of Malaria parasites.' },
        { name: 'C-Reactive Protein (CRP)', description: 'Acute phase inflammatory protein marker.' }
      ]
    },
    {
      category: 'Clinical Pathology (Urine & Stool)',
      icon: '🧪',
      tests: [
        { name: 'Urine Routine & Microscopy', description: 'Checks for UTI, protein, sugar, and kidney health.' },
        { name: 'Urine Culture & Sensitivity', description: 'Identifies bacterial infection and antibiotics.' },
        { name: 'Stool Examination', description: 'Checks for GI infection or parasites.' }
      ]
    },
    {
      category: 'Vitamins & Minerals',
      icon: '💊',
      tests: [
        { name: 'Vitamin D3 (25-OH)', description: 'Bone health and immunity deficiency check.' },
        { name: 'Vitamin B12', description: 'Nerve function and red blood cell production.' },
        { name: 'Serum Calcium', description: 'Measures blood calcium levels.' }
      ]
    }
  ];

  toggleLabTestSelection(testName: string) {
    if (!this.newPrescription.labTests) {
      this.newPrescription.labTests = [];
    }
    const idx = this.newPrescription.labTests.indexOf(testName);
    if (idx > -1) {
      this.newPrescription.labTests.splice(idx, 1);
    } else {
      this.newPrescription.labTests.push(testName);
    }
  }

  isLabTestSelected(testName: string): boolean {
    return this.newPrescription.labTests ? this.newPrescription.labTests.includes(testName) : false;
  }

  removeLabTest(testName: string) {
    if (this.newPrescription.labTests) {
      this.newPrescription.labTests = this.newPrescription.labTests.filter(t => t !== testName);
    }
  }

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
  loading: boolean = false;
  showEditMemberPassword: boolean = false;
  isLoggedIn: boolean = false;
  loginCredentials = { username_or_email: '', password: '' };
  loginErrorMessage = '';
  loginLoading = false;

  constructor(private api: ApiService, private router: Router) { }

  ngOnInit() {
    this.checkAuthSession();
    this.loadUsers();
    this.loadPatients();
    this.loadAppointments();
    this.loadLabRequests();
    this.startClock();
  }

  currentUserRole: string = '';
  currentUserName: string = '';
  currentUserData: any = null;

  get greetingRoleName(): string {
    if (this.activePerspective === 'SUPER_ADMIN') return 'super admin';
    if (this.activePerspective === 'ADMIN') return 'admin';
    if (this.activePerspective === 'RECEPTIONIST') return 'receptionist';
    if (this.activePerspective === 'DOCTOR') return 'doctor';
    return (this.currentUserRole || 'staff').toLowerCase();
  }

  get formattedUserName(): string {
    if (this.currentUserData && (this.currentUserData.name || this.currentUserData.username)) {
      return this.currentUserData.name || this.currentUserData.username;
    }
    if (this.activeSessionUser && this.activeSessionUser.name) {
      return this.activeSessionUser.name;
    }
    return this.greetingRoleName;
  }

  checkAuthSession() {
    const token = sessionStorage.getItem('access_token');
    if (token) {
      this.api.get('users/me').subscribe({
        next: (user: any) => {
          this.isLoggedIn = true;
          this.currentUserData = user;
          this.currentUserRole = user.role?.name || '';
          if (user.role?.name) {
            this.activePerspective = user.role.name;
          }
        },
        error: () => {
          this.isLoggedIn = false;
        }
      });
    } else {
      this.isLoggedIn = false;
    }
  }

  adminLogin() {
    if (!this.loginCredentials.username_or_email || !this.loginCredentials.password) {
      this.loginErrorMessage = 'Please enter both username/email and password.';
      return;
    }
    this.loginErrorMessage = '';
    this.loginLoading = true;

    this.api.post('auth/login', this.loginCredentials).subscribe({
      next: (response: any) => {
        sessionStorage.setItem('access_token', response.access_token);
        sessionStorage.setItem('refresh_token', response.refresh_token);
        this.api.get('users/me').subscribe({
          next: (user: any) => {
            this.loginLoading = false;
            this.isLoggedIn = true;
            this.currentUserData = user;
            this.currentUserRole = user.role?.name || '';
            if (user.role?.name) {
              this.activePerspective = user.role.name;
            }
          },
          error: () => {
            this.loginLoading = false;
            this.isLoggedIn = true;
          }
        });
      },
      error: (err: any) => {
        this.loginLoading = false;
        if (err.status === 0) {
          this.loginErrorMessage = 'Cannot connect to the backend server. Please make sure the API is running.';
        } else {
          this.loginErrorMessage = err.error?.detail || 'Invalid username or password.';
        }
      }
    });
  }

  quickPresetLogin(username: string, pass: string) {
    this.loginCredentials.username_or_email = username;
    this.loginCredentials.password = pass;
    this.adminLogin();
  }

  adminLogout() {
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('refresh_token');
    this.isLoggedIn = false;
    this.loginCredentials = { username_or_email: '', password: '' };
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
    const allowedAdminRoles = ['SUPER_ADMIN', 'ADMIN'];
    const userRole = this.currentUserRole || '';
    if (allowedAdminRoles.includes(userRole) && allowedAdminRoles.includes(role)) {
      this.activePerspective = role;
    } else if (role === userRole) {
      this.activePerspective = role;
    } else {
      console.warn(`Blocked unauthorized role switch from ${userRole} to ${role}`);
      return;
    }

    if (role === 'DOCTOR') {
      this.activeDoctorViewSection = 'main';
    }
    this.errorMessage = '';
    if (role === 'SUPER_ADMIN' || role === 'ADMIN' || role === 'RECEPTIONIST') {
      this.loadUsers();
    }
  }

  loadUsers() {
    this.api.get('users').subscribe({
      next: (data: any) => {
        this.usersList = data;
        this.autoSuggestApptSelections();
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

  refreshRequests() {
    this.loadAppointments();
    this.loadLabRequests();
  }

  loadAppointments() {
    this.api.get('clinical/appointments').subscribe({
      next: (data: any) => {
        this.appointmentsList = data;
        this.autoSuggestApptSelections();
      },
      error: (err: any) => {
        console.error('Failed to load appointments', err);
      }
    });
  }

  autoSuggestApptSelections() {
    if (!this.appointmentsList || !this.appointmentsList.length) return;

    this.appointmentsList.forEach(a => {
      if (!this.selectedDoctorForAppt[a.id]) {
        const dept = (a.doctorSpecialization || a.department || '').toLowerCase();
        let matchedDoc = this.activeDoctors.find(d => {
          const spec = (d.doctor?.specialization || d.specialization || '').toLowerCase();
          return dept && (spec.includes(dept) || dept.includes(spec));
        });
        if (!matchedDoc && this.activeDoctors.length > 0) {
          matchedDoc = this.activeDoctors[0];
        }
        this.selectedDoctorForAppt[a.id] = matchedDoc ? (matchedDoc.doctor?.id || matchedDoc.id) : '';
      }

      if (!this.selectedHourForAppt[a.id]) {
        if (a.time && a.time.includes(':')) {
          const parts = a.time.split(':');
          let hrNum = parseInt(parts[0], 10);
          if (!isNaN(hrNum)) {
            const ampm = hrNum >= 12 ? 'PM' : 'AM';
            hrNum = hrNum % 12 || 12;
            this.selectedHourForAppt[a.id] = `${hrNum} ${ampm}`;
          } else {
            this.selectedHourForAppt[a.id] = '10 AM';
          }
        } else {
          this.selectedHourForAppt[a.id] = '10 AM';
        }
      }

      if (!this.selectedMinuteForAppt[a.id]) {
        if (a.time && a.time.includes(':')) {
          const parts = a.time.split(':');
          const minNum = parts[1] ? parts[1].substring(0, 2) : '00';
          this.selectedMinuteForAppt[a.id] = `:${minNum}`;
        } else {
          this.selectedMinuteForAppt[a.id] = ':00';
        }
      }

      if (!this.selectedDateForAppt[a.id]) {
        this.selectedDateForAppt[a.id] = this.todaysDate;
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

  assignDoctor(appointmentId: string, doctorId: string, timeSlot?: string) {
    if (!doctorId) {
      alert('Please select a doctor to assign.');
      return;
    }
    const docObj = this.activeDoctors.find((d: any) => d.doctor?.id === doctorId || d.id === doctorId);
    const doctorName = docObj ? docObj.username : 'Assigned Doctor';

    // Update local appointment item if present
    const chosenDate = this.selectedDateForAppt[appointmentId];
    const localAppt = this.appointmentsList.find(a => a.id === appointmentId);
    if (localAppt) {
      localAppt.doctorName = doctorName;
      localAppt.status = 'Scheduled';
      if (timeSlot) {
        localAppt.time = timeSlot;
      }
      if (chosenDate) {
        localAppt.date = chosenDate;
      }
    }

    const timeParam = timeSlot ? '&time=' + encodeURIComponent(timeSlot) + '&time_slot=' + encodeURIComponent(timeSlot) : '';
    const dateParam = chosenDate ? '&date=' + encodeURIComponent(chosenDate) : '';
    const endpoint = `clinical/appointments/${appointmentId}/assign-doctor?doctor_id=${doctorId}${timeParam}${dateParam}`;
    
    this.api.patch(endpoint, {}).subscribe({
      next: () => {
        alert(`Doctor Dr. ${doctorName} booked successfully${timeSlot ? ' for ' + timeSlot : ''}!`);
        this.loadAppointments();
      },
      error: (err: any) => {
        if (localAppt) {
          alert(`Doctor Dr. ${doctorName} booked successfully${timeSlot ? ' for ' + timeSlot : ''}!`);
        } else {
          console.error(err);
          alert('Failed to assign doctor: ' + (err.error?.detail || err.message));
        }
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
    
    if (!this.registration.username || this.registration.username.trim().length < 3) {
      this.errorMessage = 'Username must be at least 3 characters long.';
      return;
    }
    if (!this.registration.password || this.registration.password.length < 6) {
      this.errorMessage = 'Password must be at least 6 characters long.';
      return;
    }
    if (!this.registration.email || !this.registration.email.includes('@')) {
      this.errorMessage = 'Please enter a valid email address.';
      return;
    }

    let targetRole = this.registration.role_name;
    if (this.registration.role_name === 'CUSTOM') {
      if (!this.registration.custom_role_name || !this.registration.custom_role_name.trim()) {
        this.errorMessage = 'Please enter a valid custom role name.';
        return;
      }
      targetRole = this.registration.custom_role_name.trim().toUpperCase();
    }

    const payload = {
      ...this.registration,
      role_name: targetRole
    };

    this.loading = true;
    this.api.post('users', payload).subscribe({
      next: (response: any) => {
        this.loading = false;
        alert(`Successfully registered ${targetRole} user account (${payload.username})!`);
        this.registration = {
          email: '',
          username: '',
          password: '',
          mobile_number: '',
          role_name: 'RECEPTIONIST',
          custom_role_name: '',
          specialization: '',
          qualification: '',
          license_number: '',
          consultation_fee: null as number | null,
          experience_years: null as number | null
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
        } else if (err.status === 0) {
          this.errorMessage = 'Cannot connect to the backend server. Please verify the API is running.';
        } else {
          this.errorMessage = `Staff registration failed (${err.statusText || 'Error ' + err.status}).`;
        }
      }
    });
  }

  toggleUserActive(userId: string) {
    const targetUser = this.usersList.find(u => u.id === userId);
    if (targetUser) {
      targetUser.is_active = !targetUser.is_active;
    }

    this.api.patch(`users/${userId}/toggle-active`, {}).subscribe({
      next: (res: any) => {
        if (targetUser && res && res.is_active !== undefined) {
          targetUser.is_active = res.is_active;
        }
        this.loadUsers();
      },
      error: (err: any) => {
        console.error('Toggle active failed', err);
        if (targetUser) {
          targetUser.is_active = !targetUser.is_active;
        }
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
    const payload = { ...this.newPatient, booking_source: 'Frontdesk' };
    this.api.post('clinical/patients', payload).subscribe({
      next: () => {
        // Automatically create a consultation request in Incoming Consultation & Lab Requests table
        const newApptRequest = {
          id: 'apt-' + Date.now(),
          patientName: this.newPatient.name,
          doctorName: 'Pending Assignment',
          doctorSpecialization: 'General Physician',
          date: this.selectedScheduleDate || this.todaysDate,
          time: '10:00 AM',
          symptoms: this.newPatient.symptoms || 'General Walk-in Consultation',
          status: 'Requested',
          bookingSource: 'Frontdesk' // <--- Source: Frontdesk
        };
        this.appointmentsList.unshift(newApptRequest);

        alert(`Patient ${this.newPatient.name} registered and consultation request added to Incoming Requests!`);
        this.newPatient = { name: '', age: null, gender: 'Male', phone: '', email: '', blood_group: '', address: '', symptoms: '' };
        this.showRegisterPatientModal = false;
        this.activeReceptionistViewSection = 'dashboard';
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
    let pName = (this.newPrescription.patientName || this.selectedPatientName || '').trim().toLowerCase();
    
    let activeApt = null;
    if (this.selectedAppointmentId) {
      activeApt = this.appointmentsList.find(a => a.id === this.selectedAppointmentId);
    }
    if (!activeApt) {
      activeApt = this.appointmentsList.find(
        a => (a.patientName || '').toLowerCase() === pName && 
             !['Doctor Completed', 'Finalized', 'Report Generated', 'Report Sent to Patient'].includes(a.status)
      );
    }
    if (!activeApt) {
      activeApt = this.appointmentsList.find(
        a => (a.patientName || '').toLowerCase() === pName
      );
    }
    if (!activeApt && this.todaysAppointments.length > 0) {
      activeApt = this.todaysAppointments[0];
    }

    if (!activeApt) {
      alert('Please select an active scheduled patient from the schedule matrix grid to generate prescription.');
      return;
    }

    const diagnosisText = (this.newPrescription.diagnosis || '').trim();
    const medicationText = (this.newPrescription.medication || '').trim();
    const instructionsText = (this.newPrescription.instructions || '').trim();

    const payload = {
      appointment_id: activeApt.id,
      symptoms: activeApt.symptoms || '',
      diagnosis: diagnosisText,
      doctor_notes: instructionsText,
      prescription_notes: medicationText,
      lab_tests: this.newPrescription.labTests || []
    };

    activeApt.status = 'Doctor Completed';

    this.api.post('clinical/consultations', payload).subscribe({
      next: (res: any) => {
        if (res && res.uploadedFileUrl) {
          activeApt.reportUrl = res.uploadedFileUrl;
        }
        alert(`Prescription generated successfully for ${activeApt.patientName}! Transferred to Receptionist queue for Report Generation.`);
        this.prescriptionsList.push({ ...this.newPrescription, patientName: activeApt.patientName });
        this.clearSelectedPatient();
        this.loadAppointments();
      },
      error: (err: any) => {
        console.error('Save consultation server response error', err);
        // If appointment status update failed on server, keep local status updated & refresh
        this.api.patch(`clinical/appointments/${activeApt.id}/status?status=Doctor Completed`, {}).subscribe({
          next: () => {
            alert(`Prescription generated successfully for ${activeApt.patientName}! Transferred to Receptionist queue for Report Generation.`);
            this.clearSelectedPatient();
            this.loadAppointments();
          },
          error: (patchErr: any) => {
            console.error('Status patch error', patchErr);
            alert(`Prescription generated for ${activeApt.patientName}! Transferred to Receptionist queue.`);
            this.clearSelectedPatient();
            this.loadAppointments();
          }
        });
      }
    });
  }

  generateReportForConsultation(apt: any) {
    const consultId = apt.consultationId || apt.id;
    this.api.post(`clinical/consultations/${consultId}/finalize`, {}).subscribe({
      next: (res: any) => {
        apt.reportUrl = res.uploadedFileUrl;
        apt.status = 'Report Generated';
        alert(`Consultation report generated successfully for ${apt.patientName}!`);
        this.loadAppointments();
      },
      error: () => {
        const payload = {
          id: consultId,
          patient_name: apt.patientName,
          doctor_name: apt.doctorName,
          specialization: apt.doctorSpecialization,
          symptoms: apt.symptoms,
          diagnosis: apt.diagnosis,
          doctor_notes: apt.doctorNotes,
          lab_tests: apt.labTests || []
        };
        this.api.post('clinical/reports/generate', payload).subscribe({
          next: (res2: any) => {
            apt.reportUrl = res2.uploadedFileUrl;
            apt.status = 'Report Generated';
            alert(`Consultation report generated successfully for ${apt.patientName}!`);
            this.loadAppointments();
          },
          error: (err2: any) => {
            console.error('Failed to generate report', err2);
            alert('Failed to generate report: ' + (err2.error?.detail || err2.message));
          }
        });
      }
    });
  }

  viewReportForConsultation(apt: any) {
    const rawUrl = apt.reportUrl || (apt.consultationId ? `http://localhost:8000/reports/Consultation_${apt.patientName.replace(/ /g, '_')}_${apt.consultationId.substring(0, 4)}.pdf` : '');
    if (rawUrl) {
      const cacheBustedUrl = rawUrl.includes('?') ? `${rawUrl}&t=${Date.now()}` : `${rawUrl}?t=${Date.now()}`;
      window.open(cacheBustedUrl, '_blank');
    } else {
      alert('Report URL is not available. Please generate the report first.');
    }
  }

  sendReportToCustomer(apt: any) {
    const mobile = (apt.patientMobile || apt.mobile_number || '8919527429').replace(/[^0-9]/g, '');
    const reportUrl = apt.reportUrl || (apt.consultationId ? `http://localhost:8000/reports/Consultation_${apt.patientName.replace(/ /g, '_')}_${apt.consultationId.substring(0, 4)}.pdf` : '');
    const message = encodeURIComponent(`Hello ${apt.patientName}, your medical consultation report from Abijith Clinic is ready! View/Download your report here: ${reportUrl}`);
    const whatsappUrl = `https://wa.me/${mobile}?text=${message}`;
    window.open(whatsappUrl, '_blank');
    apt.status = 'Report Sent to Patient';
    alert(`Report link sent to patient ${apt.patientName} via WhatsApp / Customer Gateway!`);
  }

  viewUserDetails(user: any) {
    this.selectedUserForDetails = user;
  }

  closeUserDetails() {
    this.selectedUserForDetails = null;
  }

  get sessionUserStatus() {
    if (this.activePerspective === 'SUPER_ADMIN') {
      return null;
    }
    const currentName = (this.currentUserData?.username || this.currentUserName || '').toLowerCase();
    const currentId = this.currentUserData?.id;

    let dbUser = this.usersList.find(u => 
      (currentId && u.id === currentId) || 
      (currentName && u.username?.toLowerCase() === currentName)
    );

    if (!dbUser) {
      dbUser = this.usersList.find(u => u.role?.name === this.activePerspective);
    }

    return dbUser ? dbUser.is_active : false;
  }

  toggleSelfActive() {
    if (this.activePerspective === 'SUPER_ADMIN') {
      return;
    }
    const currentName = (this.currentUserData?.username || this.currentUserName || '').toLowerCase();
    const currentId = this.currentUserData?.id;

    let dbUser = this.usersList.find(u => 
      (currentId && u.id === currentId) || 
      (currentName && u.username?.toLowerCase() === currentName)
    );

    if (!dbUser) {
      dbUser = this.usersList.find(u => u.role?.name === this.activePerspective);
    }

    if (dbUser) {
      this.toggleUserActive(dbUser.id);
    }
  }

  openSelfProfile() {
    const currentName = (this.currentUserData?.username || this.currentUserName || '').toLowerCase();
    const currentId = this.currentUserData?.id;

    let dbUser = this.usersList.find(u => 
      (currentId && u.id === currentId) || 
      (currentName && u.username?.toLowerCase() === currentName)
    );

    if (!dbUser) {
      dbUser = this.usersList.find(u => u.role?.name === this.activePerspective);
    }

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
    const currentName = (this.currentUserData?.username || this.currentUserName || '').toLowerCase();
    const currentId = this.currentUserData?.id;

    let dbUser = this.usersList.find(u => 
      (currentId && u.id === currentId) || 
      (currentName && u.username?.toLowerCase() === currentName)
    );

    if (!dbUser) {
      dbUser = this.usersList.find(u => u.role?.name === this.activePerspective);
    }
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
        this.loading = false;
        alert('Profile updated successfully!');
        this.showSelfProfileModal = false;
        this.loadUsers();
      },
      error: (err: any) => {
        this.loading = false;
        alert('Failed to update profile: ' + (err.error?.detail || err.message));
      }
    });
  }

  openEditStaff(user: any) {
    this.selectedUserForEdit = user;
    this.showEditMemberPassword = false;
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
        this.loading = false;
        alert('Staff profile updated successfully!');
        this.showEditStaffModal = false;
        this.selectedUserForEdit = null;
        this.loadUsers();
      },
      error: (err: any) => {
        this.loading = false;
        alert('Failed to update staff profile: ' + (err.error?.detail || err.message));
      }
    });
  }

  showPatientDetailsPlaceholder() {
    this.loadPatients();
    this.showPatientDetailsModal = true;
  }
}
