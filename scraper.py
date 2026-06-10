import logging
import time
from datetime import datetime, timezone
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

import config

logger = logging.getLogger(__name__)

def setup_logging(log_filename: str = "scraper.log"):
    """Configura o sistema de logging do projeto."""
    handlers = []
    try:
        handlers.append(logging.FileHandler(log_filename, encoding='utf-8'))
    except PermissionError:
        # Em ambientes com restrição de escrita (como containers Docker),
        # ignoramos o arquivo de log e usamos apenas a saída padrão.
        pass
    handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

    if len(handlers) == 1:
        logging.getLogger(__name__).warning(
            "Permissão negada para gravar o arquivo de log %r. Logando apenas no terminal.",
            log_filename
        )

class YouTubeScraper:
    def __init__(self):
        """Inicializa o WebDriver utilizando webdriver-manager."""
        try:
            self.driver = self._init_driver()
        except Exception as e:
            logger.exception("Erro ao inicializar o WebDriver")
            raise RuntimeError("Falha ao inicializar o YouTubeScraper WebDriver") from e
        self.data = []

    def _init_driver(self):
        """Configura e retorna a instância do ChromeDriver."""
        logger.info("Inicializando Chrome WebDriver...")
        options = Options()
        if config.HEADLESS:
            options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--mute-audio')
        options.add_argument('--lang=pt-BR')
        options.add_argument('--window-size=1920,1080')
        
        # Verifica se estamos em ambiente Docker com chromium-driver do sistema instalado
        import os
        system_chromedriver = "/usr/bin/chromedriver"
        system_chromium = "/usr/bin/chromium"
        if not os.path.exists(system_chromium) and os.path.exists("/usr/bin/chromium-browser"):
            system_chromium = "/usr/bin/chromium-browser"
            
        if os.path.exists(system_chromedriver) and os.path.exists(system_chromium):
            logger.info(f"Usando Chromium ({system_chromium}) e ChromeDriver ({system_chromedriver}) do sistema...")
            options.binary_location = system_chromium
            service = Service(executable_path=system_chromedriver)
        else:
            logger.info("Usando webdriver-manager para gerenciar ChromeDriver...")
            service = Service(ChromeDriverManager().install())
            
        driver = webdriver.Chrome(service=service, options=options)
        driver.maximize_window()
        return driver

    def navigate_to_popular(self, channel_url):
        """
        Navega para a aba de vídeos do canal e seleciona ordenação por Popular/Em alta.
        Suporta dois layouts do YouTube:
          - Layout A: Tabs diretos (role="tab") com botões "Popular"/"Em alta"
          - Layout B: Dropdown (role="combobox") que abre menu com "Em alta"/"Popular"
        Retorna True em caso de sucesso, False caso contrário.
        """
        base_url = channel_url.rstrip('/')
        if not base_url.endswith('/videos'):
            base_url = f"{base_url}/videos"

        logger.info(f"Acessando URL de vídeos: {base_url}")
        try:
            self.driver.get(base_url)
            
            # Aguarda vídeos carregarem no DOM
            for attempt in range(15):
                time.sleep(2)
                count = self.driver.execute_script("""
                    return document.querySelectorAll('a[href*="/watch?v="]').length;
                """)
                if count and count > 0:
                    logger.info(f"Página carregada. {count} links de vídeo no DOM.")
                    break
                logger.info(f"Tentativa {attempt+1}/15: Aguardando vídeos carregarem...")
            else:
                logger.error(f"Timeout: nenhum vídeo encontrado após 30s em {base_url}")
                return False
            
            # Tenta selecionar "Popular" / "Em alta" via JavaScript
            clicked = self.driver.execute_script(r"""
                // ========== LAYOUT A: Tabs diretos (role="tab") ==========
                var tabs = document.querySelectorAll('button[role="tab"]');
                for (var i = 0; i < tabs.length; i++) {
                    var label = (tabs[i].getAttribute('aria-label') || '').toLowerCase();
                    var text = (tabs[i].textContent || '').trim().toLowerCase();
                    if (label === 'popular' || label === 'em alta' || label === 'populares'
                        || text === 'popular' || text === 'em alta' || text === 'populares') {
                        // Verifica se já está selecionado
                        if (tabs[i].getAttribute('aria-selected') === 'true') {
                            return 'already_selected';
                        }
                        tabs[i].click();
                        return 'tab_clicked';
                    }
                }
                
                // ========== LAYOUT B: Dropdown combobox ==========
                var combobox = document.querySelector('button[role="combobox"]');
                if (combobox) {
                    combobox.click();
                    return 'combobox_opened';
                }
                
                return 'not_found';
            """)
            
            logger.info(f"Resultado do clique: {clicked}")
            
            if clicked == 'combobox_opened':
                # Aguarda o menu dropdown aparecer e clica em "Em alta" / "Popular"
                time.sleep(1.5)
                menu_clicked = self.driver.execute_script(r"""
                    // Busca itens do menu dropdown
                    var menuItems = document.querySelectorAll(
                        'yt-list-item-view-model span.ytListItemViewModelTitle, ' +
                        'yt-list-item-view-model button'
                    );
                    for (var i = 0; i < menuItems.length; i++) {
                        var text = (menuItems[i].textContent || '').trim().toLowerCase();
                        if (text === 'em alta' || text === 'popular' || text === 'populares') {
                            // Clica no botão pai se for um span
                            var btn = menuItems[i].closest('button') || menuItems[i];
                            btn.click();
                            return 'menu_item_clicked';
                        }
                    }
                    
                    // Fallback: busca qualquer elemento visível com o texto
                    var allEls = document.querySelectorAll('span, button, div');
                    for (var i = 0; i < allEls.length; i++) {
                        var el = allEls[i];
                        var text = (el.textContent || '').trim().toLowerCase();
                        if ((text === 'em alta' || text === 'popular' || text === 'populares') 
                            && el.offsetParent !== null) {
                            el.click();
                            return 'fallback_clicked';
                        }
                    }
                    
                    return 'menu_not_found';
                """)
                logger.info(f"Resultado do menu dropdown: {menu_clicked}")
                
                if menu_clicked in ('menu_item_clicked', 'fallback_clicked'):
                    clicked = menu_clicked
                else:
                    logger.warning("Menu dropdown abriu mas não encontrou 'Em alta'/'Popular'.")
            
            # Se nenhum método UI funcionou, tenta fallback via URL
            if clicked == 'not_found':
                fallback_url = f"{base_url}?sort=p"
                logger.warning(f"UI não encontrou filtro. Fallback via URL: {fallback_url}")
                self.driver.get(fallback_url)
            
            # Aguarda a página recarregar após o clique
            if clicked in ('tab_clicked', 'menu_item_clicked', 'fallback_clicked', 'not_found'):
                time.sleep(3)
                # Espera os novos vídeos carregarem
                for attempt in range(10):
                    count = self.driver.execute_script("""
                        return document.querySelectorAll('.ytLockupViewModelHost').length;
                    """)
                    if count and count > 0:
                        logger.info(f"Vídeos populares carregados. {count} containers no DOM.")
                        break
                    time.sleep(1)
            
            return True
            
        except Exception:
            logger.exception(f"Erro ao navegar para {base_url!r}")
            return False

    def extract_videos(self, channel_url):
        """
        Extrai informações dos primeiros MAX_VIDEOS da página atual usando JavaScript
        para garantir compatibilidade com qualquer layout do YouTube.
        """
        try:
            # Extrai o nome do canal
            channel_name = self.driver.execute_script("""
                // Tenta múltiplos seletores para o nome do canal
                var selectors = [
                    'yt-dynamic-sizing-formatted-string#text',
                    'ytd-channel-name yt-formatted-string',
                    '#channel-name yt-formatted-string',
                    '#channel-header-container yt-formatted-string'
                ];
                for (var i = 0; i < selectors.length; i++) {
                    var el = document.querySelector(selectors[i]);
                    if (el && el.textContent.trim()) {
                        return el.textContent.trim();
                    }
                }
                return null;
            """)
            
            if not channel_name:
                channel_name = channel_url.split('@')[-1].split('/')[0]
            
            logger.info(f"Iniciando extração para o canal: {channel_name}")
            
            # Extrai vídeos usando JavaScript puro
            videos_data = self.driver.execute_script(r"""
                var results = [];
                var seen = {};
                
                // Busca os containers de vídeo (ytLockupViewModelHost)
                var containers = document.querySelectorAll('.ytLockupViewModelHost');
                
                for (var i = 0; i < containers.length; i++) {
                    var container = containers[i];
                    
                    // Extrai o video ID da classe do container (content-id-XXXX)
                    var classes = container.className || '';
                    var idMatch = classes.match(/content-id-([^\s]+)/);
                    if (!idMatch) continue;
                    var videoId = idMatch[1];
                    if (seen[videoId]) continue;
                    seen[videoId] = true;
                    
                    // Título: primeiro tenta h3[title], depois a.ytLockupMetadataViewModelTitle
                    var title = '';
                    var h3 = container.querySelector('h3[title]');
                    if (h3) {
                        title = h3.getAttribute('title');
                    }
                    if (!title) {
                        var titleLink = container.querySelector('a.ytLockupMetadataViewModelTitle');
                        if (titleLink) {
                            title = titleLink.textContent.trim();
                        }
                    }
                    if (!title || title.length < 3) continue;
                    
                    // URL do vídeo
                    var url = 'https://www.youtube.com/watch?v=' + videoId;
                    
                    // Visualizações: busca span com aria-label ou textContent contendo "view" ou "visualiza"
                    var views = 'N/A';
                    
                    // 1. Tenta pegar via textContent (novo layout do YT)
                    var allSpans = container.querySelectorAll('span.ytContentMetadataViewModelMetadataText, span.inline-metadata-item, span.ytd-video-meta-block');
                    for (var j = 0; j < allSpans.length; j++) {
                        var text = (allSpans[j].textContent || '').toLowerCase();
                        if (text.includes('view') || text.includes('visualiza')) {
                            views = allSpans[j].textContent.trim().replace(/\u00A0/g, ' '); // Substitui &nbsp; por espaço normal
                            break;
                        }
                    }
                    
                    // 2. Se não encontrou, tenta fallback no aria-label antigo
                    if (views === 'N/A') {
                        var metaSpans = container.querySelectorAll('span[aria-label]');
                        for (var j = 0; j < metaSpans.length; j++) {
                            var label = (metaSpans[j].getAttribute('aria-label') || '').toLowerCase();
                            if (label.includes('view') || label.includes('visualiza')) {
                                views = metaSpans[j].getAttribute('aria-label');
                                break;
                            }
                        }
                    }
                    
                    results.push({
                        titulo: title,
                        url_video: url,
                        visualizacoes: views
                    });
                }
                
                return results;
            """)
            
            if not videos_data:
                logger.warning(f"Nenhum vídeo extraído para {channel_name}.")
                return
            
            videos_collected = 0
            for video in videos_data:
                if videos_collected >= config.MAX_VIDEOS:
                    break
                
                self.data.append({
                    "canal": channel_name,
                    "titulo": video["titulo"],
                    "url_video": video["url_video"],
                    "visualizacoes": video["visualizacoes"],
                    "data_coleta": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
                })
                videos_collected += 1
                    
            logger.info(f"[{videos_collected}/{config.MAX_VIDEOS}] vídeos coletados com sucesso do canal {channel_name!r}.")
            
        except Exception:
            logger.exception(f"Erro grave na extração de vídeos para o canal {channel_name!r}")

    def export_data(self):
        """
        Converte os dados em memória para um DataFrame do pandas e exporta para CSV e Excel.
        """
        if not self.data:
            logger.warning("Nenhum dado coletado para exportar.")
            return
            
        logger.info("Iniciando exportação dos dados coletados...")
        df = pd.DataFrame(self.data)
        
        # Exporta para CSV
        try:
            df.to_csv("videos_em_alta.csv", index=False, encoding='utf-8-sig')
            logger.info("Arquivo 'videos_em_alta.csv' gerado com sucesso!")
        except Exception:
            logger.exception("Erro ao salvar CSV")
            
        # Exporta para Excel
        try:
            df.to_excel("videos_em_alta.xlsx", index=False, engine='openpyxl')
            logger.info("Arquivo 'videos_em_alta.xlsx' gerado com sucesso!")
        except Exception:
            logger.exception("Erro ao salvar Excel")

    def close(self):
        """Encerra a sessão do WebDriver."""
        if self.driver:
            logger.info("Encerrando o navegador e limpando processos...")
            self.driver.quit()
