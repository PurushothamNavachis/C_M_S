import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReceptionistPage } from './receptionist.page';

describe('ReceptionistPage', () => {
  let component: ReceptionistPage;
  let fixture: ComponentFixture<ReceptionistPage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(ReceptionistPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
