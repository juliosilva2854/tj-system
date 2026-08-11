// frontend/src/auth.js - Fonte única de verdade para Sessão e RBAC

export const getUser = () => {
  try {
    // Tenta primeiro o localStorage, depois o sessionStorage como fallback
    const rawData = localStorage.getItem('user') || sessionStorage.getItem('user');
    if (!rawData) return null;
    
    const parsed = JSON.parse(rawData);
    // Trata se o objeto veio encapsulado como { user: { ... } } ou direto { ... }
    const user = parsed.user || parsed;
    return user && Object.keys(user).length > 0 ? user : null;
  } catch (err) {
    console.error('Erro ao ler utilizador da sessão:', err);
    return null;
  }
};

export const setUser = (userData, persist = true) => {
  try {
    const stringified = JSON.stringify(userData);
    if (persist) {
      localStorage.setItem('user', stringified);
      sessionStorage.removeItem('user'); // Evita duplicidade cruzada
    } else {
      sessionStorage.setItem('user', stringified);
      localStorage.removeItem('user');
    }
  } catch (err) {
    console.error('Erro ao guardar utilizador na sessão:', err);
  }
};

export const clearUser = () => {
  localStorage.removeItem('user');
  sessionStorage.removeItem('user');
};

export const hasSession = () => {
  return getUser() !== null;
};

// === HELPERS DE RBAC (Role-Based Access Control) ===

export const getCleanRole = (user) => {
  return String(user?.role || '').toLowerCase().trim();
};

export const isMaster = (user = getUser()) => {
  if (!user) return false;
  const role = getCleanRole(user);
  return role === 'master' || user.is_master_access === true;
};

export const isAdmin = (user = getUser()) => {
  if (!user) return false;
  const role = getCleanRole(user);
  return role === 'admin' || role === 'administrador' || isMaster(user);
};

export const hasRole = (allowedRoles = [], user = getUser()) => {
  if (!user) return false;
  if (isMaster(user)) return true;
  const role = getCleanRole(user);
  return allowedRoles.map(r => r.toLowerCase()).includes(role);
};

export const canViewModules = (user = getUser()) => {
  return isAdmin(user) || hasRole(['gerente_geral', 'gerente_logistica', 'gerente_operacional'], user);
};

export const canManageModules = (user = getUser()) => {
  return isAdmin(user);
};

// Quem pode CRUD produtos/fornecedores/notas (admin, gerentes de logistica/geral, logistica legado)
export const canManageProducts = (user = getUser()) => {
  return isAdmin(user) || hasRole(['gerente_geral', 'gerente_logistica', 'logistica'], user);
};

// Quem pode criar requisicoes (FILHO -> PAI): operacional/gerente_operacional + admin
export const canCreateRequisition = (user = getUser()) => {
  return isAdmin(user) || hasRole(['operacional', 'gerente_operacional'], user);
};

// Quem pode aprovar/rejeitar requisicoes
export const canApproveRequisition = (user = getUser()) => {
  return isAdmin(user) || hasRole(['gerente_geral', 'gerente_logistica', 'logistica'], user);
};

// Quem pode criar transferencias entre lojas (PAI -> PAI)
export const canManageTransfers = (user = getUser()) => {
  return isAdmin(user) || hasRole(['gerente_geral'], user);
};

// Quem pode gerir Lojas/Unidades (criar/editar/excluir): master (role ou is_master_access) ou admin
export const canManageStores = (user = getUser()) => {
  return isMaster(user) || isAdmin(user);
};