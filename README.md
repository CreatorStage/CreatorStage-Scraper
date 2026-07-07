# Extrator de Vídeos em Alta do YouTube 🚀

Este projeto é um script automatizado e robusto em Python utilizando **Selenium** e **pandas** para navegar em canais do YouTube, acessar a aba "Em Alta" (Popular) e extrair os vídeos mais relevantes, exportando os dados limpos para CSV e Excel.

## 📂 Estrutura do Projeto

* `config.py`: Variáveis de configuração como lista de canais, quantidade de vídeos e opção de rodar em headless.
* `scraper.py`: Classe principal (`YouTubeScraper`) que encapsula toda a lógica do WebDriver, navegação robusta, espera implícita e extração.
* `main.py`: Ponto de entrada do programa. Orquestra as chamadas com a barra de progresso do `tqdm`.
* `requirements.txt`: Dependências do projeto.
* `scraper.log`: Arquivo gerado automaticamente contendo todos os logs da execução.

## ⚙️ Pré-requisitos e Instalação

1. Certifique-se de ter o Python 3.11+ instalado.
2. (Recomendado) Crie um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou venv\Scripts\activate no Windows
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

*Nota: O Chrome WebDriver é gerenciado automaticamente pelo `webdriver-manager`, não sendo necessário baixar manualmente.*

## 🚀 Como Executar

1. Abra o arquivo `config.py` e edite a lista `CHANNELS` com as URLs dos canais desejados.
2. Configure `HEADLESS = True` (execução invisível) ou `False` (para ver o navegador trabalhando).
3. Execute o script principal:
   ```bash
   python main.py
   ```

## 🧩 Explicação dos Seletores Utilizados

O script foi projetado para ser resiliente a mudanças na UI do YouTube. Em vez de depender de posições absolutas ou classes aleatórias e instáveis, ele utiliza uma **camada de fallback** (várias opções testadas em ordem).

1. **Aba Vídeos:**
   * `//tp-yt-paper-tab[.//div[contains(text(), 'Vídeos') or contains(text(), 'Videos')]]`: Busca o componente da tab cujo texto interno contenha a palavra "Vídeos".
   * `//a[contains(@href, '/videos')]`: Uma abordagem clássica de href caso o elemento paper-tab seja alterado.
2. **Botão Em Alta (Filtro):**
   * `//yt-chip-cloud-chip-renderer[...]`: Seleciona o "chip" (botão oval) que o YouTube usa atualmente para filtros, checando o texto "Em alta" ou "Popular".
   * `//yt-formatted-string[@title='Em alta' ou @title='Popular']`: Uma alternativa pelo atributo "title" que o YouTube usa em strings customizadas.
3. **Container de Vídeo (`ytd-rich-grid-media`):**
   * Elemento pai que engloba um único vídeo completo na grade. É uma tag HTML customizada (Web Component) extremamente estável no YouTube há anos.
4. **Título do Vídeo (`a#video-title-link`):**
   * O ID `video-title-link` está presente na tag `<a>` que redireciona pro vídeo. 
5. **Visualizações (`span.inline-metadata-item.ytd-video-meta-block`):**
   * O container de metadados (`ytd-video-meta-block`) contém spans. Usamos list comprehension/loops para achar a span que contém a palavra "visualiza" ou "view", garantindo que não pegamos o timestamp por engano.

## 🤖 Modo Worker com Mensageria (RabbitMQ)

O extrator roda integrado de forma assíncrona ao ecossistema **CreatorsDeck** via RabbitMQ:
* **Script**: `worker.py` escuta a fila `youtube_scrape_queue`.
* **Fluxo**: Ao receber uma mensagem com a URL do canal do YouTube, o worker dispara a classe `YouTubeScraper`, raspa as sugestões de vídeos em alta, e as registra de volta no banco de dados chamando a API do backend local.

### Como Executar o Worker:
```bash
python worker.py
```

## 💡 Melhorias Futuras Recomendadas

* **Multithreading / Assincronismo:** Atualmente os canais são processados de forma sequencial. Usar bibliotecas concorrentes (ou múltiplas instâncias de Chrome) poderia acelerar se a lista for gigante.
* **Rotação de Proxies e User-Agents:** Para listas gigantescas de canais (centenas), o YouTube pode impor restrições (rate limit ou captchas). Adicionar Proxies rotativos evitaria bloqueios.
* **Integração com API Oficial do YouTube (Data API v3):** O Selenium é excelente para contornar limitações e raspar direto do front-end, porém se os canais desejados não precisarem de restrições de navegação complexa, a API do YouTube seria muito mais rápida.
* **Banco de Dados:** Em vez de exportar apenas para CSV/Excel, integrar com SQLite ou PostgreSQL via SQLAlchemy.

