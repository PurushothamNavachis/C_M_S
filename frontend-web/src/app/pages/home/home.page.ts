import { Component, OnInit, AfterViewInit } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-home',
  templateUrl: './home.page.html',
  styleUrls: ['./home.page.scss'],
  standalone: false,
})
export class HomePage implements OnInit, AfterViewInit {
  selectedGateway = 'consultation';
  bookingDate = '2026-07-23';
  bookingHour = '10 AM';
  bookingMinute = '00';

  isTimePickerOpen = false;

  availableHours = ['10 AM', '11 AM', '12 PM', '1 PM', '2 PM', '3 PM', '4 PM', '5 PM', '6 PM'];
  availableMinutes = ['00', '15', '30', '45'];

  constructor(private router: Router) { }

  ngOnInit() {
  }

  toggleTimePicker() {
    this.isTimePickerOpen = !this.isTimePickerOpen;
  }

  selectHour(h: string) {
    this.bookingHour = h;
  }

  selectMinute(m: string) {
    this.bookingMinute = m;
  }

  ngAfterViewInit() {
    this.initScrollReveal();
  }

  initScrollReveal() {
    if (typeof window === 'undefined' || !('IntersectionObserver' in window)) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
          }
        });
      },
      {
        threshold: 0.1,
        rootMargin: '0px 0px -40px 0px',
      }
    );

    setTimeout(() => {
      const revealElements = document.querySelectorAll('.reveal-on-scroll');
      revealElements.forEach((el) => observer.observe(el));
    }, 100);
  }

  scrollToSection(sectionId: string) {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  navigateToPortal() {
    if (this.selectedGateway === 'administration') {
      this.router.navigate(['/administration']);
    } else {
      this.router.navigate(['/patient']);
    }
  }
}
