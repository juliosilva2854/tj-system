import React, { useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from 'sonner';
import { authAPI } from './api';
import { LoginPage } from './components/LoginPage';
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

const seedDB = async () => { try { await authAPI.seed(); } catch {} };

function App() {
  useEffect(() => { seedDB(); }, []);
  return (
    <div className="App">
      <Toaster position="top-right" richColors />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/dashboard" element={<DashboardLayout />}>
            <Route index element={<DashboardHome />} />
            <Route path="products" element={<ProductsPage />} />
            <Route path="warehouses" element={<WarehousesPage />} />
            <Route path="inventory" element={<InventoryPage />} />
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
