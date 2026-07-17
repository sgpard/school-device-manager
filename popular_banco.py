import sqlite3

def popular():
    conexao = sqlite3.connect('escola.db')
    cursor = conexao.cursor()

    print("Iniciando o cadastro em lote dos dispositivos...")

    # 1. Gerando a lista de 213 Tablets 
    tablets = [('Tablet', f'PAT-TAB-{i}', f'SN-TAB-{i}', 'Disponível') for i in range(1, 214)]
    
    # 2. Gerando a lista de 40 Netbooks 
    netbooks = [('Netbook', f'PAT-NET-{i}', f'SN-NET-{i}', 'Disponível') for i in range(1, 41)]

    todos_dispositivos = tablets + netbooks

    # Inserção segura usando OR IGNORE para evitar erros de duplicidade ao re-testar
    try:
        cursor.executemany('''
            INSERT OR IGNORE INTO dispositivos (tipo, patrimonio, serial, status) 
            VALUES (?, ?, ?, ?)
        ''', todos_dispositivos)
        conexao.commit()
        print("Sucesso! Os dispositivos foram processados no banco de dados com segurança.")
    except Exception as e:
        print(f"Erro ao popular o banco de dados: {e}")
    finally:
        conexao.close()

if __name__ == "__main__":
    popular()