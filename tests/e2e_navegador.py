"""Teste ponta a ponta no navegador (opcional; não roda no `unittest discover`).

Requer:  pip install playwright && playwright install chromium
Uso:     python route.py &            # servidor em http://127.0.0.1:8080
         python tests/e2e_navegador.py [BASE_URL] [PASTA_PARA_CAPTURAS]
"""
import os
import sys
import time

from playwright.sync_api import expect, sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080"
SHOTS = sys.argv[2] if len(sys.argv) > 2 else None
EMAIL = f"e2e{int(time.time())}@exemplo.com"
COD = f"E{int(time.time()) % 10**7}"
passos = []


def ok(msg):
    passos.append(msg)
    print("OK  ", msg)


def shot(page, nome):
    if SHOTS:
        os.makedirs(SHOTS, exist_ok=True)
        page.screenshot(path=os.path.join(SHOTS, nome + ".png"), full_page=True)


def preencher(page, codigo, nome, creditos, depto, curso=""):
    page.fill("#f-codigo", codigo)
    page.fill("#f-nome", nome)
    page.fill("#f-creditos", str(creditos))
    page.fill("#f-departamento", depto)
    page.fill("#f-curso", curso)


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    erros_js = []
    page.on("pageerror", lambda e: erros_js.append(str(e)))
    # respostas 4xx esperadas (409, 400, 401) também aparecem no console; ignorá-las
    page.on("console", lambda m: erros_js.append(m.text)
        if m.type == "error" and not m.text.startswith("Failed to load resource") else None)

    # acesso sem login
    page.goto(BASE + "/banco?formato=html")
    expect(page).to_have_url(f"{BASE}/portal?err=Fa%C3%A7a+login+para+acessar+o+banco.")
    expect(page.locator(".aviso.erro")).to_contain_text("Faça login")
    ok("banco sem login redireciona ao portal com aviso")
    shot(page, "1-portal")

    # cadastro + login pelo formulário
    page.fill("#c-nome", "Aluno E2E")
    page.fill("#c-email", EMAIL)
    page.fill("#c-senha", "senhaforte1")
    page.click("text=Cadastrar")
    expect(page.locator(".aviso.ok")).to_contain_text("Conta criada")
    page.fill("#l-email", EMAIL)
    page.fill("#l-senha", "senhaforte1")
    page.click("button:has-text('Entrar')")
    expect(page.locator("h1")).to_have_text("Banco de Disciplinas")
    expect(page.locator(".marca img")).to_be_visible()
    assert page.evaluate("document.querySelector('.marca img').naturalWidth") > 0, "logo não carregou"
    ok("cadastro e login pelo navegador; logo carregada")

    # lista vazia
    expect(page.locator("#vazio")).to_be_visible()
    shot(page, "2-vazio")

    # CREATE
    page.click("#btn-nova")
    expect(page.locator("#dlg-form")).to_be_visible()
    shot(page, "3-form")
    preencher(page, COD, "Orientação a Objetos", 4, "Exemplo", "Engenharia de Software")
    page.click("#btn-salvar")
    expect(page.locator(".aviso.ok")).to_contain_text("Disciplina cadastrada")
    expect(page.locator("#corpo tr")).to_have_count(1)
    expect(page.locator("#corpo")).to_contain_text(COD)
    expect(page.locator("#total")).to_have_text("1")
    ok("cadastro de disciplina com mensagem de sucesso e tabela atualizada")
    shot(page, "4-lista")

    # erro: código duplicado (409) e campos inválidos (400)
    page.click("#btn-nova")
    preencher(page, COD, "Outra", 4, "Exemplo")
    page.click("#btn-salvar")
    expect(page.locator('[data-erro="codigo"]')).to_contain_text("Já existe")
    expect(page.locator("#dlg-form")).to_be_visible()
    preencher(page, "!", "x", 99, "")
    page.click("#btn-salvar")
    expect(page.locator('[data-erro="creditos"]')).to_contain_text("entre 1 e 30")
    expect(page.locator('[data-erro="nome"]')).not_to_be_empty()
    shot(page, "5-erros")
    page.click("#btn-cancelar")
    expect(page.locator("#dlg-form")).not_to_be_visible()
    ok("erros de duplicidade e validação aparecem no formulário")

    # UPDATE
    page.click("#corpo tr >> text=Editar")
    expect(page.locator("#f-nome")).to_have_value("Orientação a Objetos")
    page.fill("#f-creditos", "6")
    page.click("#btn-salvar")
    expect(page.locator(".aviso.ok")).to_contain_text("Disciplina atualizada")
    expect(page.locator("#corpo tr").first).to_contain_text("6")
    ok("edição preenche o formulário e salva")

    # XSS: texto com HTML aparece como texto
    page.click("#btn-nova")
    preencher(page, "XSS" + COD[-4:], "<img src=x onerror=window.__x=1>", 2, "Exemplo")
    page.click("#btn-salvar")
    expect(page.locator(".aviso.ok")).to_be_visible()
    assert page.evaluate("window.__x") is None
    expect(page.locator("#corpo")).to_contain_text("<img src=x")
    ok("HTML digitado é mostrado como texto (sem injeção)")

    # DELETE: cancelar e confirmar
    page.locator("#corpo tr").nth(1).get_by_text("Excluir").click()
    expect(page.locator("#dlg-excluir")).to_be_visible()
    shot(page, "6-excluir")
    page.click("#btn-exc-cancelar")
    expect(page.locator("#corpo tr")).to_have_count(2)
    page.locator("#corpo tr").nth(1).get_by_text("Excluir").click()
    page.click("#btn-exc-ok")
    expect(page.locator(".aviso.ok")).to_contain_text("excluída")
    expect(page.locator("#corpo tr")).to_have_count(1)
    ok("exclusão pede confirmação; cancelar não exclui; confirmar exclui")

    # persistência: recarregar a página
    page.reload()
    expect(page.locator("#corpo tr")).to_have_count(1)
    expect(page.locator("#corpo")).to_contain_text(COD)
    ok("dados persistem após recarregar")

    # celular
    page.set_viewport_size({"width": 390, "height": 800})
    page.wait_for_timeout(150)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "rolagem horizontal no celular"
    shot(page, "7-celular")
    ok("layout de celular sem rolagem horizontal")

    # sessão encerrada: API devolve 401 e a página volta ao portal
    page.set_viewport_size({"width": 1280, "height": 800})
    page.context.clear_cookies()
    page.click("#btn-nova")
    preencher(page, "SEMSESSAO", "Sem sessão", 2, "Exemplo")
    page.click("#btn-salvar")
    page.wait_for_url(f"{BASE}/portal?err=*")
    expect(page.locator(".aviso.erro")).to_contain_text("Sessão expirada")
    ok("sessão inválida redireciona ao portal")

    # logout
    page.fill("#l-email", EMAIL)
    page.fill("#l-senha", "senhaforte1")
    page.click("button:has-text('Entrar')")
    page.click("button:has-text('Sair')")
    expect(page.locator(".aviso.ok")).to_contain_text("Sessão encerrada")
    ok("logout pelo botão Sair")

    assert not erros_js, f"erros de JavaScript no console: {erros_js}"
    ok("sem erros de JavaScript no console")
    browser.close()

print(f"\n{len(passos)} verificações passaram.")
