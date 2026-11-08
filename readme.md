# 🪽 Pegasus Buddy — Assistente Inteligente de Onboarding (RAG)

Projeto desenvolvido para o desafio final **Alura Agent** do programa **Oracle Next Education (ONE)**.

---

## 🎯 Contexto e Problema de Negócio

Em empresas de tecnologia em rápido crescimento, novos desenvolvedores enfrentam uma sobrecarga cognitiva nos primeiros dias (*Sprint Zero*): dezenas de páginas de documentação interna sobre arquitetura, configuração de variáveis de ambiente, regras de *Code Review* (GitFlow), prazos de liberação de acessos e políticas de benefícios.

Na **Santo Pegasus Soluciones** (empresa desenvolvedora da plataforma *Agendio* com mais de 180 colaboradores, os *"Pegasos"*), essa dor gerava horas semanais gastas buscando informações em arquivos PDF estáticos ou acionando repetidamente os Tech Leads e o time de People.

### 💡 Solução Proposta (Visão de Produto & Developer Experience)
O **Pegasus Buddy** é um agente conversacional baseado em **RAG (Retrieval-Augmented Generation)** que transforma o *Manual Oficial de Onboarding para Desenvolvedores (19 páginas)* em um mentor virtual interativo disponível 24/7, hospedado na **Oracle Cloud Infrastructure (OCI)**.

* **Redução do *Time-to-Productivity***: Respostas imediatas e passo a passo para configuração de ambiente Java/Spring e Node/React.
* **Zero Alucinação (Fidelidade Documental)**: O agente responde estritamente com base no documento oficial e cita o número exato da página utilizada como fonte.
* **Encaminhamento Inteligente**: Quando uma informação não consta no manual, o agente orienta o colaborador a acionar seu *Buddy humano* ou os canais oficiais do Slack (`#help-ti`, `#help-rh`, `#security-reports`).

---

## 🏗️ Arquitetura da Solução

1. **Ingestão e Leitura (`PyPDFLoader`)**: Extração estruturada das 19 páginas do `Manual de Onboarding para Desenvolvedores — Santo Pegasus Soluciones (PT-BR).pdf`.
2. **Recorte Semântico (`RecursiveCharacterTextSplitter`)**: Divisão do documento em 43 blocos (*chunks*) de `1000` caracteres com sobreposição (*overlap*) de `200` caracteres, preservando tabelas de acessos e listas de comandos.
3. **Vetorização e Indexação (`GoogleGenerativeAIEmbeddings` + `FAISS`)**: Conversão dos trechos em vetores densos (`models/gemini-embedding-001`) armazenados em memória via **FAISS**.
4. **Recuperação Diversificada (`MMR - Maximal Marginal Relevance`)**: Busca dos `k=8` trechos mais relevantes e diversificados entre os 20 principais candidatos (`fetch_k=20`), permitindo responder perguntas compostas em uma única consulta.
5. **Geração Fundamentada (`ChatGoogleGenerativeAI` - `gemini-3.8-flash`)**: Orquestração via **LangChain (LCEL)** com baixa temperatura (`0.2`) e *System Prompt* especializado em *Developer Experience*.
6. **Interface e Deploy (`Streamlit` + `Docker` + `OCI Compute`)**: Interface web interativa empacotada em container Docker e implantada em instância Linux na nuvem da Oracle (OCI).

---

## 💬 Exemplos de Perguntas e Respostas do Agente

| Categoria | Pergunta Enviada ao Agente | Resposta Fundamentada do Pegasus Buddy |
| :--- | :--- | :--- |
| **Cultura & Dicionário Interno** | *"O que significam os termos Pegaso, Ninho, Voo e Commit de Batismo?"* | Explica que **Pegaso** é o colaborador da empresa, **Ninho** é o escritório físico em São Paulo, **Voo** é o lançamento de uma grande feature/versão em produção e **Commit de Batismo** é o primeiro commit mergeado por um novo dev *(Páginas 1, 17 e 18)*. |
| **GitFlow & Code Review** | *"Qual é a Regra de Ouro para mergear um Pull Request e qual estratégia de merge usamos?"* | Informa que o PR deve apontar para a branch `develop`, exigir no mínimo **2 aprovações (Approve)** de outros desenvolvedores, estar com o **CI verde** (GitHub Actions) e utilizar a opção **Squash and merge** *(Páginas 11, 12 e 19)*. |
| **Setup Back-end** | *"Quais versões do Java e do Maven devo instalar para trabalhar no Back-end?"* | Orienta instalar o **SDKMAN**, o **Amazon Corretto 17** (`17.0.9-amzn`) como versão padrão de Java e o **Maven 3.9.6**, além do Docker para subir PostgreSQL e Redis localmente *(Páginas 5, 6 e 8)*. |
| **Acessos do Dia 1** | *"Não recebi meu acesso à VPN no primeiro dia. Qual é o prazo e o que devo fazer?"* | Informa que o acesso ao **OpenVPN** é liberado no Dia 1 (até 17h) pelo time de TI. Caso atrase, orienta abrir chamado no canal `#help-ti` e, se não houver retorno em 24h, acionar o Buddy ou Tech Lead *(Páginas 4, 5 e 18)*. |
| **RH & Benefícios** | *"Quando cai o Vale-Refeição, qual o cartão utilizado e até que dia peço reembolso?"* | Explica que o benefício cai no cartão **Caju (Multibenefícios)** até o **5º dia útil** do mês, e reembolsos de cursos/certificações devem ser aprovados previamente e enviados até o **dia 20** de cada mês *(Página 14)*. |

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
* Python 3.10+ (ou Docker instalado)
* Uma chave de API do Google Gemini ([Google AI Studio](https://aistudio.google.com/app/apikey))

### Opção 1: Execução Local (Python)

1. Clone este repositório:
   ```bash
   git clone https://github.com/SEU-USUARIO/alura-agent-pegasus.git
   cd alura-agent-pegasus
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure sua chave de API criando um arquivo `.env` na raiz (ou insira diretamente na interface lateral do app):
   ```env
   GOOGLE_API_KEY="sua_chave_aqui"
   ```

4. Execute a aplicação Streamlit:
   ```bash
   streamlit run app.py
   ```

### Opção 2: Execução com Docker (Implantação na OCI Compute)

1. Na sua instância **OCI Compute (Ubuntu/Linux)**, clone o repositório e acesse a pasta:
   ```bash
   git clone https://github.com/SEU-USUARIO/alura-agent-pegasus.git
   cd alura-agent-pegasus
   ```

2. Suba o container em background com Docker Compose:
   ```bash
   GOOGLE_API_KEY="sua_chave_aqui" docker compose up -d --build
   ```

3. Acesse no navegador através do IP público da instância OCI na porta `8501`:
   ```text
   http://SEU_IP_PUBLICO_OCI:8501
   ```

---

## ☁️ Demonstração na Oracle Cloud Infrastructure (OCI)

> 📸 **Captura de tela / Link da aplicação em execução na OCI:**
> *(Adicione aqui o print da tela do seu navegador acessando `http://SEU_IP_OCI:8501` ou o link público após subir o container na sua VPS)*

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem**: Python 3.11
* **Orquestração de IA**: LangChain (`langchain`, `langchain-community`, `langchain-core`)
* **LLM & Embeddings**: Google Gemini (`gemini-3.8-flash` & `gemini-embedding-001` via `langchain-google-genai`)
* **Vector Database**: FAISS (`faiss-cpu`)
* **Processamento de Documentos**: `pypdf`
* **Interface Web**: Streamlit
* **Infraestrutura & Nuvem**: Docker & Oracle Cloud Infrastructure (OCI Compute)
