import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { PatientConsultationsPage } from './patient-consultations.page';

const routes: Routes = [
  {
    path: '',
    component: PatientConsultationsPage
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class PatientConsultationsPageRoutingModule {}
