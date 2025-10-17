import { csrfFetch, formatCurrency } from './api.js';
import { showToast } from './toasts.js';
import { toggleLoading } from './ui.js';

const state = {
  selectedCourt: null,
  selectedDate: null,
  selectedSlot: null,
};

const buildSlotTemplate = (slot) => {
  const statusClass = `slot-${slot.status}`;
  const disabled = slot.disabled ? 'aria-disabled="true"' : '';
  return `
    <button
      type="button"
      class="slot ${statusClass}"
      data-start="${slot.start_time}"
      data-end="${slot.end_time}"
      data-price="${slot.price}"
      data-display-date="${slot.displayDate}"
      ${slot.disabled ? 'disabled' : ''}
      ${disabled}
    >
      ${slot.label}
    </button>
  `;
};

const renderSlots = (container, slots) => {
  container.innerHTML = slots.map(buildSlotTemplate).join('');
};

const openModal = (courtId, date, slot) => {
  const modal = document.getElementById('booking-modal');
  if (!modal) return;
  state.selectedCourt = courtId;
  state.selectedDate = date;
  state.selectedSlot = slot;
  modal.querySelector('[data-modal-date]').textContent = slot.displayDate;
  modal.querySelector('[data-modal-time]').textContent = `${slot.start_time} - ${slot.end_time}`;
  modal.querySelector('[data-modal-price]').textContent = formatCurrency(slot.price);
  modal.classList.add('open');
  modal.setAttribute('aria-hidden', 'false');
};

const closeModal = () => {
  const modal = document.getElementById('booking-modal');
  if (!modal) return;
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden', 'true');
};

const attachSlotListeners = (container, courtId, date) => {
  container.addEventListener('click', (event) => {
    const slotButton = event.target.closest('.slot');
    if (!slotButton || slotButton.disabled) return;
    const slot = {
      start_time: slotButton.dataset.start,
      end_time: slotButton.dataset.end,
      label: slotButton.textContent,
      price: parseFloat(slotButton.dataset.price || '0'),
      displayDate: slotButton.dataset.displayDate,
    };
    openModal(courtId, date, slot);
  });
};

const initModal = () => {
  const modal = document.getElementById('booking-modal');
  if (!modal) return;
  const closeBtn = modal.querySelector('[data-modal-close]');
  closeBtn?.addEventListener('click', closeModal);
  modal.addEventListener('click', (event) => {
    if (event.target === modal) {
      closeModal();
    }
  });

  const form = modal.querySelector('form');
  form?.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!state.selectedCourt || !state.selectedSlot) return;
    const stopLoading = toggleLoading(form.querySelector('button[type="submit"]'), 'Creating...');
    try {
      const payload = await csrfFetch('/api/bookings', {
        method: 'POST',
        body: JSON.stringify({
          court_id: state.selectedCourt,
          date: state.selectedDate,
          start_time: state.selectedSlot.start_time,
          end_time: state.selectedSlot.end_time,
        }),
      });
      showToast({
        message: payload.data.message,
        variant: 'success',
      });
      document.dispatchEvent(new CustomEvent('booking:created', { detail: payload.data.booking }));
      closeModal();
    } catch (error) {
      const message = error?.data?.errors?.join('<br>') || 'Unable to create booking';
      showToast({ message, variant: 'error', duration: null });
    } finally {
      stopLoading();
    }
  });
};

export const loadAvailability = async (container, courtId, date) => {
  const pillContainer = document.querySelector('[data-availability-dates]');
  if (pillContainer) {
    pillContainer.querySelectorAll('.pill').forEach((pill) => {
      pill.classList.toggle('active', pill.dataset.date === date);
    });
  }
  state.selectedCourt = courtId;
  state.selectedDate = date;
  container.innerHTML = '<div class="slot-grid-loading">Loading...</div>';
  try {
    const payload = await csrfFetch(`/api/availability?court_id=${courtId}&date=${date}`);
    renderSlots(container, payload.data.slots);
  } catch (error) {
    container.innerHTML = '<p class="error-text">Unable to load availability right now.</p>';
  }
};

export const initAvailability = () => {
  const container = document.querySelector('[data-availability-slots]');
  const dateContainer = document.querySelector('[data-availability-dates]');
  if (!container || !dateContainer) return;

  const { courtId } = container.dataset;
  const defaultDate = dateContainer.querySelector('.pill.active')?.dataset.date;
  attachSlotListeners(container, parseInt(courtId, 10), defaultDate);
  dateContainer.addEventListener('click', (event) => {
    const pill = event.target.closest('.pill');
    if (!pill) return;
    loadAvailability(container, courtId, pill.dataset.date);
  });

  initModal();

  if (defaultDate) {
    loadAvailability(container, courtId, defaultDate);
  }
};

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    closeModal();
  }
});

export const closeBookingModal = closeModal;
