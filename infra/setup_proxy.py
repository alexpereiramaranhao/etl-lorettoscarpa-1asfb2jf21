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
        subprocess.run(command, check=check, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Erro ao executar o comando: {' '.join(command)}")
        print(f"    Saída do erro: {e.stderr}")
        sys.exit(1)

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

    admin_email = config['admin_email']
    services = config['services']
    domains = [service['domain'] for service in services]

    # 3. Instalar dependências (Nginx e Certbot)
    print("\n[+] Instalando Nginx e Certbot...")
    run_command(['apt-get', 'update'])
    run_command(['apt-get', 'install', '-y', 'nginx', 'certbot', 'python3-certbot-nginx'])

    # 4. Configurar o firewall
    print("\n[+] Configurando o firewall (UFW)...")
    run_command(['ufw', 'allow', 'Nginx Full'])

    # 5. Gerar e ativar configurações do Nginx para cada serviço
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

    # 6. Testar e recarregar o Nginx
    print("\n[+] Testando e recarregando o Nginx...")
    run_command(['nginx', '-t'])
    run_command(['systemctl', 'reload', 'nginx'])

    # 7. Executar o Certbot para obter os certificados SSL
    print("\n[+] Executando o Certbot para obter os certificados SSL...")
    certbot_command = [
        'certbot', '--nginx',
        '--agree-tos',
        '--redirect',
        '--no-eff-email',
        '--email', admin_email
    ]
    for domain in domains:
        certbot_command.extend(['-d', domain])
    
    run_command(certbot_command)

    print("\n[✓] Configuração concluída com sucesso!")
    print("Seus sites devem estar acessíveis via HTTPS.")

if __name__ == '__main__':
    main()