import React, { useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from 'sonner';
import { authAPI } from './api';
import { LoginPage } from './components/LoginPage';
import { ForgotPasswordPage } from './components/ForgotPasswordPage';
import { ResetPasswordPage } from './components/ResetPasswordPage';
import { ProfilePage } from './components/ProfilePage';
import { DashboardLayout } from './components/DashboardLayout';
import { DashboardHome } from './components/DashboardHome';
import { ProductsPage } from './components/ProductsPage';
import { InventoryPage } from './components/InventoryPage';
import { SuppliersPage } from './components/SuppliersPage';
import { InvoicesPage } from './components/InvoicesPage';
import { ReportsPage } from './components/ReportsPage';
import { AuditPage } from './components/AuditPage';
import { UsersPage } from './components/UsersPage';
import { WarehousesPage } from './components/WarehousesPage';
import { AlertsPage } from './components/AlertsPage';
import { GuidePage } from './components/GuidePage';
import { TenantsPage } from './components/TenantsPage';
import { RequisitionsPage } from './components/RequisitionsPage';
import { StoresPage } from './components/StoresPage';
import { TransfersPage } from './components/TransfersPage';
import { ModulesPage } from './components/ModulesPage';

const seedDB = async () => { try { await authAPI.seed(); } catch {} };

function App() {
  useEffect(() => { seedDB(); }, []);
  return (
    <div className="App">
      <Toaster position="top-right" richColors />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/dashboard" element={<DashboardLayout />}>
            <Route index element={<DashboardHome />} />
            <Route path="profile" element={<ProfilePage />} />
            <Route path="tenants" element={<TenantsPage />} />
            <Route path="stores" element={<StoresPage />} />
            <Route path="modules" element={<ModulesPage />} />
            <Route path="transfers" element={<TransfersPage />} />
            <Route path="products" element={<ProductsPage />} />
            <Route path="warehouses" element={<WarehousesPage />} />
            <Route path="inventory" element={<InventoryPage />} />
            <Route path="requisitions" element={<RequisitionsPage />} />
            <Route path="suppliers" element={<SuppliersPage />} />
            <Route path="invoices" element={<InvoicesPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="alerts" element={<AlertsPage />} />
            <Route path="audit" element={<AuditPage />} />
            <Route path="users" element={<UsersPage />} />
            <Route path="guide" element={<GuidePage />} />
          </Route>
          <Route path="/" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}
export default App;
