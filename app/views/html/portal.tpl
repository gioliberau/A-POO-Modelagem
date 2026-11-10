<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Portal — Banco de Disciplinas UnB FCTE</title>
  <link rel="icon" href="/static/img/logo-unb-fcte.png">
  <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
<header class="topo"></header>
<main class="portal-wrap">
  <div class="portal-logo"><img src="/static/img/logo-unb-fcte.png" alt="UnB | FCTE"></div>
  <h1>Portal</h1>
  <p class="sub">Banco de Disciplinas — UnB FCTE</p>
  % if msg:
  <p class="aviso ok">{{msg}}</p>
  % end
  % if err:
  <p class="aviso erro">{{err}}</p>
  % end

  <section class="cartao">
    <h2>Entrar</h2>
    <form method="post" action="/portal/login">
      <label for="l-email">E-mail</label>
      <input id="l-email" type="email" name="email" required autocomplete="username">
      <label for="l-senha">Senha</label>
      <input id="l-senha" type="password" name="senha" required autocomplete="current-password">
      <button type="submit" class="btn btn-primario">Entrar</button>
    </form>
  </section>

  <section class="cartao">
    <h2>Criar conta</h2>
    <form method="post" action="/portal/cadastro">
      <label for="c-nome">Nome</label>
      <input id="c-nome" type="text" name="nome" required minlength="2" autocomplete="name">
      <label for="c-email">E-mail</label>
      <input id="c-email" type="email" name="email" required autocomplete="email">
      <label for="c-senha">Senha <span class="opc">(mínimo 8 caracteres)</span></label>
      <input id="c-senha" type="password" name="senha" required minlength="8" autocomplete="new-password">
      <button type="submit" class="btn btn-claro-borda">Cadastrar</button>
    </form>
  </section>
</main>
<footer class="rodape">Universidade de Brasília — Faculdade de Ciências e Tecnologias em Engenharia (FCTE)</footer>
</body>
</html>
