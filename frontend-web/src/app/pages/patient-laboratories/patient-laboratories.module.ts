import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { PatientLaboratoriesPageRoutingModule } from './patient-laboratories-routing.module';

import { PatientLaboratoriesPage } from './patient-laboratories.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    PatientLaboratoriesPageRoutingModule
  ],
  declarations: [PatientLaboratoriesPage]
})
export class PatientLaboratoriesPageModule {}
