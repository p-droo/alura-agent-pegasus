import os
import glob
import streamlit as st
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Carrega variáveis de ambiente do arquivo .env (se existir)
load_dotenv()

st.set_page_config(
    page_title="Pegasus Buddy | Onboarding AI Agent",
    page_icon="🪽",
    layout="wide"
)

# Estilização sutil para cabeçalho e cartões
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🪽 Pegasus Buddy — Assistente de Onboarding</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Agente Inteligente (RAG) da Santo Pegasus Soluciones | Oracle ONE & Alura Challenge</div>', unsafe_allow_html=True)

# Barra lateral (Configurações e Status)
with st.sidebar:
    st.header("⚙️ Configuração do Agente")
    
    api_key_env = os.getenv("GOOGLE_API_KEY", "")
    api_key_input = st.text_input(
        "Google Gemini API Key:",
        value=api_key_env,
        type="password",
        help="Insira sua chave do Google AI Studio ou configure no arquivo .env"
    )
    
    if api_key_input:
        os.environ["GOOGLE_API_KEY"] = api_key_input

    modelo_escolhido = st.selectbox(
        "Modelo Gemini:",
        options=["gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"],
        index=0,
        help="Selecione o modelo disponível para sua chave do Google AI Studio."
    )

    st.divider()
    st.subheader("📄 Base de Conhecimento (PDF)")
    
    # Busca qualquer PDF na pasta atual ou na pasta data/
    arquivos_locais = glob.glob("*.pdf") + glob.glob("data/*.pdf")
    arquivo_upload = st.file_uploader("Ou envie um PDF adicional:", type=["pdf"])
    
    caminho_pdf_ativo = None
    if arquivo_upload is not None:
        caminho_temp = "temp_uploaded.pdf"
        with open(caminho_temp, "wb") as f:
            f.write(arquivo_upload.read())
        caminho_pdf_ativo = caminho_temp
        st.success(f"Usando PDF enviado: {arquivo_upload.name}")
    elif arquivos_locais:
        caminho_pdf_ativo = arquivos_locais[0]
        st.info(f"Documento carregado: `{os.path.basename(caminho_pdf_ativo)}`")
    else:
        st.warning("Nenhum PDF encontrado na pasta. Faça upload acima.")

    st.divider()
    st.markdown("""
    **💡 Sugestões de perguntas:**
    - *O que significam os termos Pegaso, Ninho, Voo e Commit de Batismo?*
    - *Qual é a Regra de Ouro para mergear um Pull Request?*
    - *Quais ferramentas devo instalar para o ambiente Back-end?*
    - *Como funcionam as férias, o cartão Caju e os reembolsos?*
    - *Não recebi acesso à VPN no Dia 1. O que eu faço?*
    """)


@st.cache_resource(show_spinner="Indexando o Manual de Onboarding no banco vetorial FAISS...")
def criar_banco_vetorial(caminho_pdf: str, _api_key: str):
    """Carrega o PDF, divide em chunks e cria o índice vetorial FAISS."""
    loader = PyPDFLoader(caminho_pdf)
    paginas = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(paginas)

    # Tenta os modelos de embedding oficiais do Google AI Studio
    ultimo_erro = None
    for nome_emb in ["models/gemini-embedding-001", "models/text-embedding-004"]:
        try:
            embeddings = GoogleGenerativeAIEmbeddings(
                model=nome_emb,
                google_api_key=_api_key
            )
            vectorstore = FAISS.from_documents(chunks, embeddings)
            return vectorstore, len(paginas), len(chunks)
        except Exception as e:
            ultimo_erro = e
            continue

    raise RuntimeError(f"Erro ao gerar embeddings: {ultimo_erro}")


def obter_resposta_rag(pergunta: str, vectorstore, modelo_llm: str, api_key: str) -> str:
    """Executa a busca MMR no FAISS e gera a resposta fundamentada no documento."""
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 8, "fetch_k": 20}
    )

    llm = ChatGoogleGenerativeAI(
        model=modelo_llm,
        temperature=0.2,
        google_api_key=api_key
    )

    template_prompt = """
Você é o 'Pegasus Buddy', o assistente virtual oficial de Onboarding da Santo Pegasus Soluciones.
Sua missão é ajudar novos colaboradores ('Pegasos') a tirarem dúvidas sobre cultura, estrutura de squads/chapters, acessos do Dia 1, configuração de ambiente (Back-end/Front-end/IDEs), GitFlow, plano de 30/60/90 dias, segurança e benefícios de RH.

Regras obrigatórias:
1. Responda APENAS com base nas informações contidas no CONTEXTO abaixo.
2. Se a resposta não estiver no contexto, diga educadamente que não encontrou essa informação no Manual de Onboarding e sugira procurar o Buddy humano ou os canais #help-ti / #help-rh no Slack.
3. Seja acolhedor, didático, organizado e sempre cite entre parênteses a página de onde tirou cada informação (ex: Página 17).

CONTEXTO EXTRAÍDO DO MANUAL:
{context}

PERGUNTA DO COLABORADOR:
{question}

RESPOSTA DO PEGASUS BUDDY:
"""
    prompt = ChatPromptTemplate.from_template(template_prompt)

    def formatar_docs(docs):
        return "\n\n---\n\n".join(
            [f"[Página {d.metadata.get('page', 0) + 1}]: {d.page_content}" for d in docs]
        )

    rag_chain = (
        {"context": retriever | formatar_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain.invoke(pergunta)


# Inicialização do histórico de conversa
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Olá, novo(a) Pegaso! 🪽 Sou o **Pegasus Buddy**, seu mentor virtual de Onboarding na **Santo Pegasus Soluciones**. Como posso te ajudar hoje com seus acessos, configuração de ambiente, GitFlow ou benefícios?"
        }
    ]

# Exibe histórico de mensagens no chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Entrada do usuário
pergunta_usuario = st.chat_input("Digite sua dúvida sobre o Manual de Onboarding da Santo Pegasus...")

if pergunta_usuario:
    if not os.environ.get("GOOGLE_API_KEY"):
        st.error("⚠️ Por favor, insira sua Google Gemini API Key na barra lateral esquerda antes de enviar uma pergunta.")
    elif not caminho_pdf_ativo:
        st.error("⚠️ Nenhum arquivo PDF encontrado. Coloque o manual na pasta do projeto ou faça o upload na barra lateral.")
    else:
        # Mostra a pergunta do usuário
        st.session_state.messages.append({"role": "user", "content": pergunta_usuario})
        with st.chat_message("user"):
            st.markdown(pergunta_usuario)

        # Gera a resposta do agente
        with st.chat_message("assistant"):
            with st.spinner("Consultando o Manual de Onboarding da Santo Pegasus..."):
                try:
                    vectorstore, num_paginas, num_chunks = criar_banco_vetorial(
                        caminho_pdf_ativo,
                        os.environ["GOOGLE_API_KEY"]
                    )
                    resposta = obter_resposta_rag(
                        pergunta_usuario,
                        vectorstore,
                        modelo_escolhido,
                        os.environ["GOOGLE_API_KEY"]
                    )
                    st.markdown(resposta)
                    st.session_state.messages.append({"role": "assistant", "content": resposta})
                except Exception as e:
                    st.error(f"Ocorreu um erro ao consultar o modelo: {e}")