import sqlite3

def limpar_ambiente():
    conexao = sqlite3.connect('escola.db')
    cursor = conexao.cursor()

    print("Iniciando a limpeza do histórico de testes...")

    try:
        # 1. Deleta todas as linhas de movimentação gravadas
        cursor.execute("DELETE FROM movimentacoes")
        
        # 2. Reseta o auto-incremento da tabela de movimentações no SQLite
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='movimentacoes'")

        # 3. Reseta o status de absolutamente todos os dispositivos de volta para Disponível
        cursor.execute("UPDATE dispositivos SET status = 'Disponível'")

        conexao.commit()
        print("Sucesso! Histórico esvaziado e todos os dispositivos estão 'Disponíveis' para uso real.")
    except Exception as e:
        print(f"Erro ao limpar o ambiente de testes: {e}")
    finally:
        conexao.close()

if __name__ == "__main__":
    limpar_ambiente()