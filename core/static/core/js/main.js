import { csrfFetch, debounce, formatCurrency, formatDateTime } from './api.js';
import { renderCourtCard, renderSkeletonCard, toggleLoading } from './ui.js';
import { initAvailability, loadAvailability } from './availability.js';
import { showToast } from './toasts.js';

const courtsGrid = document.querySelector('[data-courts-grid]');
const searchForm = document.querySelector('[data-search-form]');
const searchInputs = document.querySelectorAll('[data-search-input]');

const renderCourts = (courts) => {
  if (!courtsGrid) return;
  courtsGrid.innerHTML = courts.map(renderCourtCard).join('');
  courtsGrid.querySelectorAll('.check-availability').forEach((button) => {
    button.addEventListener('click', (event) => {
      const card = event.target.closest('[data-court-id]');
      const courtId = card.dataset.courtId;
      window.location.href = `/courts/${courtId}/`;
    });
  });
};

const renderSkeletons = () => {
  if (!courtsGrid) return;
  courtsGrid.innerHTML = new Array(6).fill(null).map(renderSkeletonCard).join('');
};

const fetchCourts = debounce(async () => {
  if (!courtsGrid || !searchForm) return;
  const params = new URLSearchParams(new FormData(searchForm));
  renderSkeletons();
  try {
    const payload = await csrfFetch(`/api/courts?${params.toString()}`);
    renderCourts(payload.data.results);
  } catch (error) {
    courtsGrid.innerHTML = '<p class="error-text">Unable to load courts right now.</p>';
  }
}, 400);

searchInputs.forEach((input) => {
  input.addEventListener('input', fetchCourts);
});

if (searchForm) {
  searchForm.addEventListener('submit', (event) => {
    event.preventDefault();
    fetchCourts();
  });
}

const bookingsList = document.querySelector('[data-bookings-list]');

const renderBooking = (booking) => {
  const statusClass = `status-${booking.status.toLowerCase()}`;
  const paymentClass = `status-${booking.payment_status.toLowerCase()}`;
  const formattedDate = formatDateTime(booking.date, booking.start_time);
  const price = formatCurrency(booking.total_price);
  return `
    <article class="booking-card glass" data-booking-id="${booking.id}">
      <header>
        <h3>${booking.court_name}</h3>
        <span class="chip ${statusClass}">${booking.status}</span>
      </header>
      <p class="booking-date">${formattedDate} - ${booking.end_time}</p>
      <p class="booking-total">${price}</p>
      <footer>
        <span class="chip ${paymentClass}">${booking.payment_status}</span>
        <div class="booking-actions">
          ${booking.status === 'PENDING' ? '<button class="btn-primary" data-action="confirm">Confirm & Pay</button>' : ''}
          ${booking.status !== 'CANCELED' ? '<button class="btn-ghost" data-action="cancel">Cancel</button>' : ''}
        </div>
      </footer>
    </article>
  `;
};

const loadBookings = async () => {
  if (!bookingsList) return;
  bookingsList.innerHTML = '<p class="muted">Loading...</p>';
  try {
    const payload = await csrfFetch('/api/bookings/mine');
    if (payload.data.results.length === 0) {
      bookingsList.innerHTML = '<div class="empty-state glass"><p>No bookings yet.</p></div>';
      return;
    }
    bookingsList.innerHTML = payload.data.results.map(renderBooking).join('');
  } catch (error) {
    bookingsList.innerHTML = '<p class="error-text">Unable to load bookings.</p>';
  }
};

bookingsList?.addEventListener('click', async (event) => {
  const button = event.target.closest('button[data-action]');
  if (!button) return;
  const card = button.closest('[data-booking-id]');
  const { bookingId } = card.dataset;
  const action = button.dataset.action;
  const stopLoading = toggleLoading(button, action === 'confirm' ? 'Confirming...' : 'Canceling...');
  try {
    const payload = await csrfFetch(`/api/bookings/${bookingId}/${action}`, { method: 'POST' });
    const toastConfig = { message: payload.data.message, variant: 'success' };
    if (payload.data.receipt_url) {
      toastConfig.action = {
        label: 'View receipt',
        handler: () => {
          window.location.href = payload.data.receipt_url;
        },
      };
    }
    if (action === 'cancel') {
      toastConfig.duration = 8000;
      toastConfig.action = {
        label: 'Undo',
        handler: async () => {
          try {
            await csrfFetch(`/api/bookings/${bookingId}/cancel`, {
              method: 'POST',
              body: JSON.stringify({ undo: true }),
            });
            loadBookings();
            showToast({ message: 'Booking restored.', variant: 'success' });
          } catch (undoError) {
            showToast({ message: 'Unable to undo cancellation.', variant: 'error', duration: null });
          }
        },
      };
    }
    showToast(toastConfig);
    loadBookings();
  } catch (error) {
    const message = error?.data?.errors?.join('<br>') || 'Unable to process request';
    showToast({ message, variant: 'error', duration: null });
  } finally {
    stopLoading();
  }
});

if (bookingsList) {
  loadBookings();
}

document.addEventListener('booking:created', loadBookings);

const favoritesToggle = document.querySelectorAll('[data-favorite-toggle]');

favoritesToggle.forEach((button) => {
  button.addEventListener('click', async () => {
    const courtId = button.dataset.courtId;
    const stopLoading = toggleLoading(button, 'Saving...');
    let isFavorite;
    try {
      const payload = await csrfFetch('/api/favorites/toggle', {
        method: 'POST',
        body: JSON.stringify({ court_id: courtId }),
      });
      showToast({ message: payload.data.message, variant: 'success' });
      isFavorite = payload.data.is_favorite;
      button.classList.toggle('active', isFavorite);
    } catch (error) {
      showToast({ message: 'Unable to update favorite', variant: 'error' });
    } finally {
      stopLoading();
      if (typeof isFavorite === 'boolean') {
        button.textContent = isFavorite ? '★ Favorite' : '☆ Favorite';
      }
    }
  });
});

initAvailability();

window.addEventListener('DOMContentLoaded', () => {
  const quickSearch = document.querySelector('[data-quick-search]');
  if (quickSearch) {
    quickSearch.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        const target = document.querySelector(quickSearch.dataset.target);
        target?.focus();
      }
    });
  }
});
