import React, { useState, useEffect } from 'react';
import { authAPI } from '../api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { toast } from 'sonner';
import { User, Mail, Phone, CreditCard, Camera, Lock, Save, Trash2 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const ProfilePage = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // Profile data
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  
  // Password change
  const [showPasswordSection, setShowPasswordSection] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  // Photo upload
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [photoPreview, setPhotoPreview] = useState(null);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const response = await authAPI.getProfile();
      const profileData = response.data;
      setUser(profileData);
      setName(profileData.name || '');
      setPhone(profileData.phone || '');
      if (profileData.profile_picture) {
        setPhotoPreview(`${BACKEND_URL}/api/uploads/profiles/${profileData.profile_picture}`);
      }
    } catch (error) {
      toast.error('Erro ao carregar perfil');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await authAPI.updateProfile({ name, phone });
      toast.success('Perfil atualizado com sucesso!');
      loadProfile();
    } catch (error) {
      toast.error('Erro ao atualizar perfil');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    
    if (newPassword.length < 6) {
      toast.error('Nova senha deve ter no mínimo 6 caracteres');
      return;
    }
    
    if (newPassword !== confirmPassword) {
      toast.error('As senhas não coincidem');
      return;
    }

    setSaving(true);
    try {
      await authAPI.changePassword(currentPassword, newPassword);
      toast.success('Senha alterada com sucesso!');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setShowPasswordSection(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao alterar senha');
    } finally {
      setSaving(false);
    }
  };

  const handlePhotoChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validações
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      toast.error('Formato inválido. Use JPG, PNG ou WEBP');
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      toast.error('Arquivo muito grande. Máximo 2MB');
      return;
    }

    setUploadingPhoto(true);
    try {
      const response = await authAPI.uploadProfilePicture(file);
      toast.success('Foto atualizada com sucesso!');
      setPhotoPreview(`${BACKEND_URL}/api${response.data.url}`);
      loadProfile();
    } catch (error) {
      toast.error('Erro ao fazer upload da foto');
    } finally {
      setUploadingPhoto(false);
    }
  };

  const handleDeletePhoto = async () => {
    if (!window.confirm('Deseja remover sua foto de perfil?')) return;

    setUploadingPhoto(true);
    try {
      await authAPI.deleteProfilePicture();
      toast.success('Foto removida com sucesso!');
      setPhotoPreview(null);
      loadProfile();
    } catch (error) {
      toast.error('Erro ao remover foto');
    } finally {
      setUploadingPhoto(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900">Meu Perfil</h1>
        <p className="text-sm text-zinc-600 mt-1">Gerencie suas informações pessoais e configurações de conta</p>
      </div>

      {/* Photo Section */}
      <div className="bg-white rounded-xl border border-zinc-200 p-6">
        <h2 className="text-lg font-semibold text-zinc-900 mb-4">Foto de Perfil</h2>
        <div className="flex items-center gap-6">
          <div className="relative">
            {photoPreview ? (
              <img
                src={photoPreview}
                alt="Profile"
                className="h-24 w-24 rounded-full object-cover border-4 border-zinc-100"
              />
            ) : (
              <div className="h-24 w-24 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white text-3xl font-bold">
                {user?.name?.charAt(0).toUpperCase() || 'U'}
              </div>
            )}
            {uploadingPhoto && (
              <div className="absolute inset-0 bg-black/50 rounded-full flex items-center justify-center">
                <div className="animate-spin h-6 w-6 border-2 border-white border-t-transparent rounded-full"></div>
              </div>
            )}
          </div>
          
          <div className="flex-1">
            <p className="text-sm text-zinc-600 mb-3">
              JPG, PNG ou WEBP. Tamanho máximo: 2MB
            </p>
            <div className="flex gap-2">
              <label>
                <Button
                  type="button"
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                  disabled={uploadingPhoto}
                  onClick={() => document.getElementById('photo-input').click()}
                >
                  <Camera className="h-4 w-4 mr-2" />
                  {photoPreview ? 'Alterar Foto' : 'Adicionar Foto'}
                </Button>
                <input
                  id="photo-input"
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={handlePhotoChange}
                />
              </label>
              
              {photoPreview && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleDeletePhoto}
                  disabled={uploadingPhoto}
                  className="text-red-600 border-red-200 hover:bg-red-50"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Remover
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Personal Info Section */}
      <div className="bg-white rounded-xl border border-zinc-200 p-6">
        <h2 className="text-lg font-semibold text-zinc-900 mb-4">Informações Pessoais</h2>
        <form onSubmit={handleSaveProfile} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-1.5">
                <User className="h-4 w-4 inline mr-1" />
                Nome Completo
              </label>
              <Input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                placeholder="Seu nome completo"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-1.5">
                <Phone className="h-4 w-4 inline mr-1" />
                Telefone
              </label>
              <Input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="(11) 99999-9999"
              />
            </div>
          </div>

          {/* Read-only fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-1.5">
                <Mail className="h-4 w-4 inline mr-1" />
                Email
              </label>
              <Input
                type="email"
                value={user?.email || ''}
                disabled
                className="bg-zinc-50"
              />
              <p className="text-xs text-zinc-500 mt-1">Email não pode ser alterado</p>
            </div>

            {user?.username && (
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">
                  <User className="h-4 w-4 inline mr-1" />
                  Usuário
                </label>
                <Input
                  type="text"
                  value={user.username}
                  disabled
                  className="bg-zinc-50 font-mono"
                />
                <p className="text-xs text-zinc-500 mt-1">Usuário não pode ser alterado</p>
              </div>
            )}

            {user?.cpf && (
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">
                  <CreditCard className="h-4 w-4 inline mr-1" />
                  CPF
                </label>
                <Input
                  type="text"
                  value={user.cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4')}
                  disabled
                  className="bg-zinc-50 font-mono"
                />
              </div>
            )}
          </div>

          <div className="flex justify-end pt-2">
            <Button
              type="submit"
              disabled={saving}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              {saving ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                  Salvando...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Salvar Alterações
                </>
              )}
            </Button>
          </div>
        </form>
      </div>

      {/* Security Section */}
      <div className="bg-white rounded-xl border border-zinc-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-zinc-900">Segurança</h2>
            <p className="text-sm text-zinc-600 mt-1">Altere sua senha de acesso</p>
          </div>
          {!showPasswordSection && (
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowPasswordSection(true)}
              className="border-zinc-300"
            >
              <Lock className="h-4 w-4 mr-2" />
              Alterar Senha
            </Button>
          )}
        </div>

        {showPasswordSection && (
          <form onSubmit={handleChangePassword} className="space-y-4 mt-4 pt-4 border-t">
            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-1.5">
                Senha Atual
              </label>
              <Input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
                placeholder="Digite sua senha atual"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">
                  Nova Senha
                </label>
                <Input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  placeholder="Mínimo 6 caracteres"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">
                  Confirmar Nova Senha
                </label>
                <Input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  placeholder="Digite novamente"
                />
              </div>
            </div>

            <div className="flex gap-2 justify-end pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowPasswordSection(false);
                  setCurrentPassword('');
                  setNewPassword('');
                  setConfirmPassword('');
                }}
                className="border-zinc-300"
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={saving}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                {saving ? 'Alterando...' : 'Alterar Senha'}
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
