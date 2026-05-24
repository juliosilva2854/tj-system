import React from 'react';
import { MasterDashboardPage } from './MasterDashboardPage';
import { NormalDashboardHome } from './NormalDashboardHome';

const getCurrentUser = () => { 
  try { 
    return JSON.parse(localStorage.getItem('user') || '{}'); 
  } catch { 
    return {}; 
  } 
};

export const DashboardHome = () => {
  const me = getCurrentUser();
  const isMaster = me.role === 'master' || me.is_master_access;

  // Se for master, mostra dashboard master
  if (isMaster) {
    return <MasterDashboardPage />;
  }

  // Senão, mostra dashboard normal
  return <NormalDashboardHome />;
};
