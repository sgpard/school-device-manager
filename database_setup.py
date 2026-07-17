import sqlite3
from werkzeug.security import generate_password_hash

def configurar_banco():
    # Conectando (ou criando) o arquivo de banco de dados
    conexao = sqlite3.connect('escola.db')
    cursor = conexao.cursor()

    # Habilitando o suporte a chaves estrangeiras no SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Criando a tabela de Dispositivos (Tablets e Netbooks)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dispositivos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL,
        patrimonio TEXT UNIQUE NOT NULL,
        serial TEXT,
        status TEXT DEFAULT 'Disponível'
    )
    ''')

    # 2. Tabela de Administradores (Diretora e Coordenadoras)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios_admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        login TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        pergunta_seguranca TEXT NOT NULL,
        resposta_seguranca TEXT NOT NULL 
    )
    ''')

    # 3. Tabela de Movimentações
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_dispositivo INTEGER NOT NULL,
        responsavel_retirada TEXT NOT NULL,
        data_saida DATETIME DEFAULT CURRENT_TIMESTAMP,
        data_devolucao_prevista TEXT,
        data_devolucao_real DATETIME,
        id_admin INTEGER NOT NULL,
        FOREIGN KEY (id_dispositivo) REFERENCES dispositivos (id),
        FOREIGN KEY (id_admin) REFERENCES usuarios_admin (id)
    )
    ''')

    # 4. Criando um Administrador Padrão para Testes Iniciais
    # Verifica se já existe algum usuário cadastrado
    cursor.execute("SELECT COUNT(*) FROM usuarios_admin")
    total_usuarios = cursor.fetchone()[0]

    if total_usuarios == 0:
        print("Nenhum administrador encontrado. Criando usuário padrão para testes...")
        # Dados do Admin de Testes (Seguindo as boas práticas com senha criptografada em Hash)
        nome_padrao = "Administrador"
        login_padrao = "admin"
        senha_padrao = "admin123"  # Esta será a senha de acesso
        pergunta_padrao = "Qual o nome da escola?"
        resposta_padrao = "zanei"  # Resposta de segurança para recuperação

        senha_hash = generate_password_hash(senha_padrao)
        resposta_hash = generate_password_hash(resposta_padrao)

        cursor.execute("""
            INSERT INTO usuarios_admin (nome, login, senha, pergunta_seguranca, resposta_seguranca)
            VALUES (?, ?, ?, ?, ?)
        """, (nome_padrao, login_padrao, senha_hash, pergunta_padrao, resposta_hash))
        
        print(f"Sucesso! Administrador padrão criado.")
        print(f"-> Login: {login_padrao}")
        print(f"-> Senha: {senha_padrao}")

    conexao.commit()
    conexao.close()
    print("Banco de dados configurado e pronto com sucesso!")

if __name__ == "__main__":
    configurar_banco()