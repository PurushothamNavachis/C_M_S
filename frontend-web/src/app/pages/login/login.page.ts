import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-login',
  templateUrl: './login.page.html',
  styleUrls: ['./login.page.scss'],
  standalone: false,
})
export class LoginPage {
  credentials = {
    username_or_email: '',
    password: ''
  };
  errorMessage = '';
  loading = false;

  constructor(private api: ApiService, private router: Router) { }

  onLogin() {
    this.errorMessage = '';
    this.loading = true;
    this.api.post('auth/login', this.credentials).subscribe({
      next: (response) => {
        this.loading = false;
        // Save token to localstorage
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('refresh_token', response.refresh_token);
        this.router.navigate(['/administration']);
        alert('Login Successful!');
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err.error?.detail || 'Invalid username or password.';
      }
    });
  }
}
