<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Banco de Disciplinas — UnB FCTE</title>
  <link rel="icon" href="/static/img/logo-unb-fcte.png">
  <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
<header class="topo">
  <div class="topo-inner">
    <a class="marca" href="/banco?formato=html">
      <img src="/static/img/logo-unb-fcte.png" alt="UnB | FCTE">
    </a>
    <div class="usuario">
      <span class="usuario-nome">Olá, {{user['nome']}}</span>
      <form method="post" action="/portal/logout">
        <button type="submit" class="btn btn-claro">Sair</button>
      </form>
    </div>
  </div>
</header>

<main class="conteudo">
  <div class="titulo-linha">
    <div>
      <h1>Banco de Disciplinas</h1>
      <p class="sub"><span id="total">{{len(disciplinas)}}</span> disciplina(s) cadastrada(s)</p>
    </div>
    <button type="button" class="btn btn-primario" id="btn-nova">+ Nova disciplina</button>
  </div>

  <div id="avisos" class="avisos" role="status" aria-live="polite"></div>

  <div class="tabela-wrap">
    <table id="tabela">
      <thead>
        <tr>
          <th>ID</th><th>Código</th><th>Nome</th><th>Créditos</th>
          <th>Departamento</th><th>Curso</th><th class="col-acoes">Ações</th>
        </tr>
      </thead>
      <tbody id="corpo">
        % for d in disciplinas:
        <tr data-id="{{d['id']}}">
          <td data-label="ID">{{d['id']}}</td>
          <td data-label="Código"><strong>{{d['codigo']}}</strong></td>
          <td data-label="Nome">{{d['nome']}}</td>
          <td data-label="Créditos">{{d['creditos']}}</td>
          <td data-label="Departamento">{{d['departamento']}}</td>
          <td data-label="Curso">{{d['curso']}}</td>
          <td data-label="Ações" class="col-acoes"></td>
        </tr>
        % end
      </tbody>
    </table>
    <p id="vazio" class="vazio" {{!'hidden' if disciplinas else ''}}>Nenhuma disciplina cadastrada ainda. Clique em “+ Nova disciplina”.</p>
  </div>
  <noscript><p class="aviso erro">Ative o JavaScript para cadastrar, editar e excluir pelo navegador.</p></noscript>
</main>

<footer class="rodape">Universidade de Brasília — Faculdade de Ciências e Tecnologias em Engenharia (FCTE)</footer>

<!-- Formulário de cadastro / edição -->
<dialog id="dlg-form" aria-labelledby="form-titulo">
  <form id="form" novalidate>
    <h2 id="form-titulo">Nova disciplina</h2>
    <p id="form-erro" class="aviso erro" hidden></p>

    <label for="f-codigo">Código <span class="obrig">*</span></label>
    <input id="f-codigo" name="codigo" maxlength="12" autocomplete="off" required placeholder="Ex.: ABC0001">
    <small class="dica">3 a 12 letras ou números.</small>
    <small class="erro-campo" data-erro="codigo"></small>

    <label for="f-nome">Nome <span class="obrig">*</span></label>
    <input id="f-nome" name="nome" maxlength="120" autocomplete="off" required placeholder="Ex.: Orientação a Objetos">
    <small class="erro-campo" data-erro="nome"></small>

    <div class="linha-2">
      <div>
        <label for="f-creditos">Créditos <span class="obrig">*</span></label>
        <input id="f-creditos" name="creditos" type="number" min="1" max="30" step="1" inputmode="numeric" required placeholder="1 a 30">
        <small class="erro-campo" data-erro="creditos"></small>
      </div>
      <div>
        <label for="f-departamento">Departamento <span class="obrig">*</span></label>
        <input id="f-departamento" name="departamento" maxlength="100" autocomplete="off" required>
        <small class="erro-campo" data-erro="departamento"></small>
      </div>
    </div>

    <label for="f-curso">Curso <span class="opc">(opcional)</span></label>
    <input id="f-curso" name="curso" maxlength="100" autocomplete="off">
    <small class="erro-campo" data-erro="curso"></small>

    <div class="botoes">
      <button type="button" class="btn btn-claro-borda" id="btn-cancelar">Cancelar</button>
      <button type="submit" class="btn btn-primario" id="btn-salvar">Salvar</button>
    </div>
  </form>
</dialog>

<!-- Confirmação de exclusão -->
<dialog id="dlg-excluir" aria-labelledby="exc-titulo">
  <form method="dialog" id="form-excluir">
    <h2 id="exc-titulo">Excluir disciplina?</h2>
    <p id="exc-texto"></p>
    <p class="dica">Esta ação não pode ser desfeita.</p>
    <div class="botoes">
      <button type="button" class="btn btn-claro-borda" id="btn-exc-cancelar">Cancelar</button>
      <button type="submit" class="btn btn-perigo" id="btn-exc-ok">Excluir</button>
    </div>
  </form>
</dialog>

<script src="/static/js/banco.js"></script>
</body>
</html>
