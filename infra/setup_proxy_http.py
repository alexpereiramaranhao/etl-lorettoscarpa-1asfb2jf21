import os
import sys
import subprocess
import json

# --- Configurações ---
CONFIG_FILE = 'proxy_config.json'
NGINX_SITES_AVAILABLE = '/etc/nginx/sites-available'
NGINX_SITES_ENABLED = '/etc/nginx/sites-enabled'

# --- Funções Auxiliares ---

def run_command(command, check=True):
    """Executa um comando no shell e lida com erros."""
    print(f"[*] Executando: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=check, capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"[!] Erro ao executar o comando: {' '.join(command)}")
        print(f"    Saída do erro: {e.stderr}")
        sys.exit(1)

def install_docker():
    """Instala o Docker Engine e o Docker Compose seguindo o método oficial."""
    print("\n[+] Instalando Docker e Docker Compose...")
    try:
        # Verifica se o Docker já está instalado
        run_command(['docker', '--version'], check=False)
        print("    - Docker já parece estar instalado. Pulando.")
        return
    except FileNotFoundError:
        # Se o comando 'docker' não for encontrado, prossegue com a instalação
        print("    - Docker não encontrado. Iniciando instalação.")
        # 1. Configurar o repositório do Docker
        run_command(['apt-get', 'install', '-y', 'ca-certificates', 'curl'])
        run_command(['install', '-m', '0755', '-d', '/etc/apt/keyrings'])
        run_command(['curl', '-fsSL', 'https://download.docker.com/linux/ubuntu/gpg', '-o', '/etc/apt/keyrings/docker.asc'])
        run_command(['chmod', 'a+r', '/etc/apt/keyrings/docker.asc'])
        
        # Adiciona o repositório às fontes do APT
        arch = run_command(['dpkg', '--print-architecture']).stdout.strip()
        codename = run_command(['bash', '-c', '. /etc/os-release && echo "$VERSION_CODENAME"']).stdout.strip()
        repo_string = f"deb [arch={arch} signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu {codename} stable"
        
        with open("/etc/apt/sources.list.d/docker.list", "w") as f:
            f.write(repo_string)
            
        run_command(['apt-get', 'update'])
        
        # 2. Instalar os pacotes do Docker
        print("    - Instalando pacotes do Docker Engine e Compose...")
        run_command([
            'apt-get', 'install', '-y',
            'docker-ce',
            'docker-ce-cli',
            'containerd.io',
            'docker-buildx-plugin',
            'docker-compose-plugin'
        ])
        print("    - Docker e Docker Compose instalados com sucesso.")


def generate_nginx_config(domain, port):
    """Gera o conteúdo da configuração do Nginx para um serviço."""
    return f"""
server {{
    listen 80;
    server_name {domain};

    location / {{
        proxy_pass http://127.0.0.1:{port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }}
}}
"""

# --- Script Principal ---

def main():
    # 1. Verificar se está rodando como root
    if os.geteuid() != 0:
        print("[!] Este script precisa ser executado como root (sudo).")
        sys.exit(1)

    # 2. Carregar a configuração
    if not os.path.exists(CONFIG_FILE):
        print(f"[!] Arquivo de configuração '{CONFIG_FILE}' não encontrado.")
        sys.exit(1)

    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)

    services = config['services']
    
    # Atualiza os pacotes do sistema
    print("\n[+] Atualizando a lista de pacotes do sistema...")
    run_command(['apt-get', 'update'])

    # ====================================================================
    # NOVA SEÇÃO: Instalação do Docker e Docker Compose
    # ====================================================================
    install_docker()

    # ====================================================================
    # SEÇÃO EXISTENTE: Instalação do Nginx e configuração do Proxy
    # ====================================================================
    print("\n[+] Instalando Nginx...")
    run_command(['apt-get', 'install', '-y', 'nginx'])

    print("\n[+] Configurando o firewall (UFW)...")
    run_command(['ufw', 'allow', 'Nginx Full'])

    print("\n[+] Gerando e ativando configurações do Nginx...")
    for service in services:
        domain = service['domain']
        port = service['port']
        print(f"  -> Configurando {domain}")

        config_content = generate_nginx_config(domain, port)
        config_path = os.path.join(NGINX_SITES_AVAILABLE, domain)
        
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        enabled_link_path = os.path.join(NGINX_SITES_ENABLED, domain)
        if not os.path.exists(enabled_link_path):
            os.symlink(config_path, enabled_link_path)
        else:
            print(f"     - Link de ativação para {domain} já existe. Pulando.")

    print("\n[+] Testando e recarregando o Nginx...")
    run_command(['nginx', '-t'])
    run_command(['systemctl', 'reload', 'nginx'])

    print("\n[✓] Setup do ambiente (Docker, Compose e Nginx) concluído com sucesso!")
    print("Agora você pode clonar seu repositório e rodar 'docker-compose up -d'.")
    print("Verifique os endereços no seu navegador antes de prosseguir com o SSL.")

if __name__ == '__main__':
    main()