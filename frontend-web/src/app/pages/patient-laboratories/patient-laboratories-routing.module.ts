import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { PatientLaboratoriesPage } from './patient-laboratories.page';

const routes: Routes = [
  {
    path: '',
    component: PatientLaboratoriesPage
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class PatientLaboratoriesPageRoutingModule {}
