import streamlit as st
import requests

st.set_page_config(page_title='Sistemas de Respostas Automatizadas da UERJ', page_icon='🤖')
st.title('🤖 Sistemas de Respostas Automatizadas da UERJ')

if 'welcome_shown' not in st.session_state:
    st.chat_message("assistant").write(
        "Olá! Bem-vindo ao Sistema de Respostas Automatizadas da UERJ. 🤖\n\n"
        "Escolha um modo na barra lateral e digite sua dúvida para receber respostas."
    )
    st.session_state['welcome_shown'] = True

TARGET_URL = st.secrets.get("TARGET_URL")
API_KEY = st.secrets.get("API_KEY")
HEADERS = {"X-API-KEY": API_KEY, "Content-Type": "application/json"}

st.sidebar.markdown("## ⚙️ Modos de Operação")
modo_container = st.sidebar.container()


modo = st.session_state.get('current_mode', "Busca em todo o regulamento da UERJ")


if modo_container.button("📚 Regulamento Completo"):
    if modo != "Busca em todo o regulamento da UERJ":
        for key in ['last_prompt', 'last_doc_id', 'last_answer']:
            st.session_state[key] = None
        modo = "Busca em todo o regulamento da UERJ"

if modo_container.button("📑 Documento Específico"):
    if modo != "Documento Específico":
        for key in ['last_prompt', 'last_doc_id', 'last_answer']:
            st.session_state[key] = None
        modo = "Documento Específico"

st.session_state['current_mode'] = modo
st.markdown(f"**🟢 Modo ativo:** {modo}")

for key, default in {
    'last_prompt': None,
    'last_doc_id': None,
    'last_answer': None,
    'documents': []
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


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


if modo == "Busca em todo o regulamento da UERJ":
    prompt = st.chat_input("Escreva sua dúvida aqui:")
    if prompt:
        st.session_state['last_prompt'] = prompt
        st.session_state['last_doc_id'] = None
        st.session_state['last_answer'] = get_response(prompt, all_docs=True)

    if st.session_state['last_prompt']:
        st.chat_message("user").write(st.session_state['last_prompt'])
        st.chat_message("assistant").write(st.session_state['last_answer'])

        if st.button("🔄 Gerar nova resposta"):
            new_answer = get_response(st.session_state['last_prompt'], top_k=100, all_docs=True)
            st.session_state['last_answer'] = new_answer
            st.chat_message("assistant").write(new_answer)


elif modo == "Documento Específico":
    if not st.session_state['documents']:
        try:
            list_response = requests.get(f"{TARGET_URL}/list/", headers=HEADERS)
            list_response.raise_for_status()
            st.session_state['documents'] = list_response.json()
        except Exception as e:
            st.error(f"Erro ao buscar documentos: {e}")
            st.session_state['documents'] = []

    doc_options = ["-- Nenhum --"] + [doc['title'] for doc in st.session_state['documents']]
    selected_doc_title = st.selectbox("📄 Selecione um documento:", doc_options)

    selected_doc_id = None
    if selected_doc_title != "-- Nenhum --":
        for doc in st.session_state['documents']:
            if doc['title'] == selected_doc_title:
                selected_doc_id = doc['public_id']
                break

    prompt = st.chat_input("Escreva sua dúvida sobre o documento selecionado:")
    if prompt and selected_doc_id:
        st.session_state['last_prompt'] = prompt
        st.session_state['last_doc_id'] = selected_doc_id
        st.session_state['last_answer'] = get_response(prompt, document_id=selected_doc_id)

    if st.session_state['last_prompt'] and st.session_state['last_doc_id']:
        st.chat_message("user").write(st.session_state['last_prompt'])
        st.chat_message("assistant").write(st.session_state['last_answer'])

        if st.button("🔄 Gerar nova resposta"):
            new_answer = get_response(
                st.session_state['last_prompt'],
                document_id=st.session_state['last_doc_id'],
                top_k=20
            )
            st.session_state['last_answer'] = new_answer
            st.chat_message("assistant").write(new_answer)