import { NgModule } from '@angular/core';
import { PreloadAllModules, RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  {
    path: '',
    redirectTo: 'home',
    pathMatch: 'full'
  },
  {
    path: 'home',
    loadChildren: () => import('./pages/home/home.module').then( m => m.HomePageModule)
  },
  {
    path: 'services',
    loadChildren: () => import('./pages/services/services.module').then( m => m.ServicesPageModule)
  },
  {
    path: 'doctors',
    loadChildren: () => import('./pages/doctors/doctors.module').then( m => m.DoctorsPageModule)
  },
  {
    path: 'login',
    loadChildren: () => import('./pages/login/login.module').then( m => m.LoginPageModule)
  },
  {
    path: 'register',
    loadChildren: () => import('./pages/register/register.module').then( m => m.RegisterPageModule)
  },
  {
    path: 'super-admin',
    loadChildren: () => import('./portals/super-admin/super-admin.module').then( m => m.SuperAdminPageModule)
  },
  {
    path: 'admin',
    loadChildren: () => import('./portals/admin/admin.module').then( m => m.AdminPageModule)
  },
  {
    path: 'receptionist',
    loadChildren: () => import('./portals/receptionist/receptionist.module').then( m => m.ReceptionistPageModule)
  },
  {
    path: 'doctor',
    loadChildren: () => import('./portals/doctor/doctor.module').then( m => m.DoctorPageModule)
  },
  {
    path: 'patient',
    loadChildren: () => import('./portals/patient/patient.module').then( m => m.PatientPageModule)
  },
  {
    path: 'administration',
    loadChildren: () => import('./pages/administration/administration.module').then( m => m.AdministrationPageModule)
  },
  {
    path: 'patients',
    loadChildren: () => import('./pages/patients/patients.module').then( m => m.PatientsPageModule)
  },
  {
    path: 'patients/:id/consultations',
    loadChildren: () => import('./pages/patient-consultations/patient-consultations.module').then( m => m.PatientConsultationsPageModule)
  },
  {
    path: 'patients/:id/laboratories',
    loadChildren: () => import('./pages/patient-laboratories/patient-laboratories.module').then( m => m.PatientLaboratoriesPageModule)
  }
];
@NgModule({
  imports: [
    RouterModule.forRoot(routes, { preloadingStrategy: PreloadAllModules })
  ],
  exports: [RouterModule]
})
export class AppRoutingModule {}
