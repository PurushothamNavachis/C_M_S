import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { ReceptionistPage } from './receptionist.page';

const routes: Routes = [
  {
    path: '',
    component: ReceptionistPage
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class ReceptionistPageRoutingModule {}
