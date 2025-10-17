export const renderSkeletonCard = () => {
  return `
    <article class="court-card glass skeleton">
      <div class="court-image" aria-hidden="true"></div>
      <div class="skeleton-line" style="width: 60%"></div>
      <div class="skeleton-line" style="width: 40%"></div>
    </article>
  `;
};

export const renderCourtCard = (court) => {
  const price = new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
  }).format(court.price_per_hour);
  return `
    <article class="court-card glass" data-court-id="${court.id}">
      <img src="${court.image}" alt="${court.name}" class="court-image" loading="lazy" />
      <div class="court-card-body">
        <h3>${court.name}</h3>
        <p class="court-location">${court.location}</p>
        <p class="court-price">${price} / hour</p>
        <button class="btn-primary check-availability" type="button">Check Availability</button>
      </div>
    </article>
  `;
};

export const renderAvailabilitySkeleton = (count = 6) => {
  return new Array(count)
    .fill(null)
    .map(
      () => `
        <div class="slot skeleton" aria-hidden="true"></div>
      `,
    )
    .join('');
};

export const toggleLoading = (element, loadingText = 'Loading...') => {
  if (!element) return () => {};
  const original = element.innerHTML;
  const originalDisabled = element.disabled;
  element.innerHTML = `<span class="spinner"></span>${loadingText}`;
  element.disabled = true;
  return () => {
    element.innerHTML = original;
    element.disabled = originalDisabled;
  };
};
