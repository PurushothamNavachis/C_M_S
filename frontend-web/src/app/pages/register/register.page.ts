import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-register',
  templateUrl: './register.page.html',
  styleUrls: ['./register.page.scss'],
  standalone: false,
})
export class RegisterPage {
  registration = {
    email: '',
    username: '',
    password: ''
  };
  errorMessage = '';
  loading = false;

  constructor(private api: ApiService, private router: Router) { }

  onRegister() {
    this.errorMessage = '';
    this.loading = true;
    this.api.post('auth/register', this.registration).subscribe({
      next: (response) => {
        this.loading = false;
        alert('Registration Successful! Please log in.');
        this.router.navigate(['/login']);
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err.error?.detail || 'Registration failed. Check details.';
      }
    });
  }
}
