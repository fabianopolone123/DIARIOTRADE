# VPS Context - 2026-06-25

Resumo do que foi feito no VPS `145.223.93.162`.

## Estado inicial

- Ubuntu 24.04.3 LTS, depois atualizado para 24.04.4 LTS.
- Nginx em produção com apps Django/Gunicorn no host.
- Firewall estava inativo.
- CUPS estava ativo e escutando em `631`.
- `sitemissao` estava com `DEBUG=True` e `ALLOWED_HOSTS=['*']`.
- Havia vários atalhos de deploy com nomes diferentes para o mesmo projeto.

## Limpeza de projetos

- Removido o projeto antigo `/var/www/site_missao`.
- Removido o projeto `/var/www/site_idiomas`.
- Removidos os atalhos globais antigos desses projetos.
- `site_missao` antigo não estava ligado a Nginx nem a um service systemd ativo.

## Deploys padronizados

Atalhos globais atuais:

- `pinhaljunior-deploy` -> `sitepinhal`
- `missaoandrewsc-deploy` -> `sitemissao`
- `inscricaoandrews-deploy` -> `site_inscricao`
- `fabianopolone-deploy` -> `polloniflow`
- `fabianopolone-orcamentoneevy-deploy` -> `site_samela_faculdade`
- `fabianopolone-mapa-deploy` -> `mapa`

Notas:

- Os scripts novos foram padronizados no estilo do deploy completo do `sitepinhal`.
- `site_idiomas` foi removido, então o antigo atalho foi excluído.
- `site_missao` antigo também foi removido.

## Segurança aplicada

- Firewall ativado com apenas:
  - `22/tcp`
  - `80/tcp`
  - `443/tcp`
- CUPS desativado.
- Porta `631` não ficou exposta.

## Django corrigido

- `sitemissao` foi ajustado para produção:
  - `DEBUG=False` via ambiente
  - `ALLOWED_HOSTS` restrito a `missaoandrewsc.com.br` e `www.missaoandrewsc.com.br`
  - `CSRF_TRUSTED_ORIGINS` configurado
- `manage.py check` passou no `sitemissao`.
- `site_inscricao` já estava com `DJANGO_DEBUG=False` e hosts definidos no service.

## Atualização do sistema

- Foi executado `apt update && apt upgrade -y`.
- O reboot foi feito.
- O kernel novo carregado passou a ser `6.8.0-124-generic`.
- Após o reboot:
  - sem serviços falhando
  - sem `reboot-required`
  - Nginx OK
  - firewall OK

## Domínios validados

- `pinhaljunior.com.br`
- `missaoandrewsc.com.br`
- `xn--inscriaoandrews-jmb.com.br`
- `fabianopolone.com.br`
- `fabianopolone.com.br/OrcamentoNeevy/`
- `fabianopolone.com.br/mapa/`

## Observação sobre economia do Codex

- Para uso diário, `5.4 mini` com `Reasoning: Low` foi a opção mais econômica discutida.

