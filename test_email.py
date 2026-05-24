#!/usr/bin/env python3
"""Script de teste para verificar envio de email"""
import sys
import os
sys.path.insert(0, '/app/backend')

from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

from email_service import send_email, build_password_reset_email

def test_email():
    print("🧪 Testando envio de email via Gmail SMTP...")
    print(f"📧 SMTP User: {os.environ.get('SMTP_USER')}")
    print(f"🔐 SMTP Password: {'*' * len(os.environ.get('SMTP_PASSWORD', ''))}")
    print()
    
    # Construir email de teste
    reset_url = "https://tj.sconnecta.com.br/reset-password?token=abc123"
    subject, html = build_password_reset_email(reset_url, "Teste Usuario")
    
    # Enviar para o próprio email de suporte
    recipient = "suportegestaotj@gmail.com"
    print(f"📤 Enviando email de teste para: {recipient}")
    
    success = send_email(recipient, subject, html)
    
    if success:
        print("✅ Email enviado com sucesso!")
        print(f"📬 Verifique a caixa de entrada de {recipient}")
    else:
        print("❌ Falha ao enviar email. Verifique os logs acima.")
        return False
    
    return True

if __name__ == "__main__":
    success = test_email()
    sys.exit(0 if success else 1)
