import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { PatientConsultationsPageRoutingModule } from './patient-consultations-routing.module';

import { PatientConsultationsPage } from './patient-consultations.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    PatientConsultationsPageRoutingModule
  ],
  declarations: [PatientConsultationsPage]
})
export class PatientConsultationsPageModule {}
