# Dashboard eSocial - Controle de Eventos (TOTVS RM)

## Objetivo
Interface web desenvolvida em Python (Streamlit) para monitorar e auditar eventos do eSocial pendentes de envio no sistema TOTVS RM. O foco é identificar atrasos (regra do 15º dia útil) e mapear responsabilidades por usuário do RH.

## Arquitetura
* **Front-end / Back-end:** Streamlit (Python)
* **Banco de Dados:** SQL Server (Base CorporeRM)
* **Conexão:** PyODBC
* **Processamento de Dados:** Pandas

## Como executar o projeto localmente
1. Certifique-se de ter o Python instalado (versão 3.9 ou superior).
2. Crie um ambiente virtual: `python -m venv venv`
3. Ative o ambiente: `.\venv\Scripts\activate`
4. Instale as dependências: `pip install -r requirements.txt`
5. Configure os dados de acesso ao banco no arquivo `config_db.py`.
6. Execute a aplicação: `streamlit run app.py`