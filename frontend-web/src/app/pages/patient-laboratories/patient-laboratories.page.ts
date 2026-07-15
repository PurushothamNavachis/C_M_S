import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-patient-laboratories',
  templateUrl: './patient-laboratories.page.html',
  styleUrls: ['./patient-laboratories.page.scss'],
  standalone: false
})
export class PatientLaboratoriesPage implements OnInit {
  patientId: string = '';
  patientName: string = '';
  reportsList: any[] = [];
  loading: boolean = false;

  editingReportId: string | null = null;
  editStatus: string = '';
  editFileUrl: string = '';
  saving: boolean = false;

  userRole: string = '';
  showResultsForm: boolean = false;
  selectedLabDate: string = '';
  resultsForm = {
    resultValue: ''
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
      this.loadLabRequests();
      this.loadCurrentUserRole();
    }
  }

  loadCurrentUserRole() {
    this.api.get('users/me').subscribe({
      next: (user: any) => {
        this.userRole = user.role?.name || '';
      },
      error: () => {
        this.userRole = 'SUPER_ADMIN';
      }
    });
  }

  loadPatientInfo() {
    this.api.get('clinical/patients').subscribe({
      next: (data: any[]) => {
        const found = data.find(p => p.id === this.patientId);
        if (found) {
          this.patientName = found.name;
        }
      },
      error: (err) => console.error('Failed to load patient name', err)
    });
  }

  loadLabRequests() {
    this.loading = true;
    this.api.get(`clinical/patients/${this.patientId}/lab-requests`).subscribe({
      next: (data: any) => {
        this.reportsList = data;
        this.loading = false;
      },
      error: (err: any) => {
        console.error('Failed to load patient lab requests', err);
        this.loading = false;
      }
    });
  }

  approveLab(date: string) {
    this.actionLoading = true;
    this.api.post(`clinical/lab-requests/group/${this.patientId}/${date}/approve`, {}).subscribe({
      next: () => {
        this.actionLoading = false;
        alert('Lab requests approved successfully!');
        this.loadLabRequests();
      },
      error: (err) => {
        this.actionLoading = false;
        console.error(err);
        alert('Failed to approve lab requests');
      }
    });
  }

  cancelLab(date: string) {
    if (!confirm('Are you sure you want to cancel these lab requests?')) return;
    this.actionLoading = true;
    this.api.post(`clinical/lab-requests/group/${this.patientId}/${date}/cancel`, {}).subscribe({
      next: () => {
        this.actionLoading = false;
        alert('Lab requests cancelled.');
        this.loadLabRequests();
      },
      error: (err) => {
        this.actionLoading = false;
        console.error(err);
        alert('Failed to cancel lab requests');
      }
    });
  }

  openResultsModal(r: any) {
    this.selectedLabDate = r.date;
    this.resultsForm.resultValue = r.resultValue || '';
    this.showResultsForm = true;
  }

  closeResultsModal() {
    this.showResultsForm = false;
    this.selectedLabDate = '';
  }

  submitResults() {
    if (!this.resultsForm.resultValue) {
      alert('Please enter a result or status description.');
      return;
    }
    this.actionLoading = true;
    const payload = {
      result_value: this.resultsForm.resultValue
    };
    this.api.post(`clinical/lab-requests/group/${this.patientId}/${this.selectedLabDate}/submit`, payload).subscribe({
      next: () => {
        this.actionLoading = false;
        this.showResultsForm = false;
        alert('Lab results submitted to receptionist.');
        this.loadLabRequests();
      },
      error: (err) => {
        this.actionLoading = false;
        console.error(err);
        alert('Failed to submit lab results');
      }
    });
  }

  finalizeLab(r: any) {
    this.actionLoading = true;
    const payload = {
      result_value: r.resultValue || 'Completed'
    };
    this.api.post(`clinical/lab-requests/group/${this.patientId}/${r.date}/finalize`, payload).subscribe({
      next: () => {
        this.actionLoading = false;
        alert('Lab reports finalized and A4 PDF successfully generated!');
        this.loadLabRequests();
      },
      error: (err) => {
        this.actionLoading = false;
        console.error(err);
        alert('Failed to finalize lab reports');
      }
    });
  }

  startEdit(report: any) {
    this.editingReportId = report.id;
    this.editStatus = report.status || 'Requested';
    this.editFileUrl = report.uploadedFileUrl || '';
  }

  cancelEdit() {
    this.editingReportId = null;
    this.editStatus = '';
    this.editFileUrl = '';
  }

  saveReport() {
    if (!this.editingReportId) return;
    this.saving = true;
    
    const payload = {
      status: this.editStatus,
      uploaded_file_url: this.editFileUrl
    };

    this.api.patch(`clinical/lab-reports/${this.editingReportId}`, payload).subscribe({
      next: () => {
        this.saving = false;
        this.editingReportId = null;
        this.loadLabRequests();
      },
      error: (err: any) => {
        console.error('Failed to save lab report changes', err);
        this.saving = false;
      }
    });
  }

  sendReport(report: any) {
    report.isSent = true;
    report.sending = true;
    setTimeout(() => {
      report.sending = false;
    }, 400);
  }
}
