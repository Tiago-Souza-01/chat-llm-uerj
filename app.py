import streamlit as st
import requests

st.set_page_config(page_title='Sistemas de Respostas Automatizadas da UERJ', page_icon='🤖')
st.title('🤖 Sistemas de Respostas Automatizadas da UERJ')

if 'welcome_shown' not in st.session_state:
    st.write(
        "Olá! Bem-vindo ao Sistema de Respostas Automatizadas da UERJ. 🤖\n\n"
        "Escolha um modo na barra lateral e digite sua dúvida para receber respostas."
    )
    st.session_state['welcome_shown'] = True

TARGET_URL = st.secrets.get("TARGET_URL")
API_KEY = st.secrets.get("API_KEY")
HEADERS = {"X-API-KEY": API_KEY, "Content-Type": "application/json"}

# --------------------------
# Seleção de modo (com ícones)
# --------------------------
st.sidebar.markdown("## Modos de Operação")
modo_container = st.sidebar.container()


modo = st.session_state.get('current_mode', "Busca em todo o regulamento da UERJ")
if modo_container.button("📚 Regulamento Completo"):
    if modo != "Busca em todo o regulamento da UERJ":
        st.session_state['last_prompt'] = ""
        st.session_state['last_doc_id'] = None
        st.session_state['last_answer'] = None
        modo = "Busca em todo o regulamento da UERJ"
if modo_container.button("📑 Documento Específico"):
    if modo != "Documento Específico":
        st.session_state['last_prompt'] = ""
        st.session_state['last_doc_id'] = None
        st.session_state['last_answer'] = None
        modo = "Documento Específico"

st.session_state['current_mode'] = modo
st.markdown(f"**Modo ativo:** {modo}")

# Inicializa estado
if 'last_prompt' not in st.session_state:
    st.session_state['last_prompt'] = ""
if 'last_doc_id' not in st.session_state:
    st.session_state['last_doc_id'] = None
if 'last_answer' not in st.session_state:
    st.session_state['last_answer'] = None

def get_response(prompt, document_id=None, top_k=None, all_docs=False):
    payload = {"question": prompt}
    if document_id:
        payload["document_id"] = document_id
    if top_k:
        payload["top_k"] = top_k
    endpoint = f"{TARGET_URL}/ask-all/" if all_docs else f"{TARGET_URL}/ask/"
    with st.spinner("Buscando resposta..."):
        try:
            response = requests.post(endpoint, json=payload, headers=HEADERS)
            response.raise_for_status()
            return response.json().get("answer", "Tente novamente mais tarde.")
        except Exception as e:
            return f"Erro: {e}"

# --------------------------
# Modo Regulamento Completo
# --------------------------
if modo == "Busca em todo o regulamento da UERJ":
    prompt = st.text_input("Escreva sua dúvida aqui:", value=st.session_state['last_prompt'])
    if prompt and prompt != st.session_state['last_prompt']:
        st.session_state['last_prompt'] = prompt
        st.session_state['last_doc_id'] = None
        st.session_state['last_answer'] = get_response(prompt, all_docs=True)

    if st.session_state['last_prompt']:
        st.write(f"**Você perguntou:** {st.session_state['last_prompt']}")
        st.write(f"**Resposta:** {st.session_state['last_answer']}")
        if st.button("Gerar nova resposta"):
            st.session_state['last_answer'] = get_response(st.session_state['last_prompt'], top_k=100, all_docs=True)
            st.write(f"**Nova resposta:** {st.session_state['last_answer']}")

# --------------------------
# Modo Documento Específico
# --------------------------
elif modo == "Documento Específico":
    if 'documents' not in st.session_state:
        try:
            list_response = requests.get(f"{TARGET_URL}/list/", headers=HEADERS)
            list_response.raise_for_status()
            st.session_state['documents'] = list_response.json()
        except Exception as e:
            st.error(f"Erro ao buscar documentos: {e}")
            st.session_state['documents'] = []

    doc_options = ["-- Nenhum --"] + [doc['title'] for doc in st.session_state['documents']]
    selected_doc_title = st.selectbox("Selecione um documento:", doc_options)
    selected_doc_id = None
    if selected_doc_title != "-- Nenhum --":
        for doc in st.session_state['documents']:
            if doc['title'] == selected_doc_title:
                selected_doc_id = doc['public_id']
                break

    prompt = st.text_input("Escreva sua dúvida sobre o documento selecionado:", value=st.session_state['last_prompt'])
    if prompt and prompt != st.session_state['last_prompt'] and selected_doc_id:
        st.session_state['last_prompt'] = prompt
        st.session_state['last_doc_id'] = selected_doc_id
        st.session_state['last_answer'] = get_response(prompt, document_id=selected_doc_id)

    if st.session_state['last_prompt'] and st.session_state['last_doc_id']:
        st.write(f"**Você perguntou:** {st.session_state['last_prompt']}")
        st.write(f"**Resposta:** {st.session_state['last_answer']}")
        if st.button("Gerar nova resposta"):
            st.session_state['last_answer'] = get_response(
                st.session_state['last_prompt'],
                document_id=st.session_state['last_doc_id'],
                top_k=100
            )
            st.write(f"**Nova resposta:** {st.session_state['last_answer']}")
