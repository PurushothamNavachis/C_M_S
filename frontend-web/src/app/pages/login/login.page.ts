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
        // Save token to localstorage
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('refresh_token', response.refresh_token);
        
        // Fetch user profile to route properly
        this.api.get('users/me').subscribe({
          next: (user) => {
            this.loading = false;
            alert('Login Successful!');
            if (user.role?.name === 'PATIENT') {
              this.router.navigate(['/patient']);
            } else {
              this.router.navigate(['/administration']);
            }
          },
          error: (err) => {
            this.loading = false;
            this.router.navigate(['/administration']);
            alert('Login Successful!');
          }
        });
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err.error?.detail || 'Invalid username or password.';
      }
    });
  }
}
