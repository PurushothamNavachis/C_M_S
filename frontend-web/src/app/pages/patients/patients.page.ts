import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-patients',
  templateUrl: './patients.page.html',
  styleUrls: ['./patients.page.scss'],
  standalone: false,
})
export class PatientsPage implements OnInit {
  patientsList: any[] = [];
  loading: boolean = false;
  searchTerm: string = '';

  showEditPatientModal: boolean = false;
  selectedPatientForEdit: any = null;
  showPatientPassword: boolean = false;
  savingPatient: boolean = false;

  editPatientForm: any = {
    username: '',
    email: '',
    mobile_number: '',
    blood_group: '',
    gender: '',
    password: ''
  };

  get filteredPatients() {
    return this.patientsList.filter(p => {
      const term = this.searchTerm.trim().toLowerCase();
      if (!term) return true;
      
      const matchName = p.name ? p.name.toLowerCase().includes(term) : false;
      
      const cardId = p.id ? p.id.slice(0, 8).toLowerCase() : '';
      const matchCardId = cardId.includes(term) || `#${cardId}`.includes(term);
      
      return matchName || matchCardId;
    });
  }

  constructor(private api: ApiService) { }

  ngOnInit() {
    this.loadPatients();
  }

  ionViewWillEnter() {
    this.loadPatients();
  }

  loadPatients() {
    this.loading = true;
    this.api.get('clinical/patients').subscribe({
      next: (data: any) => {
        this.patientsList = data;
        this.loading = false;
      },
      error: (err: any) => {
        console.error('Failed to load patients', err);
        this.loading = false;
      }
    });
  }

  openEditPatientModal(patient: any) {
    this.selectedPatientForEdit = patient;
    this.showPatientPassword = false;
    this.editPatientForm = {
      username: patient.name || '',
      email: patient.email || '',
      mobile_number: patient.phone || '',
      blood_group: patient.blood_group || '',
      gender: patient.gender || '',
      password: ''
    };
    this.showEditPatientModal = true;
  }

  savePatientEdit() {
    if (!this.selectedPatientForEdit) return;
    this.savingPatient = true;

    const targetUserId = this.selectedPatientForEdit.user_id || this.selectedPatientForEdit.id;
    const payload: any = {
      username: this.editPatientForm.username,
      email: this.editPatientForm.email,
      mobile_number: this.editPatientForm.mobile_number,
      blood_group: this.editPatientForm.blood_group,
      gender: this.editPatientForm.gender
    };
    if (this.editPatientForm.password && this.editPatientForm.password.trim() !== '') {
      payload.password = this.editPatientForm.password;
    }

    (this.api as any).put(`users/${targetUserId}`, payload).subscribe({
      next: () => {
        this.savingPatient = false;
        alert('Patient profile updated successfully!');
        this.showEditPatientModal = false;
        this.selectedPatientForEdit = null;
        this.loadPatients();
      },
      error: (err: any) => {
        this.savingPatient = false;
        alert('Failed to update patient profile: ' + (err.error?.detail || err.message));
      }
    });
  }
}
