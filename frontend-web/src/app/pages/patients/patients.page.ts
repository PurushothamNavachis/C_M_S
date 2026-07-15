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
}
