# 🚀 Guia Completo de Deploy — Render + Vercel

## Visão Geral

Este guia detalha como fazer deploy da aplicação em dois serviços:

- **Backend** (FastAPI): **Render** (gratuito)
- **Frontend** (HTML + Tailwind): **Vercel** (gratuito)

---

## PARTE 1: Preparação no GitHub

### 1.1 Crie um repositório

```bash
# No seu projeto local
git init
git add .
git commit -m "Versão inicial — Simulador Porto Itaqui"
git branch -M main
git remote add origin https://github.com/seu-usuario/seu-repo.git
git push -u origin main
```

✅ Todos os arquivos (main.py, frontend.html, requirements.txt, Procfile, .gitignore) devem estar no repositório.

---

## PARTE 2: Deploy do Backend no Render

### 2.1 Acesse Render

1. Vá para [render.com](https://render.com)
2. Clique em **"Sign Up"** (ou faça login se já tem conta)
3. Escolha **"GitHub"** como método de autenticação
4. Autorize o Render a acessar seus repositórios

### 2.2 Crie um Web Service

1. No painel do Render, clique em **"New +"** (canto superior direito)
2. Selecione **"Web Service"**
3. Escolha seu repositório GitHub com o projeto

### 2.3 Configure o Web Service

Preencha os campos conforme abaixo:

| Campo | Valor |
|-------|-------|
| **Name** | `porto-itaqui-api` |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python main.py` |
| **Instance Type** | Free (gratuito) |
| **Auto-deploy** | Ativado (deploy automático ao fazer push) |

### 2.4 Deploy

1. Clique em **"Create Web Service"**
2. O Render fará:
   - ✅ Clonar o repositório
   - ✅ Instalar dependências
   - ✅ Iniciar o servidor

3. Aguarde até ver:
   ```
   ✓ Your service is live!
   ```

### 2.5 Obtenha a URL da API

Na página do seu Web Service, copie a URL pública (ex: `https://porto-itaqui-api-xyz.onrender.com`).

---

## PARTE 3: Deploy do Frontend no Vercel

### Opção A: Deploy direto do arquivo HTML (⭐ Mais fácil)

#### 3A.1 Crie um repositório separado (opcional, mas recomendado)

```bash
mkdir porto-itaqui-frontend
cd porto-itaqui-frontend
git init
# Copie apenas o frontend.html para aqui
cp ../frontend.html ./index.html
git add .
git commit -m "Frontend — Simulador Porto Itaqui"
git remote add origin https://github.com/seu-usuario/porto-itaqui-frontend.git
git push -u origin main
```

#### 3A.2 Deploy no Vercel

1. Acesse [vercel.com](https://vercel.com)
2. Clique em **"Import Project"**
3. Selecione **"Import Git Repository"**
4. Cole a URL do seu repositório frontend
5. Clique em **"Import"**

#### 3A.3 Configure variáveis de ambiente

Na página de configuração do projeto:

1. Clique em **"Environment Variables"**
2. Adicione:
   ```
   NEXT_PUBLIC_API_URL = https://porto-itaqui-api-xyz.onrender.com
   ```
   (Substitua `porto-itaqui-api-xyz` pelo seu domínio Render)

3. Clique em **"Deploy"**

#### 3A.4 Acesse seu site

Vercel fornecerá um URL como `https://porto-itaqui-frontend.vercel.app`

---

### Opção B: Deploy com Next.js (Mais profissional, opcional)

Se quiser um projeto mais robusto com Next.js:

#### 3B.1 Crie um projeto Next.js

```bash
npx create-next-app@latest porto-itaqui-web
cd porto-itaqui-web
```

#### 3B.2 Configure o frontend.html

No arquivo `pages/index.js`:

```javascript
export default function Home() {
  const [state, setState] = useState(null);

  useEffect(() => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    fetch(`${API_URL}/state`)
      .then(r => r.json())
      .then(setState);
  }, []);

  return <iframe src={`${process.env.NEXT_PUBLIC_API_URL}`} style={{width: '100vw', height: '100vh'}} />;
}
```

Ou ainda mais simples: apenas sirva o `frontend.html` na pasta `public/`.

#### 3B.3 Deploy

```bash
git add .
git commit -m "Next.js - Porto Itaqui"
git push origin main
```

No Vercel, repita os passos de importação e adicione a variável `NEXT_PUBLIC_API_URL`.

---

## ✅ Verificação de Deploy

### 1. Teste o Backend

```bash
curl https://seu-backend.onrender.com/state
```

Deve retornar JSON com o estado da simulação.

### 2. Teste o Frontend

Abra `https://seu-frontend.vercel.app` no navegador.

Você deve ver:
- ✅ Interface carregada (tema azul oceano)
- ✅ Botões funcionando
- ✅ Relógio mostrando "T = 0.0h"
- ✅ Sem erros no console (F12)

### 3. Teste interação

- Clique em **"Cenário Demo"**
- Adicione um navio manualmente
- Clique em **"+1h"** para avançar o tempo

---

## 🔄 Atualizações Futuras

### Atualizar Backend

```bash
# Faça mudanças em main.py
git add main.py
git commit -m "Melhorias no simulador"
git push origin main
```

Render fará redeploy automaticamente! 🚀

### Atualizar Frontend

```bash
# Faça mudanças em frontend.html
git add frontend.html
git commit -m "Melhorias na UI"
git push origin main
```

Vercel fará redeploy automaticamente! 🚀

---

## 🆘 Troubleshooting

### Erro: "Failed to connect to API"

**Causa**: Frontend não consegue acessar o backend.

**Solução**:
1. Verifique se o URL do Render está correto em `NEXT_PUBLIC_API_URL`
2. Verifique se o backend está rodando (status "live" no Render)
3. Tente acessar `https://seu-backend.onrender.com/state` direto

### Erro: "CORS error"

**Causa**: Problema de origem cruzada.

**Solução**: O backend já tem CORS configurado. Se persiste:

Em `main.py`, modifique:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ← Permite todas as origens
    allow_methods=["*"],
    allow_headers=["*"]
)
```

### Frontend em branco/vazio

**Causa**: Arquivo HTML não está sendo servido corretamente.

**Solução**:
- No Vercel, certifique-se de que `frontend.html` está como `index.html` ou na raiz
- Verifique os logs no console (F12)

### Vercel: "Cannot find module 'next'"

**Causa**: Você seguiu a Opção B mas não instalou Next.js.

**Solução**:
```bash
npm install next react react-dom
npm run build
npm run start
```

---

## 📊 Limite de Recursos (Gratuito)

| Serviço | Limite |
|---------|--------|
| **Render** | 750h/mês de web service (rodando 24/7) |
| **Vercel** | Deploy ilimitado, 100GB/mês de bandwidthgoogle |

Para uso educacional, ambos são **totalmente gratuitos e suficientes**.

---

## 🎯 Próximos Passos

1. ✅ Deploy do Backend
2. ✅ Deploy do Frontend
3. 🔜 Customizar domínios (opcional)
4. 🔜 Adicionar CI/CD
5. 🔜 Monitoramento

---

**Dúvidas?** Consulte:
- [Render Docs](https://docs.render.com)
- [Vercel Docs](https://vercel.com/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
