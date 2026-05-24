#!/bin/bash
###############################################################################
# Script de Instalação Rápida - Gestão TJ
# Detecta o ambiente e executa a instalação apropriada
###############################################################################

set -e  # Exit on error

echo "========================================="
echo "  🚀 Gestão TJ - Instalação Rápida"
echo "========================================="
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funções auxiliares
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Detecta sistema operacional
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "mac"
    else
        echo "unknown"
    fi
}

# Verifica se comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verifica Docker
check_docker() {
    echo "Verificando Docker..."
    if command_exists docker && command_exists docker-compose; then
        print_success "Docker encontrado!"
        return 0
    else
        print_warning "Docker não encontrado"
        return 1
    fi
}

# Instalação com Docker
install_with_docker() {
    echo ""
    echo "========================================="
    echo "  🐳 Instalação com Docker"
    echo "========================================="
    
    # Verifica se .env existe
    if [ ! -f .env ]; then
        print_warning ".env não encontrado. Criando a partir do exemplo..."
        cp .env.example .env
        
        # Gera JWT_SECRET
        if command_exists openssl; then
            JWT_SECRET=$(openssl rand -hex 32)
            sed -i.bak "s/seu-secret-super-seguro-mude-em-producao/$JWT_SECRET/" .env
            print_success "JWT_SECRET gerado automaticamente"
        fi
        
        echo ""
        print_warning "ATENÇÃO: Configure as credenciais de email no arquivo .env!"
        echo "Edite o arquivo .env e adicione:"
        echo "  SMTP_USER=seu-email@gmail.com"
        echo "  SMTP_PASSWORD=sua-senha-de-app-16-chars"
        echo ""
        read -p "Pressione ENTER após configurar o .env..."
    fi
    
    # Build e start
    echo ""
    echo "Iniciando containers..."
    docker-compose up --build -d
    
    echo ""
    echo "Aguardando serviços iniciarem..."
    sleep 15
    
    # Verifica saúde
    echo "Verificando saúde dos serviços..."
    if docker-compose ps | grep -q "Up"; then
        print_success "Containers estão rodando!"
    else
        print_error "Alguns containers falharam. Verifique com: docker-compose logs"
        exit 1
    fi
    
    # Seed database
    echo ""
    echo "Inicializando banco de dados..."
    sleep 10
    if curl -s -X POST http://localhost:8001/api/seed | grep -q "inicializado"; then
        print_success "Banco de dados inicializado!"
    else
        print_warning "Falha ao inicializar banco. Execute manualmente: curl -X POST http://localhost:8001/api/seed"
    fi
    
    echo ""
    print_success "========================================="
    print_success "  ✅ Instalação concluída!"
    print_success "========================================="
    echo ""
    echo "Acesse:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend:  http://localhost:8001"
    echo "  API Docs: http://localhost:8001/docs"
    echo ""
    echo "Credenciais de teste:"
    echo "  Usuário: admin.tj"
    echo "  Senha:   Admin@2026"
    echo ""
    echo "Para ver logs: docker-compose logs -f"
    echo "Para parar:    docker-compose down"
}

# Instalação local
install_local() {
    echo ""
    echo "========================================="
    echo "  💻 Instalação Local"
    echo "========================================="
    
    OS=$(detect_os)
    
    # Verifica MongoDB
    if ! command_exists mongod; then
        print_error "MongoDB não encontrado!"
        echo "Instale MongoDB:"
        if [ "$OS" = "linux" ]; then
            echo "  Ubuntu: sudo apt-get install mongodb-org"
        elif [ "$OS" = "mac" ]; then
            echo "  macOS: brew install mongodb-community@7.0"
        fi
        exit 1
    fi
    
    # Backend
    echo ""
    echo "Configurando backend..."
    cd backend
    
    if [ ! -f .env ]; then
        cp .env.example .env
        print_warning "Configure backend/.env com suas credenciais!"
        read -p "Pressione ENTER após configurar..."
    fi
    
    # Python venv
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install -q -r requirements.txt
    print_success "Dependências do backend instaladas"
    
    # Frontend
    echo ""
    echo "Configurando frontend..."
    cd ../frontend
    
    if [ ! -f .env ]; then
        cp .env.example .env
    fi
    
    if ! command_exists yarn; then
        npm install -g yarn
    fi
    
    yarn install
    print_success "Dependências do frontend instaladas"
    
    cd ..
    
    echo ""
    print_success "========================================="
    print_success "  ✅ Instalação local concluída!"
    print_success "========================================="
    echo ""
    echo "Para iniciar:"
    echo ""
    echo "Terminal 1 - Backend:"
    echo "  cd backend"
    echo "  source venv/bin/activate"
    echo "  uvicorn server:app --host 0.0.0.0 --port 8001 --reload"
    echo ""
    echo "Terminal 2 - Frontend:"
    echo "  cd frontend"
    echo "  yarn start"
    echo ""
    echo "Terminal 3 - Seed:"
    echo "  curl -X POST http://localhost:8001/api/seed"
}

# Menu principal
main() {
    echo "Escolha o método de instalação:"
    echo ""
    echo "1) Docker (Recomendado - mais rápido)"
    echo "2) Instalação Local (Para desenvolvimento)"
    echo "3) Sair"
    echo ""
    read -p "Opção [1-3]: " choice
    
    case $choice in
        1)
            if check_docker; then
                install_with_docker
            else
                print_error "Docker não está instalado!"
                echo "Instale Docker Desktop: https://www.docker.com/get-started"
                exit 1
            fi
            ;;
        2)
            install_local
            ;;
        3)
            echo "Saindo..."
            exit 0
            ;;
        *)
            print_error "Opção inválida!"
            exit 1
            ;;
    esac
}

# Executa
main
