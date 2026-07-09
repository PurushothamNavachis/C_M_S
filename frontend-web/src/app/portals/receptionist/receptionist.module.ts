import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { ReceptionistPageRoutingModule } from './receptionist-routing.module';

import { ReceptionistPage } from './receptionist.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    ReceptionistPageRoutingModule
  ],
  declarations: [ReceptionistPage]
})
export class ReceptionistPageModule {}
