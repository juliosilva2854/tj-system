import axios from 'axios';
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const api = axios.create({ 
  baseURL: `${BACKEND_URL}/api`,
  withCredentials: true // IMPORTANTE: Envia cookies httpOnly automaticamente
});

// Interceptor: Cookies são enviados automaticamente, não precisa de Authorization header
api.interceptors.request.use((config) => {
  // Cookies httpOnly vêm automaticamente pelo navegador
  return config;
}, (error) => {
  console.error('Request error:', error);
  return Promise.reject(error);
});

api.interceptors.response.use((r) => r, (error) => {
  if (error.response?.status === 401) {
    console.warn('Authentication failed (401). Redirecting to login...');
    sessionStorage.removeItem('user');
    if (!window.location.pathname.startsWith('/login')) window.location.href = '/login';
  }
  return Promise.reject(error);
});

export const authAPI = {
  login: (c) => api.post('/auth/login', c),
  logout: () => api.post('/auth/logout'),
  register: (d) => api.post('/auth/register', d),
  me: () => api.get('/auth/me'),
  seed: () => api.post('/seed'),
  forgotPassword: (identifier) => api.post('/auth/forgot-password', { identifier }),
  resetPassword: (token, new_password) => api.post('/auth/reset-password', { token, new_password }),
  getProfile: () => api.get('/auth/profile'),
  updateProfile: (data) => api.put('/auth/profile', data),
  changePassword: (current_password, new_password) => api.put('/auth/change-password', { current_password, new_password }),
  uploadProfilePicture: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/auth/profile/picture', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  deleteProfilePicture: () => api.delete('/auth/profile/picture'),
};
export const tenantsAPI = {
  getAll: () => api.get('/tenants'),
  create: (d) => api.post('/tenants', d),
  update: (id, d) => api.patch(`/tenants/${id}`, d),
  delete: (id) => api.delete(`/tenants/${id}`),
  createStore: (id, d) => api.post(`/tenants/${id}/stores`, d),
};
export const storesAPI = {
  getAll: () => api.get('/stores'),
  create: (d) => api.post('/stores', d),
  update: (id, d) => api.patch(`/stores/${id}`, d),
  delete: (id) => api.delete(`/stores/${id}`),
};
export const transfersAPI = {
  getAll: () => api.get('/transfers'),
  get: (id) => api.get(`/transfers/${id}`),
  create: (d) => api.post('/transfers', d),
};
export const modulesAPI = {
  list: () => api.get('/modules'),
  me: () => api.get('/modules/me'),
  getWarehouse: (wid) => api.get(`/warehouses/${wid}/modules`),
  updateWarehouse: (wid, modules) => api.put(`/warehouses/${wid}/modules`, { enabled_modules: modules }),
};
export const usersAPI = {
  getAll: () => api.get('/users'),
  update: (id, d) => api.patch(`/users/${id}`, d),
  delete: (id) => api.delete(`/users/${id}`),
};
export const warehousesAPI = {
  getAll: () => api.get('/warehouses'),
  create: (d) => api.post('/warehouses', d),
  update: (id, d) => api.patch(`/warehouses/${id}`, d),
  delete: (id) => api.delete(`/warehouses/${id}`),
};
export const suppliersAPI = {
  getAll: () => api.get('/suppliers'),
  create: (d) => api.post('/suppliers', d),
  update: (id, d) => api.patch(`/suppliers/${id}`, d),
  delete: (id) => api.delete(`/suppliers/${id}`),
};
export const productsAPI = {
  getAll: () => api.get('/products'),
  create: (d) => api.post('/products', d),
  update: (id, d) => api.patch(`/products/${id}`, d),
  transfer: (id, warehouseId, qty, sector) => api.post(`/products/${id}/transfer?warehouse_id=${warehouseId}&quantity=${qty}&sector=${encodeURIComponent(sector || '')}`),
};
export const inventoryAPI = {
  getAll: () => api.get('/inventory'),
  adjust: (pid, wid, qty) => api.post(`/inventory/adjust?product_id=${pid}&warehouse_id=${wid}&quantity=${qty}`),
};
export const requisitionsAPI = {
  getAll: () => api.get('/requisitions'),
  create: (d) => api.post('/requisitions', d),
  approve: (id) => api.post(`/requisitions/${id}/approve`),
  reject: (id) => api.post(`/requisitions/${id}/reject`),
};
export const invoicesAPI = {
  getAll: () => api.get('/invoices'),
  create: (d) => api.post('/invoices', d),
  processOCR: (b64) => api.post('/invoices/ocr', { image_base64: b64 }),
  uploadFile: (file) => { const fd = new FormData(); fd.append('file', file); return api.post('/invoices/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } }); },
  processItems: (invoiceId) => api.post(`/invoices/${invoiceId}/process-items`),
};
export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
  getAlerts: () => api.get('/dashboard/alerts'),
};
export const reportsAPI = {
  getFinancial: (p) => api.get(`/reports/financial?period=${p}`),
  exportPDF: (p) => api.get(`/reports/export/pdf?period=${p}`, { responseType: 'blob' }),
  exportExcel: (p) => api.get(`/reports/export/excel?period=${p}`, { responseType: 'blob' }),
  getABCCurve: () => api.get('/reports/abc-curve'),
  getInventoryTurnover: () => api.get('/reports/inventory-turnover'),
};
export const auditAPI = {
  getLogs: () => api.get('/audit'),
  exportExcel: () => api.get('/audit/export', { responseType: 'blob' }),
};
export const notificationsAPI = {
  getAll: () => api.get('/notifications'),
  getUnreadCount: () => api.get('/notifications/unread-count'),
  markRead: (id) => api.patch(`/notifications/${id}/read`),
  markAllRead: () => api.post('/notifications/read-all'),
  getPreferences: () => api.get('/notifications/preferences'),
  updatePreferences: (preferences) => api.put('/notifications/preferences', { preferences }),
};

export const getSubdomain = () => {
  const host = window.location.hostname;
  // Reads first label only when host has multiple labels (e.g., master.sconnecta.com.br)
  const parts = host.split('.');
  if (parts.length < 3) return null;
  return parts[0];
};

export const isMasterSubdomain = () => {
  const hostname = window.location.hostname;
  // administrator.* ou master.* = master access
  return hostname.startsWith('administrator.') || hostname.startsWith('master.');
};

export default api;
