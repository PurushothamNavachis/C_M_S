import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PatientLaboratoriesPage } from './patient-laboratories.page';

describe('PatientLaboratoriesPage', () => {
  let component: PatientLaboratoriesPage;
  let fixture: ComponentFixture<PatientLaboratoriesPage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(PatientLaboratoriesPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
