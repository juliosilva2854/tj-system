import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

def send_email(to: str, subject: str, html_content: str) -> bool:
    """Envia email usando Gmail SMTP"""
    smtp_user = os.environ.get('SMTP_USER')
    smtp_password = os.environ.get('SMTP_PASSWORD')
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    
    if not smtp_user or not smtp_password:
        logger.warning("Gmail SMTP not configured (SMTP_USER or SMTP_PASSWORD missing). Email not sent.")
        return False
    
    try:
        # Criar mensagem
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = smtp_user
        message['To'] = to
        
        # Adicionar conteúdo HTML
        html_part = MIMEText(html_content, 'html', 'utf-8')
        message.attach(html_part)
        
        # Conectar ao servidor SMTP e enviar
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(message)
        
        logger.info(f"Email sent successfully to {to}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return False


def build_stock_alert_email(product_name: str, warehouse_name: str, current_qty: float, min_stock: float) -> tuple:
    subject = f"[Gestao TJ] Alerta de Estoque Baixo - {product_name}"
    html = f"""
    <div style="font-family: 'IBM Plex Sans', Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #E4E4E7; border-radius: 12px; overflow: hidden;">
      <div style="background: #2563EB; color: white; padding: 20px 24px;">
        <h1 style="margin: 0; font-size: 20px;">Gestao TJ - Alerta de Estoque</h1>
      </div>
      <div style="padding: 24px;">
        <p style="color: #DC2626; font-weight: 600; font-size: 16px;">Estoque Baixo Detectado</p>
        <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
          <tr><td style="padding: 8px 0; color: #71717A;">Produto:</td><td style="padding: 8px 0; font-weight: 600;">{product_name}</td></tr>
          <tr><td style="padding: 8px 0; color: #71717A;">Deposito:</td><td style="padding: 8px 0;">{warehouse_name}</td></tr>
          <tr><td style="padding: 8px 0; color: #71717A;">Quantidade Atual:</td><td style="padding: 8px 0; color: #DC2626; font-weight: 600;">{current_qty}</td></tr>
          <tr><td style="padding: 8px 0; color: #71717A;">Estoque Minimo:</td><td style="padding: 8px 0;">{min_stock}</td></tr>
        </table>
        <p style="color: #71717A; font-size: 14px;">Acesse o sistema para reabastecer o estoque.</p>
      </div>
      <div style="background: #FAFAFA; padding: 16px 24px; border-top: 1px solid #E4E4E7; text-align: center;">
        <p style="color: #A1A1AA; font-size: 12px; margin: 0;">Sistema Gestao TJ - Notificacao Automatica</p>
      </div>
    </div>
    """
    return subject, html


def build_invoice_pending_email(invoice_number: str, supplier_name: str, total_value: float) -> tuple:
    subject = f"[Gestao TJ] Nota Fiscal Pendente - {invoice_number}"
    html = f"""
    <div style="font-family: 'IBM Plex Sans', Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #E4E4E7; border-radius: 12px; overflow: hidden;">
      <div style="background: #2563EB; color: white; padding: 20px 24px;">
        <h1 style="margin: 0; font-size: 20px;">Gestao TJ - Nota Fiscal</h1>
      </div>
      <div style="padding: 24px;">
        <p style="color: #EAB308; font-weight: 600; font-size: 16px;">Nota Fiscal Pendente</p>
        <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
          <tr><td style="padding: 8px 0; color: #71717A;">Numero:</td><td style="padding: 8px 0; font-weight: 600;">{invoice_number}</td></tr>
          <tr><td style="padding: 8px 0; color: #71717A;">Fornecedor:</td><td style="padding: 8px 0;">{supplier_name}</td></tr>
          <tr><td style="padding: 8px 0; color: #71717A;">Valor:</td><td style="padding: 8px 0; font-weight: 600;">R$ {total_value:.2f}</td></tr>
        </table>
      </div>
      <div style="background: #FAFAFA; padding: 16px 24px; border-top: 1px solid #E4E4E7; text-align: center;">
        <p style="color: #A1A1AA; font-size: 12px; margin: 0;">Sistema Gestao TJ - Notificacao Automatica</p>
      </div>
    </div>
    """
    return subject, html


def build_sale_completed_email(sale_number: str, total: float, customer_name: str) -> tuple:
    subject = f"[Gestao TJ] Venda Concluida - {sale_number}"
    html = f"""
    <div style="font-family: 'IBM Plex Sans', Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #E4E4E7; border-radius: 12px; overflow: hidden;">
      <div style="background: #2563EB; color: white; padding: 20px 24px;">
        <h1 style="margin: 0; font-size: 20px;">Gestao TJ - Venda</h1>
      </div>
      <div style="padding: 24px;">
        <p style="color: #16A34A; font-weight: 600; font-size: 16px;">Venda Concluida com Sucesso</p>
        <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
          <tr><td style="padding: 8px 0; color: #71717A;">Numero:</td><td style="padding: 8px 0; font-weight: 600;">{sale_number}</td></tr>
          <tr><td style="padding: 8px 0; color: #71717A;">Cliente:</td><td style="padding: 8px 0;">{customer_name or 'Nao informado'}</td></tr>
          <tr><td style="padding: 8px 0; color: #71717A;">Total:</td><td style="padding: 8px 0; font-weight: 600; color: #16A34A;">R$ {total:.2f}</td></tr>
        </table>
      </div>
      <div style="background: #FAFAFA; padding: 16px 24px; border-top: 1px solid #E4E4E7; text-align: center;">
        <p style="color: #A1A1AA; font-size: 12px; margin: 0;">Sistema Gestao TJ - Notificacao Automatica</p>
      </div>
    </div>
    """
    return subject, html



def build_password_reset_email(reset_url: str, user_name: str) -> tuple:
    """Template de email para recuperação de senha"""
    subject = "[Gestao TJ] Recuperação de Senha"
    html = f"""
    <div style="font-family: 'IBM Plex Sans', Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #E4E4E7; border-radius: 12px; overflow: hidden;">
      <div style="background: #2563EB; color: white; padding: 20px 24px;">
        <h1 style="margin: 0; font-size: 20px;">Gestao TJ - Recuperação de Senha</h1>
      </div>
      <div style="padding: 24px;">
        <p style="font-size: 16px;">Olá, <strong>{user_name}</strong>!</p>
        <p style="color: #71717A; font-size: 14px;">Recebemos uma solicitação para redefinir a senha da sua conta.</p>
        <p style="color: #71717A; font-size: 14px;">Clique no botão abaixo para criar uma nova senha:</p>
        <div style="text-align: center; margin: 24px 0;">
          <a href="{reset_url}" style="display: inline-block; background: #2563EB; color: white; padding: 12px 32px; text-decoration: none; border-radius: 8px; font-weight: 600;">Redefinir Senha</a>
        </div>
        <p style="color: #71717A; font-size: 13px;">Ou copie e cole o link abaixo no seu navegador:</p>
        <p style="color: #2563EB; font-size: 13px; word-break: break-all;">{reset_url}</p>
        <div style="background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 12px; margin: 16px 0; border-radius: 4px;">
          <p style="margin: 0; color: #92400E; font-size: 13px;">⚠️ Este link expira em 1 hora. Se você não solicitou esta recuperação, ignore este email.</p>
        </div>
      </div>
      <div style="background: #FAFAFA; padding: 16px 24px; border-top: 1px solid #E4E4E7; text-align: center;">
        <p style="color: #A1A1AA; font-size: 12px; margin: 0;">Sistema Gestao TJ - Notificação Automática</p>
      </div>
    </div>
    """
    return subject, html
