================================================================================
              TP1 - AUTOMATO FINITO APLICADO EM JOGOS
                    Knight vs Big Demon
================================================================================

DESCRICAO
---------
Jogo de batalha onde dois personagens sao controlados por Automatos Finitos
(Maquina de Moore). Cada estado do automato corresponde a uma acao/animacao.


COMO EXECUTAR
-------------
1. Ative o ambiente virtual:
   source venv/bin/activate

2. Execute o jogo:
   python jogo_batalha.py


CONTROLES
---------
JOGADOR 1 (Knight):
  W - Pular
  A - Andar esquerda
  D - Andar direita
  J - Atacar
  Especial: S, S, J (baixo duas vezes + ataque)

JOGADOR 2 (Big Demon):
  Seta Cima  - Pular
  Seta Esq   - Andar esquerda
  Seta Dir   - Andar direita
  N          - Atacar
  Especial: Baixo, Baixo, N

OUTROS:
  R   - Reiniciar partida
  ESC - Sair


ESTADOS DO AUTOMATO
-------------------
- PARADO   (q0) - Estado inicial
- ANDANDO       - Personagem se movendo
- PULANDO       - Personagem no ar
- ATACANDO      - Ataque normal
- ESPECIAL      - Golpe especial (combo)
- DANO          - Personagem levou dano


ESTRUTURA DO PROJETO
--------------------
TP1-Automato-Anime/
  jogo_batalha.py   <- Codigo principal
  README.txt        <- Este arquivo
  sprites/          <- Sprites dos personagens
  venv/             <- Ambiente virtual Python


REQUISITOS
----------
- Python 3.8+
- Pygame


================================================================================
