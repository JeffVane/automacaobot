from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import random


# 🔥 Função robusta para encontrar elementos com vários seletores
def encontrar_elemento(driver, lista_xpaths):
    for xpath in lista_xpaths:
        try:
            return driver.find_element(By.XPATH, xpath)
        except:
            continue
    return None


# 🔥 Função de scroll inteligente
def scroll_ate_pegar_cards(driver, scroll_area, limite_desejado):
    tentativas = 0
    cards = []

    while tentativas < 50:
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_area)
        time.sleep(random.uniform(1.5, 2.5))

        cards = driver.find_elements(By.XPATH, '//a[contains(@href, "/place/")]')
        print(f"🔍 Cards carregados até agora: {len(cards)}")

        if len(cards) >= limite_desejado:
            print(f"🎯 Alcançado o limite desejado de {limite_desejado} cards.")
            break

        tentativas += 1

    if len(cards) == 0:
        print("⚠️ Nenhum card encontrado, tentando clicar manualmente no primeiro item da lista.")
        try:
            primeiro = driver.find_element(By.XPATH, '(//div[@role="article"])[1]')
            driver.execute_script("arguments[0].scrollIntoView(true);", primeiro)
            primeiro.click()
            time.sleep(4)
        except:
            print("❌ Não foi possível clicar no primeiro item.")

    return cards


# 🔥 Função principal
def buscar_dados_cards_maps(termo, limite=50, username=None, status_buscas=None):
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://www.google.com/")
    time.sleep(2)

    # Aceita cookies
    try:
        aceitar = driver.find_element(By.XPATH, "//button/div[contains(text(),'Aceitar')]")
        aceitar.click()
    except:
        pass

    # Pesquisa o termo
    barra = driver.find_element(By.NAME, "q")
    barra.send_keys(termo)
    barra.send_keys(Keys.ENTER)
    time.sleep(3)

    # Abre aba Maps
    try:
        aba_maps = driver.find_element(By.PARTIAL_LINK_TEXT, "Maps")
        aba_maps.click()
        time.sleep(random.uniform(6, 8))
    except Exception as e:
        print("❌ Erro ao clicar na aba Maps:", e)
        driver.quit()
        return []

    # Faz o scroll
    try:
        scroll_area = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]'))
        )

        cards = scroll_ate_pegar_cards(driver, scroll_area, limite)
        print(f"✅ Total de cards encontrados: {len(cards)}")

    except Exception as e:
        print("❌ Erro ao rolar:", e)
        driver.quit()
        return []

    resultados = []

    if status_buscas and username:
        status_buscas[username]['parciais'] = []

    # 🔍 Processa os cards
    for i, card in enumerate(cards[:limite]):
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", card)
            card.click()
            time.sleep(random.uniform(3.5, 5))

            nome = encontrar_elemento(driver, [
                '//h1[contains(@class, "DUwDvf")]',
                '//*[@id="QA0Szd"]//h1',
                '//h1'
            ])
            nome = nome.text if nome else "Não encontrado"

            endereco = encontrar_elemento(driver, [
                '//button[contains(@data-item-id, "address")]'
            ])
            endereco = endereco.text if endereco else "Não encontrado"

            telefone = encontrar_elemento(driver, [
                '//button[contains(@data-item-id, "phone")]'
            ])
            telefone = telefone.text if telefone else "Não encontrado"

            site = encontrar_elemento(driver, [
                '//a[contains(@data-item-id, "authority")]'
            ])
            site = site.get_attribute('href') if site else "Não encontrado"

            resultado = {
                "nome": nome,
                "telefone": telefone,
                "endereco": endereco,
                "site": site
            }

            resultados.append(resultado)

            if status_buscas and username:
                status_buscas[username]["parciais"].append({
                    "nome": nome,
                    "endereco": endereco
                })
                status_buscas[username]["mensagem"] = f"Vendo {nome}..."
                progresso = int(((i + 1) / limite) * 100)
                status_buscas[username]["progresso"] = min(progresso, 100)

        except Exception as e:
            print(f"❌ Erro ao processar card {i + 1}: {e}")
            continue

    driver.quit()
    return resultados
