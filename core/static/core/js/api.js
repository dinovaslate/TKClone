const getCSRFToken = () => {
  const name = 'csrftoken=';
  const decodedCookie = decodeURIComponent(document.cookie || '');
  const parts = decodedCookie.split(';');
  for (let i = 0; i < parts.length; i += 1) {
    let c = parts[i];
    while (c.charAt(0) === ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) === 0) {
      return c.substring(name.length, c.length);
    }
  }
  return '';
};

export const csrfFetch = async (url, options = {}) => {
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  if (options.method && options.method.toUpperCase() !== 'GET') {
    headers.set('X-CSRFToken', getCSRFToken());
  }
  const config = {
    credentials: 'same-origin',
    ...options,
    headers,
  };

  const response = await fetch(url, config);
  const contentType = response.headers.get('content-type');
  let payload = null;
  if (contentType && contentType.includes('application/json')) {
    payload = await response.json();
  }
  if (!response.ok) {
    const error = new Error('Request failed');
    error.response = response;
    error.data = payload;
    throw error;
  }
  return payload;
};

export const debounce = (fn, wait = 300) => {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn.apply(null, args), wait);
  };
};

export const formatCurrency = (value) => {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
  }).format(value);
};

export const formatDate = (dateString) => {
  const options = { day: '2-digit', month: 'short', year: 'numeric' };
  return new Intl.DateTimeFormat('en-GB', options).format(new Date(dateString));
};

export const formatDateTime = (dateString, timeString) => {
  const [hour, minute] = timeString.split(':');
  const date = new Date(dateString);
  date.setHours(parseInt(hour, 10), parseInt(minute, 10), 0, 0);
  const options = { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Intl.DateTimeFormat('en-GB', options).format(date);
};
