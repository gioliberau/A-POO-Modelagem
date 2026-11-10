/* Interface administrativa do recurso `banco`.
 * Usa a API REST já existente (GET/POST /banco, PUT/DELETE /banco/<id>)
 * com o cookie de sessão do navegador. Não há lógica de negócio aqui. */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var corpo = $("corpo"), avisos = $("avisos"), dlgForm = $("dlg-form"), dlgExc = $("dlg-excluir");
  var form = $("form"), editandoId = null, excluirId = null, ultimoFoco = null;
  var disciplinas = [];

  // ---------- API ----------
  function api(metodo, caminho, corpoJson) {
    var opts = { method: metodo, credentials: "same-origin", headers: { "Accept": "application/json" } };
    if (corpoJson !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(corpoJson);
    }
    return fetch(caminho, opts).then(function (r) {
      return r.text().then(function (t) {
        var dados = {};
        try { dados = t ? JSON.parse(t) : {}; } catch (e) { dados = {}; }
        if (r.status === 401) {
          window.location.href = "/portal?err=" + encodeURIComponent("Sessão expirada. Faça login novamente.");
        }
        return { status: r.status, ok: r.ok, dados: dados };
      });
    });
  }

  // ---------- mensagens ----------
  function aviso(tipo, texto) {
    var el = document.createElement("div");
    el.className = "aviso " + tipo;
    var span = document.createElement("span");
    span.textContent = texto;
    var fechar = document.createElement("button");
    fechar.type = "button"; fechar.className = "fechar"; fechar.setAttribute("aria-label", "Fechar");
    fechar.textContent = "×";
    fechar.onclick = function () { el.remove(); };
    el.appendChild(span); el.appendChild(fechar);
    avisos.innerHTML = "";
    avisos.appendChild(el);
    if (tipo === "ok") { setTimeout(function () { if (el.parentNode) el.remove(); }, 6000); }
  }

  function textoErro(dados, padrao) {
    var t = (dados && dados.erro) || padrao;
    if (dados && dados.campos) {
      t += " " + Object.keys(dados.campos).map(function (k) { return k + ": " + dados.campos[k]; }).join(" ");
    }
    return t;
  }

  // ---------- tabela ----------
  function td(rotulo, conteudo, classe) {
    var c = document.createElement("td");
    c.setAttribute("data-label", rotulo);
    if (classe) { c.className = classe; }
    if (conteudo instanceof Node) { c.appendChild(conteudo); } else { c.textContent = conteudo; }
    return c;
  }

  function botaoAcao(rotulo, classe, aoClicar) {
    var b = document.createElement("button");
    b.type = "button"; b.className = "btn btn-sm " + classe; b.textContent = rotulo;
    b.onclick = aoClicar;
    return b;
  }

  function desenhar() {
    corpo.innerHTML = "";
    disciplinas.forEach(function (d) {
      var tr = document.createElement("tr");
      tr.setAttribute("data-id", d.id);
      var forte = document.createElement("strong"); forte.textContent = d.codigo;
      var acoes = document.createElement("div"); acoes.className = "acoes";
      acoes.appendChild(botaoAcao("Editar", "btn-claro-borda", function (e) { abrirForm(d, e.currentTarget); }));
      acoes.appendChild(botaoAcao("Excluir", "btn-perigo-borda", function (e) { abrirExcluir(d, e.currentTarget); }));
      tr.appendChild(td("ID", String(d.id)));
      tr.appendChild(td("Código", forte));
      tr.appendChild(td("Nome", d.nome));
      tr.appendChild(td("Créditos", String(d.creditos)));
      tr.appendChild(td("Departamento", d.departamento));
      tr.appendChild(td("Curso", d.curso || "—"));
      tr.appendChild(td("Ações", acoes, "col-acoes"));
      corpo.appendChild(tr);
    });
    $("total").textContent = disciplinas.length;
    $("vazio").hidden = disciplinas.length > 0;
  }

  function carregar() {
    return api("GET", "/banco").then(function (r) {
      if (r.ok) { disciplinas = r.dados.disciplinas || []; desenhar(); }
      else { aviso("erro", textoErro(r.dados, "Não foi possível carregar a lista.")); }
    }).catch(function () { aviso("erro", "Falha de conexão com o servidor."); });
  }

  // ---------- formulário (cadastro / edição) ----------
  function limparErros() {
    $("form-erro").hidden = true; $("form-erro").textContent = "";
    Array.prototype.forEach.call(form.querySelectorAll(".erro-campo"), function (e) { e.textContent = ""; });
    Array.prototype.forEach.call(form.elements, function (e) { e.removeAttribute("aria-invalid"); });
  }

  function mostrarErrosCampos(campos) {
    var gerais = [];
    Object.keys(campos || {}).forEach(function (k) {
      var alvo = form.querySelector('[data-erro="' + k + '"]');
      if (alvo) { alvo.textContent = campos[k]; if (form.elements[k]) { form.elements[k].setAttribute("aria-invalid", "true"); } }
      else { gerais.push(campos[k]); }
    });
    return gerais;
  }

  function abrirForm(d, origem) {
    ultimoFoco = origem || null;
    editandoId = d ? d.id : null;
    limparErros();
    form.reset();
    $("form-titulo").textContent = d ? "Editar disciplina" : "Nova disciplina";
    $("btn-salvar").textContent = d ? "Salvar alterações" : "Cadastrar";
    if (d) {
      form.elements.codigo.value = d.codigo; form.elements.nome.value = d.nome;
      form.elements.creditos.value = d.creditos; form.elements.departamento.value = d.departamento;
      form.elements.curso.value = d.curso || "";
    }
    dlgForm.showModal();
    form.elements.codigo.focus();
  }

  function fechar(dlg) { if (dlg.open) { dlg.close(); } if (ultimoFoco) { ultimoFoco.focus(); } }

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    limparErros();
    var payload = {
      codigo: form.elements.codigo.value.trim(),
      nome: form.elements.nome.value.trim(),
      creditos: form.elements.creditos.value.trim() === "" ? null : Number(form.elements.creditos.value),
      departamento: form.elements.departamento.value.trim(),
      curso: form.elements.curso.value.trim()
    };
    var salvar = $("btn-salvar"); salvar.disabled = true;
    var req = editandoId === null ? api("POST", "/banco", payload) : api("PUT", "/banco/" + editandoId, payload);
    req.then(function (r) {
      if (r.ok) {
        fechar(dlgForm);
        aviso("ok", (r.dados.mensagem || "Operação concluída.") + (r.dados.disciplina ? " (" + r.dados.disciplina.codigo + ")" : ""));
        return carregar();
      }
      var gerais = mostrarErrosCampos(r.dados.campos);
      if (r.status === 409) { mostrarErrosCampos({ codigo: r.dados.erro }); }
      else if (r.status === 404) { fechar(dlgForm); aviso("erro", r.dados.erro || "Disciplina não encontrada."); return carregar(); }
      else if (r.status !== 400 || gerais.length) {
        var e = $("form-erro"); e.textContent = textoErro({ erro: r.dados.erro, campos: null }, "Erro ao salvar.") + " " + gerais.join(" ");
        e.hidden = false;
      }
    }).catch(function () {
      var e = $("form-erro"); e.textContent = "Falha de conexão com o servidor."; e.hidden = false;
    }).then(function () { salvar.disabled = false; });
  });

  // ---------- exclusão ----------
  function abrirExcluir(d, origem) {
    ultimoFoco = origem || null; excluirId = d.id;
    $("exc-texto").textContent = "Você vai excluir " + d.codigo + " — " + d.nome + ".";
    dlgExc.showModal();
    $("btn-exc-cancelar").focus();
  }

  $("form-excluir").addEventListener("submit", function (ev) {
    ev.preventDefault();
    var ok = $("btn-exc-ok"); ok.disabled = true;
    api("DELETE", "/banco/" + excluirId).then(function (r) {
      fechar(dlgExc);
      aviso(r.ok ? "ok" : "erro", r.ok ? (r.dados.mensagem || "Disciplina excluída.") : textoErro(r.dados, "Não foi possível excluir."));
      return carregar();
    }).catch(function () { fechar(dlgExc); aviso("erro", "Falha de conexão com o servidor."); })
      .then(function () { ok.disabled = false; });
  });

  // ---------- eventos gerais ----------
  $("btn-nova").onclick = function (e) { abrirForm(null, e.currentTarget); };
  $("btn-cancelar").onclick = function () { fechar(dlgForm); };
  $("btn-exc-cancelar").onclick = function () { fechar(dlgExc); };
  [dlgForm, dlgExc].forEach(function (dlg) {  // clique fora do cartão fecha
    dlg.addEventListener("click", function (e) { if (e.target === dlg) { fechar(dlg); } });
  });

  carregar();
})();
