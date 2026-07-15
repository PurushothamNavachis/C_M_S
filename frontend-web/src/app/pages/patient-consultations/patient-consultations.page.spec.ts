import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PatientConsultationsPage } from './patient-consultations.page';

describe('PatientConsultationsPage', () => {
  let component: PatientConsultationsPage;
  let fixture: ComponentFixture<PatientConsultationsPage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(PatientConsultationsPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
