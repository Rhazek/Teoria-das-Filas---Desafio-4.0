# Porto do Itaqui — Simulador de Filas M/M/4

Simulador interativo de filas para o Porto do Itaqui com suporte a múltiplas políticas de sequenciamento (FIFO, Prioridade Não Preemptiva, SJF, LCFS).

## 🏗️ Arquitetura

- **Backend**: FastAPI + Python (Render)
- **Frontend**: HTML5 + Tailwind CSS (Vercel)
- **Comunicação**: REST API (CORS habilitado)

## 🚀 Deploy

### 1. Backend no Render

1. Faça push do repositório para GitHub
2. Acesse [render.com](https://render.com)
3. Clique em "New +" → "Web Service"
4. Conecte seu repositório GitHub
5. Configure:
   - **Name**: `porto-itaqui-api`
   - **Runtime**: `Python 3.11`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Region**: Qualquer (recomendado: Ohio ou São Paulo)
6. Clique em "Create Web Service"
7. Copie o URL da API (ex: `https://porto-itaqui-api.onrender.com`)

### 2. Frontend no Vercel

1. Extraia apenas o arquivo `frontend.html`
2. Crie um repositório separado ou adicione a uma pasta `public/`
3. No `frontend.html`, a URL da API será configurada automaticamente

#### Opção A: Deploy simples (recomendado)

Crie um repositório com apenas:
```
frontend.html
```

1. Acesse [vercel.com](https://vercel.com)
2. Clique em "Import Project"
3. Selecione seu repositório
4. Configure:
   - **Root Directory**: `.` (raiz)
5. Nas **Environment Variables**, adicione:
   ```
   NEXT_PUBLIC_API_URL = https://porto-itaqui-api.onrender.com
   ```
6. Deploy!

#### Opção B: Deploy com Next.js

Se quiser usar Next.js para servir melhor:

```bash
npx create-next-app@latest porto-itaqui-web
cd porto-itaqui-web
# Copie frontend.html para public/index.html
# Ajuste routes
vercel deploy
```

## 🔧 Configuração Local

### Instalação

```bash
# 1. Clone o repositório
git clone <seu-repo>
cd "Teoria das Filas - Desafio 4.0"

# 2. Crie ambiente virtual
python -m venv venv

# 3. Ative (Windows)
.\venv\Scripts\activate

# 4. Instale dependências
pip install -r requirements.txt
```

### Rodar Localmente

```bash
# Backend (porta 8000)
python main.py

# Frontend (abra no navegador)
# http://localhost:8000
```

A aplicação frontend é servida automaticamente pelo FastAPI na raiz (`/`).

## 📊 Características

### Modelo de Fila
- **M/M/4** — 4 servidores (berços) paralelos
- Chegadas Markovianas e serviços exponenciais

### Tipos de Navio
| Tipo | μ (h⁻¹) | Prioridade | Berços |
|------|--------|-----------|--------|
| Granéis | 10 | Normal (3) | B1, B4 |
| Contêineres | 8 | Normal (3) | B2, B4 |
| Combustíveis | 12 | Normal (3) | B3 (otim. B4) |
| Marinha/C.Viva | 6 | **Máxima (1)** | Todos |
| Cont. Refrigerado | 8 | **Alta (2)** | B2, B4 |

### Políticas de Sequenciamento

1. **FIFO** — Primeiro a Chegar, Primeiro a Sair
2. **Prioridade Não Preemptiva** — Classes 1→3, FIFO dentro da classe
3. **SJF** — Menor Serviço Primeiro
4. **LCFS** — Último a Chegar, Primeiro a Sair

### Otimizações Implementadas

- **Combustível B4**: Se houver 3+ navios de combustível na fila e B4 está ocioso, o sistema prioriza a alocação de um navio de combustível para B4

### Métricas (Teoria das Filas)

- **L** — Número médio de itens no sistema
- **Lq** — Número médio de itens na fila
- **W** — Tempo médio no sistema (horas)
- **Wq** — Tempo médio na fila (horas)
- **ρ** — Utilização dos servidores (%)
- **Atendidos** — Total de navios completados

## 📝 Estrutura de Arquivos

```
.
├── main.py               # Backend FastAPI + lógica de simulação
├── frontend.html         # UI (HTML + Tailwind CSS + JavaScript)
├── requirements.txt      # Dependências Python
├── Procfile              # Configuração Render
├── .gitignore            # Arquivos ignorados no Git
└── README.md             # Este arquivo
```

## 🔐 Variáveis de Ambiente

### Render (Backend)

Nenhuma configuração adicional obrigatória. Opcionais:

```
PORT=8000  # (padrão, configurado automaticamente pelo Render)
```

### Vercel (Frontend)

```
NEXT_PUBLIC_API_URL=https://porto-itaqui-api.onrender.com
```

## 🐛 Troubleshooting

### "Erro ao conectar à API"
- Verifique se o backend está rodando em Render
- Verifique o URL da API no `frontend.html`
- Ative CORS (já habilitado por padrão)

### "Página em branco no Vercel"
- Abra o DevTools (F12) e veja os logs do console
- Verifique se `NEXT_PUBLIC_API_URL` está correto

### "Erro 404 — Not Found"
- Certifique-se de que o arquivo `frontend.html` está na raiz do projeto

## 📧 Suporte

Para problemas com deploy:
- **Render**: [docs.render.com](https://docs.render.com)
- **Vercel**: [vercel.com/docs](https://vercel.com/docs)

---

**Desenvolvido para**: Teoria das Filas e Processos Estocásticos — UNDB 2026.1
