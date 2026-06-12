from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from flask_socketio import SocketIO
import sqlite3

# =========================================================
# APP
# =========================================================

app = Flask(__name__)
app.secret_key = "fogareu_secret"

socketio = SocketIO(app, cors_allowed_origins="*")

# =========================================================
# BANCO
# =========================================================

def conectar():
    conn = sqlite3.connect("FogareuClothes.db")
    conn.row_factory = sqlite3.Row
    return conn


def emitir_atualizacao():
    socketio.emit("atualizar_dashboard")


# =========================================================
# INICIO
# =========================================================

@app.route("/")
def index():
    return render_template("index.html")


# =========================================================
# CADASTRO ADMIN
# =========================================================

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":

        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO usuario (nome, email, senha)
            VALUES (?, ?, ?)
        """, (nome, email, senha))

        conn.commit()
        conn.close()

        flash("Administrador cadastrado!", "success")
        return redirect(url_for("login"))

    return render_template("cadastro.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        senha = request.form.get("senha")

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM usuario
            WHERE email = ? AND senha = ?
        """, (email, senha))

        usuario = cursor.fetchone()
        conn.close()

        if usuario:
            session["admin"] = usuario["nome"]
            return redirect(url_for("dashboard"))

        flash("Login inválido", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================
@app.route("/logout")
def logout():

    session.clear()
    return redirect(url_for("login"))


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "admin" not in session:
        return redirect(url_for("login"))

    conn = conectar()
    cursor = conn.cursor()

    # PRODUTOS
    cursor.execute("SELECT COUNT(*) FROM produtos")
    total_produtos = cursor.fetchone()[0]

    # CLIENTES
    cursor.execute("SELECT COUNT(*) FROM cliente")
    total_clientes = cursor.fetchone()[0]

    # PEDIDOS
    cursor.execute("SELECT COUNT(*) FROM pedido")
    total_pedidos = cursor.fetchone()[0]

    # VARIAÇÕES
    cursor.execute("SELECT COUNT(*) FROM variacoes")
    total_variacoes = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        produtos=total_produtos,
        pedidos=total_pedidos,
        cliente=total_clientes,
        variacoes=total_variacoes
    )


# =========================================================
# CLIENTE (LISTAR)
# =========================================================
@app.route("/cliente", methods=["GET", "POST"])
def cliente():

    if "admin" not in session:
        return redirect(url_for("login"))

    conn = conectar()
    cursor = conn.cursor()

    # CADASTRAR CLIENTE
    if request.method == "POST":

        nome = request.form.get("nome")
        cpf = request.form.get("cpf")
        email = request.form.get("email")
        telefone = request.form.get("telefone")
        endereco = request.form.get("endereco")

        cursor.execute("""
            INSERT INTO cliente (nome, cpf, email, telefone, endereco)
            VALUES (?, ?, ?, ?, ?)
        """, (nome, cpf, email, telefone, endereco))

        conn.commit()
        conn.close()

        return redirect(url_for("cliente"))

    # LISTAR CLIENTES
    cursor.execute("SELECT * FROM cliente ORDER BY rowid DESC")
    lista = cursor.fetchall()

    conn.close()

    return render_template("cliente.html", cliente=lista)


# =========================================================
# Cadastro de Produtos
# =========================================================

@app.route("/cadastro-produto", methods=["GET", "POST"])
def cadastro_produto():

    if "admin" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        nome = request.form["nome"]
        descricao = request.form["descricao"]
        preco = request.form["preco_base"]
        categoria = request.form["categoria"]

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO produtos (nome, descricao, preco_base, categoria)
            VALUES (?, ?, ?, ?)
        """, (nome, descricao, preco, categoria))

        conn.commit()
        conn.close()

        emitir_atualizacao()

        return redirect(url_for("produtos"))

    return render_template("cadastro-produto.html")


# =========================================================
# Produtos
# =========================================================

@app.route("/produtos")
def produtos():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM produtos ORDER BY id_produto DESC")
    lista = cursor.fetchall()

    conn.close()

    return render_template("produtos.html", produtos=lista)


# =========================================================
# Excluir Produtos
# =========================================================


@app.route("/produtos/excluir/<int:id_produto>", methods=["POST"])
def excluir_produto(id_produto):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM produtos WHERE id_produto = ?", (id_produto,))

    conn.commit()
    conn.close()

    emitir_atualizacao()

    return redirect(url_for("produtos"))


# =========================================================
# EDITAR PRODUTOS
# =========================================================
@app.route("/produtos/editar/<int:id_produto>", methods=["GET", "POST"])
def editar_produto(id_produto):

    if "admin" not in session:
        return redirect(url_for("login"))

    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":

        nome = request.form.get("nome")
        descricao = request.form.get("descricao")
        preco_base = request.form.get("preco_base")
        categoria = request.form.get("categoria")

        cursor.execute("""
            UPDATE produtos
            SET nome = ?, descricao = ?, preco_base = ?, categoria = ?
            WHERE id_produto = ?
        """, (nome, descricao, preco_base, categoria, id_produto))

        conn.commit()
        conn.close()

        return redirect(url_for("produtos"))

    cursor.execute("""
        SELECT * FROM produtos WHERE id_produto = ?
    """, (id_produto,))

    produto = cursor.fetchone()
    conn.close()

    return render_template("editar-produto.html", produto=produto)


# =========================================================
# VARIAÇÕES (LISTAR)
# =========================================================

@app.route("/variacoes")
def variacoes():

    if "admin" not in session:
        return redirect(url_for("login"))

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM variacoes
        ORDER BY rowid DESC
    """)

    lista_variacoes = cursor.fetchall()
    conn.close()

    return render_template(
        "variacoes.html",
        variacoes=lista_variacoes
    )


# =========================================================
# CADASTRAR VARIAÇÕES
# =========================================================

@app.route("/variacoes/cadastrar", methods=["POST"])
def cadastrar_variacao():

    if "admin" not in session:
        return redirect(url_for("login"))

    id_produto = request.form.get("id_produto")
    cor = request.form.get("cor")
    tamanho = request.form.get("tamanho")
    estoque = request.form.get("estoque")

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO variacoes (id_produto, cor, tamanho, estoque_atual)
        VALUES (?, ?, ?, ?)
    """, (id_produto, cor, tamanho, estoque))

    conn.commit()
    conn.close()

    return redirect(url_for("variacoes"))


# =========================================================
# PEDIDOS
# =========================================================

@app.route("/pedidos", methods=["GET", "POST"])
def pedidos():

    if "admin" not in session:
        return redirect(url_for("login"))

    conn = conectar()
    cursor = conn.cursor()

    # =========================
    # SALVAR PEDIDO
    # =========================
    if request.method == "POST":

        id_cliente = request.form.get("id_cliente")
        data_venda = request.form.get("data")
        status = request.form.get("status")

        cursor.execute("""
            INSERT INTO Pedido
            (id_cliente, data_venda, status)
            VALUES (?, ?, ?)
        """, (
            id_cliente,
            data_venda,
            status
        ))

        id_pedido = cursor.lastrowid

        id_produto = request.form.get("id_produto")
        quantidade = request.form.get("quantidade")

        if id_produto and quantidade:

            cursor.execute("""
                INSERT INTO Pedido_Produto
                (id_pedido, id_produto, quantidade)
                VALUES (?, ?, ?)
            """, (
                id_pedido,
                id_produto,
                quantidade
            ))

        conn.commit()

        conn.close()

        return redirect(url_for("pedidos"))

    # =========================
    # LISTAR PEDIDOS
    # =========================
    cursor.execute("""
        SELECT
            p.id_pedido,
            c.nome,
            p.data_venda,
            p.status
        FROM Pedido p
        INNER JOIN Cliente c
            ON c.id_cliente = p.id_cliente
        ORDER BY p.id_pedido DESC
    """)
    lista_pedidos = cursor.fetchall()

    # =========================
    # CLIENTES
    # =========================
    cursor.execute("""
        SELECT
            id_cliente,
            nome
        FROM Cliente
        ORDER BY nome
    """)
    lista_clientes = cursor.fetchall()

    # =========================
    # PRODUTOS
    # =========================
    cursor.execute("""
        SELECT
            id_produto,
            nome,
            preco_base
        FROM Produtos
        ORDER BY nome
    """)
    lista_produtos = cursor.fetchall()

    conn.close()

    return render_template(
        "pedidos.html",
        pedidos=lista_pedidos,
        clientes=lista_clientes,
        produtos=lista_produtos
    )

# =========================================================
# SOCKETIO EVENT
# =========================================================

@socketio.on("connect")
def connect():
    print("Cliente conectado")


# =========================================================
# RUN
# =========================================================

app = Flask(__name__)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
