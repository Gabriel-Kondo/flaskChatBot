from flask import Blueprint, render_template, request, session
from datetime import datetime
from app import socketio
import os
from app.gemini.modelo import responder_pergunta

bp = Blueprint("chat", __name__)

def registrar_log(origem, mensagem, chat_id):
    os.makedirs("logs", exist_ok=True)
    caminho = f"logs/chat_{chat_id}.log"
    mensagem = mensagem.strip()
    if mensagem:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(caminho, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{origem}] {mensagem}\n")
        html = f"[{timestamp}] [{origem}] {mensagem}"
        socketio.emit("nova_mensagem", {"html": f'<font color="{cor_por_origem(origem)}">{html}</font>'})

def cor_por_origem(origem):
    cores = {
        "USUÁRIO": "red",
        "GEMINI": "blue",
        "SISTEMA": "gray"
    }
    return cores.get(origem.upper(), "white")

def carregar_historico():
    chat_id = session.get("chat_id")
    caminho = f"logs/chat_{chat_id}.log"
    linhas_coloridas = []
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            for linha in f:
                origem = "USUÁRIO" if "[USUÁRIO]" in linha else "GEMINI" if "[GEMINI]" in linha else "SISTEMA"
                cor = cor_por_origem(origem)
                linhas_coloridas.append(f'<font color="{cor}">{linha.strip()}</font>')
    return linhas_coloridas

@bp.route("/")
def home():
    return render_template("index.html")

@bp.route("/chat", methods=["GET", "POST"])
def chat():
    if "chat_id" not in session:
        session["chat_id"] = datetime.now().strftime("%Y%m%d-%H%M%S")
        registrar_log("SISTEMA", f"=== Início da Sessão {session['chat_id']} ===", session["chat_id"])

    if request.method == "POST":
        if "encerrar" in request.form:
            registrar_log("SISTEMA", f"=== Fim da Sessão {session['chat_id']} ===", session["chat_id"])
            session.pop("chat_id", None)
            return render_template("chat.html", historico=[])
        
        mensagem = request.form.get("mensagem", "").strip()
        registrar_log("USUÁRIO", mensagem, session["chat_id"])

        if mensagem.endswith("?"):
            resposta = responder_pergunta(mensagem)
            registrar_log("GEMINI", resposta, session["chat_id"])


    historico = carregar_historico()
    return render_template("chat.html", historico=historico)
