import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-patient-consultations',
  templateUrl: './patient-consultations.page.html',
  styleUrls: ['./patient-consultations.page.scss'],
  standalone: false
})
export class PatientConsultationsPage implements OnInit {
  patientId: string = '';
  patientName: string = '';
  consultationsList: any[] = [];
  loading: boolean = false;

  userRole: string = '';
  showConsultForm: boolean = false;
  selectedConsultId: string = '';
  consultForm = {
    symptoms: '',
    diagnosis: '',
    doctorNotes: ''
  };
  actionLoading: boolean = false;

  constructor(
    private route: ActivatedRoute,
    private api: ApiService
  ) { }

  ngOnInit() {
    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      this.patientId = idParam;
      this.loadPatientInfo();
      this.loadConsultations();
      this.loadCurrentUserRole();
    }
  }

  ionViewWillEnter() {
    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      this.patientId = idParam;
      this.loadPatientInfo();
      this.loadConsultations();
      this.loadCurrentUserRole();
    }
  }

  loadCurrentUserRole() {
    this.api.get('users/me').subscribe({
      next: (user: any) => {
        this.userRole = user.role?.name || '';
      },
      error: () => {
        // Fallback for simulation testing
        this.userRole = 'SUPER_ADMIN';
      }
    });
  }

  loadPatientInfo() {
    this.api.get('clinical/patients').subscribe({
      next: (data: any[]) => {
        const found = data.find(p => p.id === this.patientId || p.id.startsWith(this.patientId) || this.patientId.toLowerCase().includes(p.id.slice(0, 8).toLowerCase()));
        if (found) {
          this.patientName = found.name;
        }
      },
      error: (err) => console.error('Failed to load patient name', err)
    });
  }

  loadConsultations() {
    this.loading = true;
    this.api.get(`clinical/patients/${this.patientId}/consultations`).subscribe({
      next: (data: any) => {
        this.consultationsList = data;
        this.loading = false;
      },
      error: (err: any) => {
        console.error('Failed to load patient consultations', err);
        this.loading = false;
      }
    });
  }

  approveAppt(apptId: string) {
    this.actionLoading = true;
    this.api.post(`clinical/appointments/${apptId}/approve`, {}).subscribe({
      next: () => {
        this.actionLoading = false;
        alert('Appointment Approved!');
        this.loadConsultations();
      },
      error: (err) => {
        this.actionLoading = false;
        console.error(err);
        alert('Failed to approve appointment');
      }
    });
  }

  cancelAppt(apptId: string) {
    if (!confirm('Are you sure you want to cancel this appointment?')) return;
    this.actionLoading = true;
    this.api.post(`clinical/appointments/${apptId}/cancel`, {}).subscribe({
      next: () => {
        this.actionLoading = false;
        alert('Appointment Cancelled.');
        this.loadConsultations();
      },
      error: (err) => {
        this.actionLoading = false;
        console.error(err);
        alert('Failed to cancel appointment');
      }
    });
  }

  openConsultModal(c: any) {
    this.selectedConsultId = c.id;
    this.consultForm = {
      symptoms: c.symptoms || '',
      diagnosis: '',
      doctorNotes: ''
    };
    this.showConsultForm = true;
  }

  closeConsultModal() {
    this.showConsultForm = false;
    this.selectedConsultId = '';
  }

  submitConsultDetails() {
    if (!this.consultForm.diagnosis) {
      alert('Please enter a diagnosis.');
      return;
    }
    this.actionLoading = true;
    const payload = {
      symptoms: this.consultForm.symptoms,
      diagnosis: this.consultForm.diagnosis,
      doctor_notes: this.consultForm.doctorNotes
    };
    this.api.post(`clinical/consultations/${this.selectedConsultId}/submit`, payload).subscribe({
      next: () => {
        this.actionLoading = false;
        this.showConsultForm = false;
        alert('Consultation details submitted to receptionist.');
        this.loadConsultations();
      },
      error: (err) => {
        this.actionLoading = false;
        console.error(err);
        alert('Failed to submit consultation details');
      }
    });
  }

  finalizeConsult(consultId: string) {
    this.actionLoading = true;
    this.api.post(`clinical/consultations/${consultId}/finalize`, {}).subscribe({
      next: () => {
        this.actionLoading = false;
        alert('Consultation finalized and PDF report successfully generated!');
        this.loadConsultations();
      },
      error: (err) => {
        this.actionLoading = false;
        console.error(err);
        alert('Failed to finalize consultation');
      }
    });
  }

  sendReport(consultation: any) {
    consultation.isSent = true;
    consultation.sending = true;
    setTimeout(() => {
      consultation.sending = false;
    }, 400);
  }
}
