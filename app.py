import tkinter as tk
from tkinter import messagebox, ttk
import pyodbc
from datetime import datetime

server = your_server
database = your_database
username = your_username
password = your_password

def conectar_bd():
    try:
        conn = pyodbc.connect(
            f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        )
        return conn
    except Exception as e:
        messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao banco: {e}")
        return None

def obter_origem():
    conn = conectar_bd()
    if conn:
        cursor = conn.cursor()
        query = "SELECT ID, NOME FROM ZMDORIGEM"
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            origens = [(row[0], row[1]) for row in rows]
            return origens
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar origens: {e}")
            return []
        finally:
            conn.close()

def obter_id_origem(nome_origem):
    for origem in origens:
        if origem[1] == nome_origem:
            return origem[0]
    return None

def obter_proximo_id():
    conexao = conectar_bd()
    if not conexao:
        return None

    cursor = conexao.cursor()
    cursor.execute("SELECT MAX(ID) FROM ZMDLEADS")
    ultimo_id = cursor.fetchone()[0]

    cursor.close()
    conexao.close()

    return 41 if ultimo_id is None else ultimo_id + 1

def inserir_dados():
    id_value = obter_proximo_id()
    if id_value is None:
        messagebox.showerror("Erro", "Falha ao obter o próximo ID.")
        return

    if not telefone_entry.get().strip() or not nome_entry.get().strip():
        messagebox.showwarning("Campo obrigatório", "Os campos Nome e Telefone devem ser preenchidos.")
        return

    try:
        data_nascimento = datetime.strptime(dnasc_entry.get(), "%d/%m/%Y").strftime("%Y-%m-%d %H:%M:%S.0000000") if dnasc_entry.get().strip() else None
    except ValueError:
        messagebox.showwarning("Data inválida", "Use o formato DD/MM/YYYY.")
        return

    origem_id = obter_id_origem(origem_combobox.get()) if origem_combobox.get().strip() else None

    id_entry.config(state=tk.NORMAL)
    id_entry.delete(0, tk.END)
    id_entry.insert(0, id_value)
    id_entry.config(state="readonly")

    conn = conectar_bd()
    if conn:
        cursor = conn.cursor()
        try:
            query = """
            INSERT INTO ZMDLEADS (ID, TELEFONE, NAME, DNASC, PROFISSAO, EMAIL, ORIGEM, OBS, INATIVO)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            valores = (
                id_value, 
                telefone_entry.get().strip(), 
                nome_entry.get().strip(), 
                data_nascimento, 
                profissao_entry.get().strip() or None, 
                email_entry.get().strip() or None, 
                origem_id, 
                obs_entry.get().strip() or None,
                0
            )
            cursor.execute(query, valores)
            conn.commit()
            messagebox.showinfo("Sucesso", "Dados inseridos com sucesso!")
            buscar_dados()
            limpar_campos()
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível inserir os dados: {e}")
        finally:
            cursor.close()
            conn.close()

def limpar_campos():
    telefone_entry.delete(0, tk.END)
    nome_entry.delete(0, tk.END)
    dnasc_entry.delete(0, tk.END)
    profissao_entry.delete(0, tk.END)
    email_entry.delete(0, tk.END)
    origem_combobox.set('')
    obs_entry.delete(0, tk.END)

def buscar_dados():
    conn = conectar_bd()
    if not conn:
        return

    cursor = conn.cursor()
    query = """
    SELECT  L.INATIVO, L.ID, L.TELEFONE, L.NAME, 
           CONVERT(VARCHAR, L.DNASC, 103) AS DNASC,
           L.PROFISSAO, L.EMAIL, O.NOME, L.OBS
    FROM ZMDLEADS L
    LEFT JOIN ZMDORIGEM O ON L.ORIGEM = O.ID
    """

    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        tabela.delete(*tabela.get_children())

        for row in rows:
            inativo, id, telefone, nome, dnasc, profissao, email, origem, obs = row
            tabela.insert("", "end", values=(inativo, id, telefone, nome, dnasc, profissao, email, origem, obs))

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao buscar dados: {e}")
    finally:
        cursor.close()
        conn.close()

def formatar_telefone(event):
    texto = telefone_entry.get()
    numeros = ''.join(filter(str.isdigit, texto))

    if len(numeros) > 14:
        numeros = numeros[:14]

    formatado = ""
    if len(numeros) > 0:
        formatado += f"({numeros[:2]})"
    if len(numeros) > 2:
        formatado += f"{numeros[2:7]}"
    if len(numeros) > 6:
        formatado += f"-{numeros[7:11]}"

    if texto != formatado:
        telefone_entry.unbind("<KeyRelease>")
        telefone_entry.delete(0, tk.END)
        telefone_entry.insert(0, formatado)
        telefone_entry.icursor(len(formatado))
        telefone_entry.bind("<KeyRelease>", formatar_telefone)

def formatar_data(event):
    texto = dnasc_entry.get()
    numeros = ''.join(filter(str.isdigit, texto))
    if len(numeros) > 8:
        numeros = numeros[:8]

    formatado = f"{numeros[:2]}" if len(numeros) > 1 else numeros
    if len(numeros) > 2:
        formatado += f"/{numeros[2:4]}"
    if len(numeros) > 4:
        formatado += f"/{numeros[4:]}"

    dnasc_entry.delete(0, tk.END)
    dnasc_entry.insert(0, formatado)
    dnasc_entry.icursor(len(formatado))

def excluir_dados():
    selected_item = tabela.selection()
    if not selected_item:
        messagebox.showwarning("Nenhuma linha selecionada", "Selecione uma linha para excluir.")
        return

    item = tabela.item(selected_item)
    id_to_delete = item['values'][1]

    confirm = messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o registro com ID: {id_to_delete}?")
    if confirm:
        conn = conectar_bd()
        if conn:
            cursor = conn.cursor()
            try:
                query = "DELETE FROM ZMDLEADS WHERE ID = ?"
                cursor.execute(query, (id_to_delete,))
                conn.commit()
                messagebox.showinfo("Sucesso", "Registro excluído com sucesso!")
                buscar_dados()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao excluir o registro: {e}")
            finally:
                conn.close()

def alternar_status():
    selected_item = tabela.selection()
    if not selected_item:
        messagebox.showwarning("Nenhuma linha selecionada", "Selecione uma linha para alterar o status.")
        return

    item = tabela.item(selected_item)
    id_to_toggle = item['values'][1]
    status_atual = item['values'][0]

    novo_status = 0 if status_atual == 1 else 1  
    novo_texto = "Ativar" if novo_status == 0 else "Inativar"

    btn_toggle.config(text=novo_texto)

    confirm = messagebox.askyesno("Confirmar Alteração", f"Tem certeza que deseja {novo_texto.lower()} o registro com ID: {id_to_toggle}?")
    if confirm:
        conn = conectar_bd()
        if conn:
            cursor = conn.cursor()
            try:
                query = "UPDATE ZMDLEADS SET INATIVO = ? WHERE ID = ?"
                cursor.execute(query, (novo_status, id_to_toggle))
                conn.commit()
                messagebox.showinfo("Sucesso", f"Registro {novo_texto.lower()} com sucesso!")
                buscar_dados()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao alterar o status: {e}")
            finally:
                conn.close()

def ajustar_largura_colunas():
    for col in tabela["columns"]:
        max_length = 0
        for item in tabela.get_children():
            value = tabela.item(item, "values")[tabela["columns"].index(col)]
            max_length = max(max_length, len(str(value)))
        tabela.column(col, width=max_length * 10)

def pesquisar_nome():
    nome_pesquisado = pesquisa_entry.get().strip().lower()
    if not nome_pesquisado:
        buscar_dados()
        return

    conn = conectar_bd()
    if not conn:
        return

    cursor = conn.cursor()
    query = """
    SELECT L.INATIVO, L.ID, L.TELEFONE, L.NAME, 
           CONVERT(VARCHAR, L.DNASC, 103) AS DNASC,  -- Formato DD/MM/YYYY
           L.PROFISSAO, L.EMAIL, O.NOME, L.OBS
    FROM ZMDLEADS L
    LEFT JOIN ZMDORIGEM O ON L.ORIGEM = O.ID
    WHERE LOWER(L.NAME) LIKE ?
    """

    try:
        cursor.execute(query, (f"%{nome_pesquisado}%",))  # Usa o operador LIKE para buscar nomes que contenham o texto
        rows = cursor.fetchall()
        tabela.delete(*tabela.get_children())  # Limpa a tabela

        for row in rows:
            inativo, id, telefone, nome, dnasc, profissao, email, origem, obs = row
            tabela.insert("", "end", values=(inativo, id, telefone, nome, dnasc, profissao, email, origem, obs))

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao buscar dados: {e}")
    finally:
        cursor.close()
        conn.close()
        pesquisa_entry.delete(0, tk.END)

root = tk.Tk()
root.title("Cadastro e Consulta")
root.state('zoomed')
root.configure(bg="white")

frame_cadastro = tk.Frame(root, padx=20, pady=20)
frame_cadastro.place(relwidth=0.3, relheight=1)

frame_consulta = tk.Frame(root, padx=10, pady=10)
frame_consulta.place(relwidth=0.7, relheight=1, relx=0.3)

# ========================= ÁREA DE CADASTRO (ESQUERDA) =========================
tk.Label(frame_cadastro, text="Cadastro de Leads", font=("Montserrat", 16, "bold")).pack(pady=10)

label_font = ("Montserrat", 10)
entry_font = ("Montserrat", 10)

tk.Label(frame_cadastro, text="ID:", anchor="w", font=label_font).pack(anchor="w")
id_entry = tk.Entry(frame_cadastro, font=entry_font)
id_entry.pack(fill="x", padx=10, pady=8)
id_entry.config(state="readonly")

labels = ["Telefone:", "Nome:", "Data de Nascimento:", "Profissão:", "E-mail:", "Observações:"]
entries = []

for label in labels:
    tk.Label(frame_cadastro, text=label, anchor="w", font=label_font).pack(anchor="w")
    entry = tk.Entry(frame_cadastro, font=entry_font)
    entry.pack(fill="x", padx=5, pady=5)
    entries.append(entry)

telefone_entry, nome_entry, dnasc_entry, profissao_entry, email_entry, obs_entry = entries

telefone_entry.bind("<KeyRelease>", formatar_telefone)
dnasc_entry.bind("<KeyRelease>", formatar_data)

tk.Label(frame_cadastro, text="Origem:", font=label_font).pack(anchor="w")
origens = obter_origem()
origem_combobox = ttk.Combobox(frame_cadastro, values=[origem[1] for origem in origens], font=entry_font, state="readonly")
origem_combobox.pack(fill="x", padx=5, pady=5)

btn_inserir = tk.Button(frame_cadastro, text="Inserir Dados", font=("Montserrat", 12, "bold"),
                        command=inserir_dados, bg="green", fg="white")
btn_inserir.pack(pady=20)

# ========================= ÁREA DE CONSULTA (DIREITA) =========================

frame_titulo_pesquisa = tk.Frame(frame_consulta)
frame_titulo_pesquisa.pack(fill="x", pady=10)

label_consulta = tk.Label(frame_titulo_pesquisa, text="Consulta de Leads", font=("Montserrat", 16, "bold"))
label_consulta.pack(side="top", pady=5)

frame_pesquisa_direita = tk.Frame(frame_titulo_pesquisa)
frame_pesquisa_direita.pack(side="bottom", fill="x", pady=5)

pesquisa_entry = tk.Entry(frame_pesquisa_direita, font=("Montserrat", 10), width=30)
pesquisa_entry.pack(side="right", padx=5)

lupa_label = tk.Label(frame_pesquisa_direita, text="🔍", font=("Arial", 14))
lupa_label.pack(side="right", padx=5)

pesquisa_entry.bind("<Return>", lambda event: pesquisar_nome())

frame_tabela = tk.Frame(frame_consulta)
frame_tabela.pack(fill="both", expand=True)

colunas = ( "Status", "ID", "Telefone", "Nome", "Data", "Profissão", "E-mail", "Origem", "Observações")
tabela = ttk.Treeview(frame_tabela, columns=colunas, show="headings", selectmode="browse")

for col in colunas:
    tabela.heading(col, text=col)

tabela.column("Status", width=30, anchor="w", stretch=tk.NO)
tabela.column("ID", width=30, anchor="center", stretch=tk.NO)
tabela.column("Telefone", width=100, anchor="center", stretch=tk.NO)
tabela.column("Nome", width=250, anchor="w", stretch=tk.NO)
tabela.column("Data", width=80, anchor="center", stretch=tk.NO)
tabela.column("Profissão", width=150, anchor="center", stretch=tk.NO)
tabela.column("E-mail", width=250, anchor="w", stretch=tk.NO)
tabela.column("Origem", width=100, anchor="center", stretch=tk.NO)
tabela.column("Observações", width=500, anchor="w", stretch=tk.YES)

scrollbar_vertical = tk.Scrollbar(frame_tabela, orient="vertical", command=tabela.yview)
scrollbar_vertical.pack(side="right", fill="y")

scrollbar_horizontal = tk.Scrollbar(frame_tabela, orient="horizontal", command=tabela.xview)
scrollbar_horizontal.pack(side="bottom", fill="x")

tabela.config(yscrollcommand=scrollbar_vertical.set, xscrollcommand=scrollbar_horizontal.set)
tabela.pack(fill="both", expand=True)

frame_botoes = tk.Frame(frame_consulta)
frame_botoes.pack(pady=5)

btn_excluir = tk.Button(frame_botoes, text="Excluir", font=("Montserrat", 12, "bold"),
                        command=excluir_dados, state=tk.DISABLED, bg="#9e1106", fg="white")
btn_excluir.pack(side="left", padx=10)

btn_toggle = tk.Button(frame_botoes, text="Ativar/Inativar", font=("Montserrat", 12, "bold"),
                       command=alternar_status, state=tk.DISABLED, bg="#2c3852", fg="white")
btn_toggle.pack(side="left", padx=5)

btn_buscar = tk.Button(frame_consulta, text="Buscar Dados", font=("Montserrat", 12, "bold"),
                       command=buscar_dados, bg="#0738a3", fg="white")
btn_buscar.pack(pady=10)

def habilitar_botoes(event):
    selected_item = tabela.selection()
    if selected_item:
        item = tabela.item(selected_item)
        status_atual = item['values'][0]

        btn_toggle.config(text="Ativar" if status_atual == 1 else "Inativar", state=tk.NORMAL)
        btn_excluir.config(state=tk.NORMAL)
    else:
        btn_toggle.config(state=tk.DISABLED)
        btn_excluir.config(state=tk.DISABLED)

tabela.bind("<<TreeviewSelect>>", habilitar_botoes)


root.iconbitmap("C:/Users/guilhermerm/Desktop/Programas/Comercial/Programa - Leads/icone.ico")
root.mainloop()