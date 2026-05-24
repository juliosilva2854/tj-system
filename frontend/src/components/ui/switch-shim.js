// Mini shim para alinhar com o componente Switch do shadcn (caso nao exista)
import React from 'react';
export const Toggle3D = ({ checked, onChange }) => (
  <input type="checkbox" checked={!!checked} onChange={(e) => onChange?.(e.target.checked)} className="h-4 w-4" />
);
