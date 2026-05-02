import streamlit as st
from datetime import datetime, date, time
import calendar
import pandas as pd
import base64

# --- IMPORTACOES DA ESTRUTURA ---
from database.connection import init_db, SessionLocal
from database.models import Cliente, Receita, Despesa, Procedimento, Foto
from services.whatsapp import gerar_link_whatsapp

# 1. Inicializa Banco de Dados
init_db()

# 2. Configuracoes da Pagina Web
st.set_page_config(page_title="Studio Grazi Rodrigues", page_icon="💅", layout="wide")

# 3. VISUAL (CSS)
st.markdown("""
    <style>
    .stApp { background-color: #F5EDE4; }
    h1, h2, h3 { color: #C8A27C !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [aria-selected="true"] { background-color: transparent !important; color: #C8A27C !important; font-weight: bold; border-bottom: 3px solid #C8A27C; }
    .stButton > button { background-color: #C8A27C !important; color: white !important; border-radius: 8px !important; width: 100%; font-weight: bold !important; border: none !important; }
    .stLinkButton > a { background-color: #25D366 !important; color: white !important; border-radius: 8px !important; width: 100%; font-weight: bold !important; text-decoration: none !important; display: block; text-align: center; border: none !important; }
    
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTimeInput input, div[data-baseweb="select"] > div, .stTextArea textarea {
        background-color: #FFFFFF !important; border: none !important; box-shadow: 0px 2px 5px rgba(0,0,0,0.05) !important; border-radius: 8px !important;
    }

    .balanco-positivo { background-color: #F5EDE4; color: #C8A27C; padding: 20px; border-radius: 10px; font-weight: bold; font-size: 24px; border: 1px solid #C8A27C; }
    .balanco-negativo { background-color: #FFE5E5; color: #D9534F; padding: 20px; border-radius: 10px; font-weight: bold; font-size: 24px; border: 1px solid #D9534F; }
    </style>
""", unsafe_allow_html=True)

# --- SISTEMA DE LOGIN SIMPLES ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

def tela_login():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.write("### 🔒 Acesso Restrito")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if usuario == "admin" and senha == "admin123":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")

# Se não estiver logado, para o código aqui e mostra a tela de login
if not st.session_state.autenticado:
    tela_login()
    st.stop()

st.title("Studio Grazi Rodrigues")
# ...
# 4. ABAS
tab_dash, tab_clientes, tab_procedimentos, tab_servicos, tab_despesas, tab_agenda, tab_financeiro = st.tabs([
    "📊 Dashboard", "👥 Clientes", "⚙️ Procedimentos", "💅 Agendamentos", "💸 Despesas", "📅 Agenda", "💰 Financeiro"
])

db = SessionLocal()
hoje = date.today()
ultimo_dia_mes = calendar.monthrange(hoje.year, hoje.month)[1]
fim_do_mes = date(hoje.year, hoje.month, ultimo_dia_mes)

# --- ABA: PROCEDIMENTOS ---
with tab_procedimentos:
    col_p1, col_p2 = st.columns([1, 2])
    
    if 'proc_edit' not in st.session_state:
        st.session_state.proc_edit = None

    with col_p1:
        st.subheader("Configurar Procedimento")
        with st.form("form_procedimento", clear_on_submit=True):
            p_nome = st.text_input("Nome do Procedimento", value=st.session_state.proc_edit.nome if st.session_state.proc_edit else "")
            p_valor = st.number_input("Preco Padrao (R$)", min_value=0.0, step=5.0, value=st.session_state.proc_edit.valor if st.session_state.proc_edit else 0.0)
            p_manut = st.number_input("% da Manutencao (Ex: 40 para 40%)", min_value=0.0, max_value=100.0, step=5.0, value=st.session_state.proc_edit.percentual_manutencao if st.session_state.proc_edit else 40.0)
            p_cat = st.selectbox("Categoria", ["Cilios", "Sobrancelha"], index=0 if not st.session_state.proc_edit or st.session_state.proc_edit.categoria == "Cilios" else 1)
            
            btn_label = "Atualizar" if st.session_state.proc_edit else "Salvar Novo"
            if st.form_submit_button(btn_label):
                if p_nome and p_valor > 0:
                    if st.session_state.proc_edit:
                        proc = db.query(Procedimento).filter(Procedimento.id == st.session_state.proc_edit.id).first()
                        proc.nome = p_nome
                        proc.valor = p_valor
                        proc.percentual_manutencao = p_manut
                        proc.categoria = p_cat
                        st.session_state.proc_edit = None
                    else:
                        db.add(Procedimento(nome=p_nome, valor=p_valor, percentual_manutencao=p_manut, categoria=p_cat, status="A"))
                    
                    db.commit()
                    st.success("Procedimento salvo!")
                    st.rerun()
        
        if st.session_state.proc_edit:
            if st.button("Cancelar Edicao"):
                st.session_state.proc_edit = None
                st.rerun()

    with col_p2:
        st.subheader("Procedimentos Cadastrados")
        procs = db.query(Procedimento).filter(Procedimento.status == "A").all()
        if procs:
            for p in procs:
                cp1, cp2, cp3 = st.columns([3, 1, 1])
                cp1.write(f"**{p.nome}** ({p.categoria}) | Manut.: {p.percentual_manutencao}%")
                cp2.write(f"R$ {p.valor:.2f}")
                
                if cp3.button("📝", key=f"edit_proc_{p.id}"):
                    st.session_state.proc_edit = p
                    st.rerun()
                st.divider()
        else:
            st.info("Nenhum procedimento cadastrado.")

# --- ABA: CLIENTES ---
with tab_clientes:
    if 'cliente_view' not in st.session_state:
        st.session_state.cliente_view = 'lista'
    if 'cliente_selecionado' not in st.session_state:
        st.session_state.cliente_selecionado = None

    # TELA 1: LISTA DE CLIENTES
    if st.session_state.cliente_view == 'lista':
        col_list_1, col_list_2 = st.columns([4, 1])
        col_list_1.subheader("Lista de Clientes")
        if col_list_2.button("➕ Cadastrar Novo"):
            st.session_state.cliente_view = 'cadastrar'
            st.rerun()
        
        # Filtros e Busca (NOVO)
        c_busca, c_filtro = st.columns([2, 1])
        busca_cliente = c_busca.text_input("🔍 Buscar Cliente por Nome")
        filtro_cli = c_filtro.radio("Ver Clientes:", ["Ativos", "Excluidos", "TODOS"], horizontal=True, key="filtro_cli_radio")
        
        q_cli = db.query(Cliente)
        if busca_cliente:
            q_cli = q_cli.filter(Cliente.nome.contains(busca_cliente))
            
        if filtro_cli == "Ativos": q_cli = q_cli.filter(Cliente.status == "A")
        elif filtro_cli == "Excluidos": q_cli = q_cli.filter(Cliente.status == "E")
        
        clientes_cadastrados = q_cli.all()
        if clientes_cadastrados:
            for c in clientes_cadastrados:
                c1, c2, c3, c4 = st.columns([4, 1, 1, 1])
                niver_str = f" | 🎂 {c.aniversario.strftime('%d/%m/%Y')}" if c.aniversario else ""
                c1.write(f"👤 **{c.nome}** - 📱 {c.telefone}{niver_str}")
                
                if c2.button("📂 Perfil", key=f"perfil_{c.id}"):
                    st.session_state.cliente_view = 'perfil'
                    st.session_state.cliente_selecionado = c.id
                    st.rerun()
                
                if c.status == "A":
                    # Botão Editar Cliente (NOVO)
                    if c3.button("✏️ Editar", key=f"edit_cli_{c.id}"):
                        st.session_state.cliente_view = 'editar'
                        st.session_state.cliente_selecionado = c.id
                        st.rerun()
                    if c4.button("🗑️ Excluir", key=f"del_cli_{c.id}"):
                        c.status = "E"
                        db.commit()
                        st.rerun()
                else:
                    if c3.button("🔄 Restaurar", key=f"res_cli_{c.id}"):
                        c.status = "A"
                        db.commit()
                        st.rerun()
                st.divider()
        else:
            st.info("Nenhum cliente encontrado.")

    # TELA 2: CADASTRAR NOVO CLIENTE (COM OBSERVAÇÃO)
    elif st.session_state.cliente_view == 'cadastrar':
        if st.button("🔙 Voltar para Lista"):
            st.session_state.cliente_view = 'lista'
            st.rerun()
            
        st.subheader("Cadastrar Cliente")
        with st.form("cad_cliente", clear_on_submit=True):
            nome = st.text_input("Nome")
            tel = st.text_input("WhatsApp")
            niver = st.date_input("Data de Aniversario", value=None, min_value=date(1950, 1, 1), max_value=hoje, help="Opcional")
            # Novo campo com limite de 500 chars
            obs = st.text_area("Observacoes / Anotacoes da Cliente", max_chars=500, help="Alergias, tamanho de fio preferido, historico (Max 500 caracteres)")
            
            if st.form_submit_button("Salvar Cliente"):
                if nome and tel:
                    novo_cli = Cliente(nome=nome, telefone=tel, aniversario=niver, obs=obs, status="A")
                    db.add(novo_cli)
                    db.commit()
                    st.success("Cliente cadastrada com sucesso!")
                    st.session_state.cliente_selecionado = novo_cli.id
                    st.session_state.cliente_view = 'perfil'
                    st.rerun()
                else: st.error("Preencha nome e WhatsApp.")

    # TELA 3: EDITAR CLIENTE EXISTENTE (NOVA TELA)
    elif st.session_state.cliente_view == 'editar':
        if st.button("🔙 Cancelar Edicao"):
            st.session_state.cliente_view = 'lista'
            st.session_state.cliente_selecionado = None
            st.rerun()
            
        cli_edit = db.query(Cliente).filter(Cliente.id == st.session_state.cliente_selecionado).first()
        if cli_edit:
            st.subheader(f"✏️ Editar Cliente: {cli_edit.nome}")
            with st.form("edit_cliente"):
                e_nome = st.text_input("Nome", value=cli_edit.nome)
                e_tel = st.text_input("WhatsApp", value=cli_edit.telefone)
                e_niver = st.date_input("Data de Aniversario", value=cli_edit.aniversario, min_value=date(1950, 1, 1), max_value=hoje)
                e_obs = st.text_area("Observacoes / Anotacoes da Cliente", value=cli_edit.obs if cli_edit.obs else "", max_chars=500)
                
                if st.form_submit_button("💾 Salvar Alteracoes"):
                    if e_nome and e_tel:
                        cli_edit.nome = e_nome
                        cli_edit.telefone = e_tel
                        cli_edit.aniversario = e_niver
                        cli_edit.obs = e_obs
                        db.commit()
                        st.success("Dados da cliente atualizados!")
                        st.session_state.cliente_view = 'lista'
                        st.session_state.cliente_selecionado = None
                        st.rerun()
                    else: st.error("Nome e WhatsApp sao obrigatorios.")

    # TELA 4: PERFIL DA CLIENTE (EXIBINDO OBS)
    elif st.session_state.cliente_view == 'perfil':
        if st.button("🔙 Voltar para Lista"):
            st.session_state.cliente_view = 'lista'
            st.session_state.cliente_selecionado = None
            st.rerun()
            
        cli_atual = db.query(Cliente).filter(Cliente.id == st.session_state.cliente_selecionado).first()
        if cli_atual:
            st.subheader(f"📂 Perfil: {cli_atual.nome}")
            st.write(f"**WhatsApp:** {cli_atual.telefone} | **Nascimento:** {cli_atual.aniversario.strftime('%d/%m/%Y') if cli_atual.aniversario else 'Nao informado'}")
            
            # Exibe as observacoes se existirem
            if cli_atual.obs:
                st.info(f"**📌 Observacoes:**\n\n{cli_atual.obs}")
                
            st.divider()
            
            st.markdown("### 📸 Galeria de Fotos")
            with st.expander("➕ Adicionar Nova Foto"):
                with st.form("upload_foto", clear_on_submit=True):
                    up_file = st.file_uploader("Selecione a foto (JPG, PNG, JPEG)", type=['jpg', 'jpeg', 'png'])
                    up_legenda = st.text_input("Legenda / Procedimento (Ex: Cilios Volume Brasil 10/05)")
                    
                    if st.form_submit_button("Salvar Foto"):
                        if up_file is not None:
                            bytes_data = up_file.getvalue()
                            b64_img = base64.b64encode(bytes_data).decode('utf-8')
                            db.add(Foto(cliente_id=cli_atual.id, imagem=b64_img, legenda=up_legenda))
                            db.commit()
                            st.success("Foto adicionada com sucesso!")
                            st.rerun()
                        else:
                            st.error("Por favor, selecione uma imagem.")
            
            fotos = db.query(Foto).filter(Foto.cliente_id == cli_atual.id).order_by(Foto.id.desc()).all()
            if fotos:
                cols = st.columns(3)
                for idx, f in enumerate(fotos):
                    with cols[idx % 3]:
                        img_bytes = base64.b64decode(f.imagem)
                        st.image(img_bytes, use_column_width=True)
                        with st.popover("✏️ Editar/Excluir"):
                            nova_legenda = st.text_input("Editar Legenda", value=f.legenda if f.legenda else "", key=f"leg_{f.id}")
                            if st.button("💾 Salvar Legenda", key=f"slv_{f.id}"):
                                f.legenda = nova_legenda
                                db.commit()
                                st.rerun()
                            if st.button("🗑️ Excluir Foto", key=f"del_{f.id}"):
                                db.delete(f)
                                db.commit()
                                st.rerun()
                        st.caption(f.legenda if f.legenda else "Sem legenda")
            else:
                st.info("Nenhuma foto salva para esta cliente ainda.")

# --- ABA: SERVICOS ---
with tab_servicos:
    st.subheader("Lancar Novo Agendamento 💅")
    clientes_ativos = db.query(Cliente).filter(Cliente.status == "A").all()
    lista_nomes = {c.nome: c.id for c in clientes_ativos}
    
    if lista_nomes:
        col_form, col_resumo = st.columns([2, 1])
        with col_form:
            cliente_sel = st.selectbox("Selecione a Cliente", options=list(lista_nomes.keys()))
            c_data, c_hora = st.columns(2)
            data_m = c_data.date_input("Data Atendimento", value=hoje)
            hora_m = c_hora.time_input("Hora Atendimento", value=time(9, 0))
            
            cat_servico = st.radio("Tipo de Atendimento", ["Colocacao", "Manutencao", "Sobrancelha"], horizontal=True)
            
            cat_busca = "Sobrancelha" if cat_servico == "Sobrancelha" else "Cilios"
            procs_db = db.query(Procedimento).filter(Procedimento.categoria == cat_busca, Procedimento.status == "A").all()
            
            if procs_db:
                dict_procs = {p.nome: p for p in procs_db}
                s_nome = st.selectbox("Escolha o Procedimento", options=list(dict_procs.keys()))
                
                proc_selecionado = dict_procs[s_nome]
                v_base = proc_selecionado.valor
                
                if cat_servico == "Manutencao":
                    v_base = v_base * (proc_selecionado.percentual_manutencao / 100.0)
                
                v_final = st.number_input("Valor Final (R$)", value=float(v_base), step=5.0)
                f_pagto = st.selectbox("Forma de Pagamento", ["Pix", "Cartao", "Dinheiro", "Pendente"])
                
                if st.button("🚀 Confirmar Agendamento"):
                    db.add(Receita(valor=v_final, data=data_m, cliente_id=lista_nomes[cliente_sel], 
                                   servico=f"{cat_servico}: {s_nome} ({hora_m.strftime('%H:%M')})", 
                                   forma_pagamento=f_pagto, status="P"))
                    db.commit()
                    st.success("Agendamento registrado na Agenda!")
            else:
                st.warning(f"Nenhum procedimento de '{cat_busca}' cadastrado. Va na aba Procedimentos primeiro!")
    else:
        st.info("Cadastre uma cliente primeiro!")

# --- ABA: DESPESAS ---
with tab_despesas:
    col_d1, col_d2 = st.columns([1, 2])
    with col_d1:
        st.subheader("Cadastrar Despesa")
        with st.form("form_despesa", clear_on_submit=True):
            d_nome = st.text_input("Descricao (Aluguel, Luz, Materiais...)")
            d_valor = st.number_input("Valor Saida (R$)", min_value=0.0, step=10.0)
            d_data = st.date_input("Data Saida", value=hoje)
            if st.form_submit_button("Salvar Despesa"):
                if d_nome and d_valor > 0:
                    db.add(Despesa(valor=d_valor, data=d_data, categoria=d_nome, status="A"))
                    db.commit()
                    st.success("Despesa salva!")
                    st.rerun()
    with col_d2:
        st.subheader("Lista de Despesas")
        filtro_desp = st.radio("Filtro Despesas:", ["Ativas", "Excluidas"], horizontal=True)
        q_desp = db.query(Despesa).filter(Despesa.status == ("A" if filtro_desp == "Ativas" else "S"))
        for d in q_desp.all():
            cd1, cd2 = st.columns([4, 1])
            cd1.write(f"💸 {d.data.strftime('%d/%m/%Y')} | **R$ {d.valor:.2f}** | {d.categoria}")
            if d.status == "A":
                if cd2.button("🗑️", key=f"del_desp_{d.id}"):
                    d.status = "S"
                    db.commit()
                    st.rerun()
            st.divider()

# --- ABA: AGENDA ---
with tab_agenda:
    st.subheader("Agenda 📅")
    
    if 'agenda_edit' not in st.session_state:
        st.session_state.agenda_edit = None

    if st.session_state.agenda_edit:
        st.markdown("### ✏️ Editar Agendamento")
        rec_edit = db.query(Receita).filter(Receita.id == st.session_state.agenda_edit).first()
        
        if rec_edit:
            cli_edit = db.query(Cliente).filter(Cliente.id == rec_edit.cliente_id).first()
            st.write(f"**Cliente:** {cli_edit.nome if cli_edit else 'Desconhecida'}")
            
            try:
                old_cat = rec_edit.servico.split(':')[0].strip()
                rest = rec_edit.servico.split(':')[1]
                old_proc = rest.split('(')[0].strip()
                old_time_str = rest.split('(')[1].replace(')','').strip()
                old_time = datetime.strptime(old_time_str, "%H:%M").time()
            except:
                old_cat = "Colocacao"
                old_proc = ""
                old_time = time(9, 0)
                
            cat_index = 0
            if old_cat == "Manutencao": cat_index = 1
            elif old_cat == "Sobrancelha": cat_index = 2

            e_data = st.date_input("Nova Data", value=rec_edit.data, key="ed_data")
            e_hora = st.time_input("Nova Hora", value=old_time, key="ed_hora")
            e_cat = st.radio("Nova Categoria", ["Colocacao", "Manutencao", "Sobrancelha"], index=cat_index, horizontal=True, key="ed_cat")

            cat_busca = "Sobrancelha" if e_cat == "Sobrancelha" else "Cilios"
            procs_db = db.query(Procedimento).filter(Procedimento.categoria == cat_busca, Procedimento.status == "A").all()

            if procs_db:
                dict_procs = {p.nome: p for p in procs_db}
                proc_options = list(dict_procs.keys())
                proc_index = proc_options.index(old_proc) if old_proc in proc_options else 0
                
                e_nome = st.selectbox("Novo Procedimento", options=proc_options, index=proc_index, key="ed_nome")
                proc_selecionado = dict_procs[e_nome]
                
                v_base = proc_selecionado.valor
                if e_cat == "Manutencao":
                    v_base = v_base * (proc_selecionado.percentual_manutencao / 100.0)
                    
                e_valor = st.number_input(f"Valor (Sugestao R$ {v_base:.2f})", value=float(rec_edit.valor), step=5.0, key="ed_valor")
                
                pagto_opts = ["Pix", "Cartao", "Dinheiro", "Pendente"]
                pagto_idx = pagto_opts.index(rec_edit.forma_pagamento) if rec_edit.forma_pagamento in pagto_opts else 3
                e_pagto = st.selectbox("Forma de Pagamento", pagto_opts, index=pagto_idx, key="ed_pagto")

                c_btn1, c_btn2 = st.columns(2)
                if c_btn1.button("💾 Salvar Alteracoes", use_container_width=True):
                    rec_edit.data = e_data
                    rec_edit.servico = f"{e_cat}: {e_nome} ({e_hora.strftime('%H:%M')})"
                    rec_edit.valor = e_valor
                    rec_edit.forma_pagamento = e_pagto
                    db.commit()
                    st.session_state.agenda_edit = None
                    st.rerun()
            else:
                st.warning("Cadastre procedimentos desta categoria primeiro!")
            
            if st.button("❌ Cancelar Edicao"):
                st.session_state.agenda_edit = None
                st.rerun()
                
        st.divider()

    else:
        c_f1, c_f2, c_f3 = st.columns([1, 1, 1])
        data_ini = c_f1.date_input("De:", value=hoje, key="agenda_de")
        data_fim = c_f2.date_input("Ate:", value=fim_do_mes, key="agenda_ate")
        busca_nome = c_f3.text_input("🔍 Buscar Nome", key="agenda_busca")
        
        filtro_status = st.radio("Status:", ["Pendentes", "Realizados", "Desmarcados", "TODOS"], horizontal=True, key="status_agenda")
        query_age = db.query(Receita).join(Cliente).filter(Receita.data >= data_ini, Receita.data <= data_fim)
        if busca_nome: query_age = query_age.filter(Cliente.nome.contains(busca_nome))
        
        if filtro_status == "Pendentes": query_age = query_age.filter(Receita.status == "P")
        elif filtro_status == "Realizados": query_age = query_age.filter(Receita.status == "R")
        elif filtro_status == "Desmarcados": query_age = query_age.filter(Receita.status == "S")
        
        for a in query_age.order_by(Receita.data.asc()).all():
            cliente = db.query(Cliente).filter(Cliente.id == a.cliente_id).first()
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                st_cor = "⏳" if a.status == "P" else ("✅" if a.status == "R" else "❌")
                col1.write(f"{st_cor} **{cliente.nome}** | 📅 {a.data.strftime('%d/%m')} | {a.servico}")
                col2.link_button("📲 WPP", gerar_link_whatsapp(cliente.telefone, f"Ola {cliente.nome}! Confirmando seu horario..."))
                
                if a.status == "P":
                    if col3.button("✅ Feito", key=f"ok_{a.id}"):
                        a.status = "R"
                        db.commit()
                        st.rerun()
                    if col4.button("✏️ Editar", key=f"edit_{a.id}"):
                        st.session_state.agenda_edit = a.id
                        st.rerun()
                    if col5.button("🗑️ Canc.", key=f"canc_{a.id}"):
                        a.status = "S"
                        db.commit()
                        st.rerun()
                elif a.status == "S" or a.status == "R":
                    if col3.button("🔄 Voltar", key=f"back_{a.id}"):
                        a.status = "P"
                        db.commit()
                        st.rerun()
                    if col4.button("✏️ Editar", key=f"edit_{a.id}"):
                        st.session_state.agenda_edit = a.id
                        st.rerun()
            st.divider()

# --- ABA: FINANCEIRO ---
with tab_financeiro:
    st.subheader("Balanco Financeiro 💰")
    cf1, cf2, cf3 = st.columns([1, 1, 1])
    f_ini = cf1.date_input("Inicio", value=date(hoje.year, hoje.month, 1), key="fin_ini")
    f_fim = cf2.date_input("Fim", value=fim_do_mes, key="fin_fim")
    m_visao = cf3.radio("Ver:", ["Balanco", "Receitas", "Despesas"], horizontal=True, key="fin_visao")
    
    recs = db.query(Receita).filter(Receita.data >= f_ini, Receita.data <= f_fim, Receita.status == "R").all()
    desps = db.query(Despesa).filter(Despesa.data >= f_ini, Despesa.data <= f_fim, Despesa.status == "A").all()
    
    t_r = sum(r.valor for r in recs)
    t_d = sum(d.valor for d in desps)
    
    if m_visao != "Despesas":
        st.write("### 📥 Receitas")
        for r in recs: 
            cli = db.query(Cliente).filter(Cliente.id == r.cliente_id).first()
            st.write(f"✅ {r.data.strftime('%d/%m')} | R$ {r.valor:.2f} | {cli.nome if cli else 'Avulso'} - {r.servico}")
    
    if m_visao != "Receitas":
        st.write("### 📤 Despesas")
        for d in desps: st.write(f"❌ {d.data.strftime('%d/%m')} | R$ {d.valor:.2f} | {d.categoria}")
    
    st.divider()
    classe = "balanco-positivo" if (t_r - t_d) >= 0 else "balanco-negativo"
    st.markdown(f'<div class="{classe}">Saldo Final: R$ {t_r - t_d:.2f}</div>', unsafe_allow_html=True)

# --- ABA: DASHBOARD ---
with tab_dash:
    st.subheader("Painel Mensal 📊")
    f_fat = sum(r.valor for r in db.query(Receita).filter(Receita.status == "R").all() if r.data.month == hoje.month)
    f_des = sum(d.valor for d in db.query(Despesa).filter(Despesa.status == "A").all() if d.data.month == hoje.month)
    c1, c2, c3 = st.columns(3)
    c1.metric("Faturamento", f"R$ {f_fat:.2f}")
    c2.metric("Despesas", f"R$ {f_des:.2f}")
    c3.metric("Lucro", f"R$ {f_fat - f_des:.2f}")

db.close()