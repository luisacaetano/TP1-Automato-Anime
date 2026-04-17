"""
TP1 - Automato Finito Aplicado em Jogos
Jogo de Batalha: Knight vs Big Demon

Maquina de Moore - Acoes associadas aos estados

Controles:
  Jogador 1 (Knight):    W/A/S/D + J (atacar) | Especial: S, S, J
  Jogador 2 (Big Demon): Setas + N (atacar)   | Especial: Baixo, Baixo, N
"""

import pygame
import os
from enum import Enum
from typing import Dict, List, Optional


# ============================================================================
# ESTADOS DO AUTOMATO FINITO
# ============================================================================
class Estado(Enum):
    """
    Estados do Automato Finito (Maquina de Moore)
    Cada estado representa uma acao/animacao do personagem
    """
    IDLE = "parado"         # Estado inicial - personagem parado
    ANDANDO = "andando"     # Personagem se movendo
    PULANDO = "pulando"     # Personagem no ar
    ATACANDO = "atacando"   # Ataque normal
    ESPECIAL = "especial"   # Golpe especial (combo)
    DANO = "dano"           # Personagem levou dano


# ============================================================================
# AUTOMATO FINITO (MAQUINA DE MOORE)
# ============================================================================
class Automato:
    """
    Automato Finito Deterministico - Maquina de Moore

    M = (Q, Sigma, delta, q0, lambda)
    - Q: Conjunto de estados {PARADO, ANDANDO, PULANDO, ATACANDO, ESPECIAL, DANO}
    - Sigma: Alfabeto de entrada {esquerda, direita, cima, ataque, especial}
    - delta: Funcao de transicao
    - q0: Estado inicial (PARADO)
    - lambda: Funcao de saida (animacao associada ao estado)
    """

    def __init__(self, nome: str):
        self.nome = nome
        self.estado_atual = Estado.IDLE

    def transicao(self, entrada: Optional[str]) -> Estado:
        """
        Funcao de transicao delta(estado_atual, entrada) -> proximo_estado
        """
        # Estados temporarios nao aceitam novas transicoes
        if self.estado_atual in [Estado.ATACANDO, Estado.ESPECIAL, Estado.DANO]:
            return self.estado_atual

        # Tabela de transicoes
        if entrada in ["esquerda", "direita"]:
            self.estado_atual = Estado.ANDANDO
        elif entrada == "cima":
            self.estado_atual = Estado.PULANDO
        elif entrada == "ataque":
            self.estado_atual = Estado.ATACANDO
        elif entrada == "especial":
            self.estado_atual = Estado.ESPECIAL
        elif entrada is None:
            self.estado_atual = Estado.IDLE

        return self.estado_atual

    def forcar_estado(self, estado: Estado):
        """Forca mudanca de estado (usado para dano e timeout)"""
        self.estado_atual = estado

    def reset(self):
        """Reseta automato ao estado inicial"""
        self.estado_atual = Estado.IDLE


# ============================================================================
# DETECTOR DE COMBO
# ============================================================================
class DetectorCombo:
    """
    Detecta sequencia de teclas para ativar golpe especial
    Combo: Baixo + Baixo + Ataque = ESPECIAL!
    """

    def __init__(self):
        self.baixo_count = 0    # Contador de vezes que pressionou baixo
        self.timer = 0          # Timer para resetar o combo
        self.TIMEOUT = 60       # 1 segundo para completar o combo (60 frames)

    def adicionar_input(self, entrada: str) -> bool:
        """
        Adiciona input ao combo e verifica se ativou
        Retorna True se o combo foi completado
        """
        # Reseta se passou muito tempo
        if self.timer <= 0:
            self.baixo_count = 0
        self.timer = self.TIMEOUT

        # Contabiliza "baixo"
        if entrada == "baixo":
            self.baixo_count += 1
            return False

        # Verifica se completou o combo (2x baixo + ataque)
        if entrada == "ataque" and self.baixo_count >= 2:
            self.baixo_count = 0
            return True  # COMBO ATIVADO!

        if entrada == "ataque":
            self.baixo_count = 0
        return False

    def atualizar(self):
        """Atualiza timer do combo"""
        if self.timer > 0:
            self.timer -= 1
        else:
            self.baixo_count = 0


# ============================================================================
# PERSONAGEM
# ============================================================================
class Personagem:
    """
    Personagem controlado por um Automato de Moore
    A animacao exibida depende do estado atual do automato
    """

    def __init__(self, nome: str, x: int, y: int, sprites_prefix: str,
                 pasta_sprites: str, escala: int = 96, virado_esquerda: bool = False):
        self.nome = nome
        self.x = x
        self.y = y
        self.y_base = y         # Posicao do chao
        self.pasta = pasta_sprites
        self.prefix = sprites_prefix
        self.escala = escala
        self.virado_esquerda = virado_esquerda

        # Automato que controla este personagem
        self.automato = Automato(nome)

        # Detector de combo especial
        self.combo = DetectorCombo()

        # Sistema de vida
        self.vida_max = 100
        self.vida = self.vida_max

        # Fisica do personagem
        self.velocidade = 6
        self.vel_y = 0
        self.no_chao = True
        self.gravidade = 0.8
        self.forca_pulo = -14

        # Sistema de animacao
        self.sprites: Dict[str, List[pygame.Surface]] = {}
        self.frame_atual = 0
        self.tempo_frame = 0
        self.velocidade_anim = 10   # Frames de jogo por frame de animacao

        # Timers de acoes
        self.acao_timer = 0         # Duracao da acao atual
        self.invencivel_timer = 0   # Invencibilidade apos dano
        self.atacando = False
        self.especial_ativo = False

        # Carrega sprites do personagem
        self._carregar_sprites()

    def _carregar_sprites(self):
        """Carrega todos os frames de animacao do personagem"""
        animacoes = {
            "idle": f"{self.prefix}_idle_anim",  # Parado
            "run": f"{self.prefix}_run_anim"     # Correndo
        }

        for nome_anim, prefixo in animacoes.items():
            frames = []
            i = 0
            # Carrega todos os frames (f0, f1, f2...)
            while True:
                caminho = os.path.join(self.pasta, f"{prefixo}_f{i}.png")
                if os.path.exists(caminho):
                    img = pygame.image.load(caminho).convert_alpha()
                    # Escala mantendo proporcao
                    w, h = img.get_size()
                    ratio = self.escala / max(w, h)
                    img = pygame.transform.scale(img, (int(w * ratio), int(h * ratio)))
                    frames.append(img)
                    i += 1
                else:
                    break
            if frames:
                self.sprites[nome_anim] = frames

        # Animacao de hit (ataque/dano)
        caminho_hit = os.path.join(self.pasta, f"{self.prefix}_hit_anim_f0.png")
        if os.path.exists(caminho_hit):
            img = pygame.image.load(caminho_hit).convert_alpha()
            w, h = img.get_size()
            ratio = self.escala / max(w, h)
            img = pygame.transform.scale(img, (int(w * ratio), int(h * ratio)))
            self.sprites["hit"] = [img]
        elif "idle" in self.sprites:
            self.sprites["hit"] = self.sprites["idle"][:1]

    def get_animacao_atual(self) -> str:
        """Retorna qual animacao usar baseado no estado do automato"""
        estado = self.automato.estado_atual
        if estado == Estado.IDLE:
            return "idle"
        elif estado == Estado.ANDANDO:
            return "run"
        elif estado == Estado.PULANDO:
            return "run"
        elif estado in [Estado.ATACANDO, Estado.ESPECIAL, Estado.DANO]:
            return "hit"
        return "idle"

    def processar_input(self, teclas: dict):
        """
        Processa entrada do jogador e atualiza automato

        teclas: dicionario com estado das teclas
            - esquerda, direita, cima: bool (tecla pressionada)
            - baixo_press, ataque_press: bool (tecla acabou de ser pressionada)
        """
        self.combo.atualizar()

        # Nao processa input durante acoes
        if self.acao_timer > 0:
            return

        entrada = None

        # Movimento
        if teclas.get("esquerda"):
            entrada = "esquerda"
            self.x -= self.velocidade
            self.virado_esquerda = True
        elif teclas.get("direita"):
            entrada = "direita"
            self.x += self.velocidade
            self.virado_esquerda = False
        elif teclas.get("cima") and self.no_chao:
            entrada = "cima"
            self.vel_y = self.forca_pulo
            self.no_chao = False

        # Input de baixo (para combo)
        if teclas.get("baixo_press"):
            self.combo.adicionar_input("baixo")

        # Ataque
        if teclas.get("ataque_press"):
            if self.combo.adicionar_input("ataque"):
                # Combo especial ativado!
                entrada = "especial"
                self.acao_timer = 50
                self.especial_ativo = True
                self.atacando = True
            else:
                # Ataque normal
                entrada = "ataque"
                self.acao_timer = 25
                self.atacando = True

        # Aplica transicao no automato
        if entrada:
            self.automato.transicao(entrada)
        elif self.no_chao and self.acao_timer == 0:
            self.automato.transicao(None)

    def atualizar(self, largura_tela: int):
        """Atualiza fisica e animacao do personagem"""
        # Gravidade
        if not self.no_chao:
            self.vel_y += self.gravidade
            self.y += self.vel_y
            if self.y >= self.y_base:
                self.y = self.y_base
                self.vel_y = 0
                self.no_chao = True

        # Limites da tela
        self.x = max(10, min(self.x, largura_tela - self.escala - 10))

        # Timer de acao
        if self.acao_timer > 0:
            self.acao_timer -= 1
            if self.acao_timer == 0:
                self.atacando = False
                self.especial_ativo = False
                self.automato.forcar_estado(Estado.IDLE)

        # Timer de invencibilidade
        if self.invencivel_timer > 0:
            self.invencivel_timer -= 1

        # Atualiza frame da animacao
        self.tempo_frame += 1
        if self.tempo_frame >= self.velocidade_anim:
            self.tempo_frame = 0
            anim = self.get_animacao_atual()
            if anim in self.sprites:
                self.frame_atual = (self.frame_atual + 1) % len(self.sprites[anim])

    def levar_dano(self, dano: int) -> bool:
        """Aplica dano ao personagem. Retorna True se aplicou."""
        if self.invencivel_timer > 0:
            return False
        self.vida = max(0, self.vida - dano)
        self.automato.forcar_estado(Estado.DANO)
        self.acao_timer = 20
        self.invencivel_timer = 40
        self.atacando = False
        self.especial_ativo = False
        return True

    def get_hitbox(self) -> pygame.Rect:
        """Retorna hitbox do personagem"""
        return pygame.Rect(self.x + 15, self.y + 10, self.escala - 30, self.escala - 15)

    def get_hitbox_ataque(self) -> Optional[pygame.Rect]:
        """Retorna hitbox do ataque (None se nao esta atacando)"""
        if not self.atacando:
            return None
        largura = 60 if self.especial_ativo else 40
        x = self.x - largura + 15 if self.virado_esquerda else self.x + self.escala - 15
        return pygame.Rect(x, self.y + 20, largura, self.escala - 40)

    def desenhar(self, tela: pygame.Surface):
        """Desenha personagem na tela"""
        anim = self.get_animacao_atual()
        if anim not in self.sprites:
            return

        frames = self.sprites[anim]
        frame = frames[self.frame_atual % len(frames)].copy()

        # Espelha se virado para esquerda
        if self.virado_esquerda:
            frame = pygame.transform.flip(frame, True, False)

        # Efeito de especial (brilho amarelo)
        if self.especial_ativo:
            frame.fill((100, 100, 0), special_flags=pygame.BLEND_ADD)

        # Efeito de dano (amarelado piscando)
        if self.invencivel_timer > 0:
            frame.fill((150, 80, 0), special_flags=pygame.BLEND_ADD)
            if (self.invencivel_timer // 4) % 2 == 0:
                frame.set_alpha(180)

        # Centraliza sprite
        x_draw = self.x + (self.escala - frame.get_width()) // 2
        y_draw = self.y + (self.escala - frame.get_height())
        tela.blit(frame, (x_draw, y_draw))

        # Efeito visual do especial
        if self.especial_ativo:
            self._desenhar_efeito_especial(tela)

    def _desenhar_efeito_especial(self, tela: pygame.Surface):
        """Desenha circulos de energia do golpe especial"""
        centro_x = self.x + self.escala // 2
        efeito_x = centro_x - 50 if self.virado_esquerda else centro_x + 50
        efeito_y = self.y + self.escala // 2

        tempo = pygame.time.get_ticks() // 50
        for i in range(3):
            raio = 20 + (tempo + i * 5) % 20
            alpha = 255 - raio * 5
            if alpha > 0:
                surf = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (255, 200, 50, alpha), (raio, raio), raio, 3)
                tela.blit(surf, (efeito_x - raio, efeito_y - raio))


# ============================================================================
# JOGO PRINCIPAL
# ============================================================================
class JogoBatalha:
    """
    Jogo de batalha: Knight vs Big Demon

    CONTROLES:
    ----------
    Jogador 1 (Knight):
        W - Pular
        A - Andar esquerda
        D - Andar direita
        J - Atacar
        Especial: S, S, J (baixo duas vezes + ataque)

    Jogador 2 (Big Demon):
        Seta Cima - Pular
        Seta Esquerda - Andar esquerda
        Seta Direita - Andar direita
        N - Atacar
        Especial: Baixo, Baixo, N

    Outros:
        R - Reiniciar partida
        ESC - Sair
    """

    def __init__(self):
        pygame.init()
        self.LARGURA = 900
        self.ALTURA = 500
        self.tela = pygame.display.set_mode((self.LARGURA, self.ALTURA))
        pygame.display.set_caption("TP1 - Automato Finito - Knight vs Big Demon")
        self.clock = pygame.time.Clock()
        self.FPS = 60

        # Carrega recursos
        self.pasta_sprites = os.path.join(os.path.dirname(__file__), "sprites")
        self.fundo = self._carregar_fundo()

        # Cria personagens
        CHAO_Y = 340
        self.jogador1 = Personagem("Knight", 150, CHAO_Y, "knight_f",
                                    self.pasta_sprites, escala=120)
        self.jogador2 = Personagem("Big Demon", 600, CHAO_Y - 30, "big_demon",
                                    self.pasta_sprites, escala=150, virado_esquerda=True)

        # Fontes
        self.fonte = pygame.font.Font(None, 36)
        self.fonte_pequena = pygame.font.Font(None, 28)
        self.fonte_grande = pygame.font.Font(None, 72)

        # Estado do jogo
        self.jogo_ativo = True
        self.vencedor = None

        # Flags de input (detecta quando tecla e pressionada)
        self.j1_ataque_press = False
        self.j1_baixo_press = False
        self.j2_ataque_press = False
        self.j2_baixo_press = False

        # Mostra diagrama no terminal
        self._mostrar_diagrama()

    def _carregar_fundo(self) -> pygame.Surface:
        """Carrega imagem de fundo"""
        caminho = os.path.join(self.pasta_sprites, "Fundo.png")
        if os.path.exists(caminho):
            img = pygame.image.load(caminho).convert()
            return pygame.transform.scale(img, (self.LARGURA, self.ALTURA))
        surf = pygame.Surface((self.LARGURA, self.ALTURA))
        surf.fill((30, 30, 50))
        return surf

    def _mostrar_diagrama(self):
        """Mostra diagrama do automato no terminal"""
        print("""
╔════════════════════════════════════════════════════════════════════╗
║              AUTOMATO FINITO - MAQUINA DE MOORE                    ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║                        ┌──────────┐                                ║
║           ┌───────────>│  PARADO  │<───────────┐                   ║
║           │            │   (q0)   │            │                   ║
║           │            └────┬─────┘            │                   ║
║           │                 │                  │                   ║
║       (timeout)    ┌────────┼────────┐     (timeout)               ║
║           │        │        │        │         │                   ║
║           │    esq/dir    cima    ataque       │                   ║
║           │        │        │        │         │                   ║
║           │        v        v        v         │                   ║
║      ┌────┴────┐ ┌──────┐ ┌────────┐ ┌────────┴───┐                ║
║      │ ANDANDO │ │PULANDO│ │ATACANDO│ │  ESPECIAL  │               ║
║      └─────────┘ └──────┘ └────────┘ │ (Baixo x2  │                ║
║                                      │ + Ataque)  │                ║
║                                      └────────────┘                ║
║                                                                    ║
╠════════════════════════════════════════════════════════════════════╣
║  CONTROLES:                                                        ║
║  Jogador 1 (Knight): W/A/S/D + J      | Especial: S, S, J          ║
║  Jogador 2 (Demon):  Setas + N        | Especial: Baixo x2 + N     ║
╚════════════════════════════════════════════════════════════════════╝
        """)

    def processar_eventos(self) -> bool:
        """Processa eventos do pygame. Retorna False para sair."""
        # Reseta flags de press
        self.j1_ataque_press = False
        self.j1_baixo_press = False
        self.j2_ataque_press = False
        self.j2_baixo_press = False

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    return False
                if evento.key == pygame.K_r:
                    self._reiniciar()
                # Jogador 1 (Knight): WASD + J
                if evento.key == pygame.K_j:
                    self.j1_ataque_press = True
                if evento.key == pygame.K_s:
                    self.j1_baixo_press = True
                # Jogador 2 (Big Demon): Setas + N
                if evento.key == pygame.K_n:
                    self.j2_ataque_press = True
                if evento.key == pygame.K_DOWN:
                    self.j2_baixo_press = True
        return True

    def _reiniciar(self):
        """Reinicia a partida"""
        self.jogador1.vida = self.jogador1.vida_max
        self.jogador2.vida = self.jogador2.vida_max
        self.jogador1.x = 150
        self.jogador2.x = 600
        self.jogador1.automato.reset()
        self.jogador2.automato.reset()
        self.jogador1.combo = DetectorCombo()
        self.jogador2.combo = DetectorCombo()
        self.jogo_ativo = True
        self.vencedor = None

    def atualizar(self):
        """Atualiza logica do jogo"""
        if not self.jogo_ativo:
            return

        teclas = pygame.key.get_pressed()

        # Jogador 1 (Knight): W/A/S/D + J
        self.jogador1.processar_input({
            "esquerda": teclas[pygame.K_a],
            "direita": teclas[pygame.K_d],
            "cima": teclas[pygame.K_w],
            "baixo_press": self.j1_baixo_press,
            "ataque_press": self.j1_ataque_press,
        })

        # Jogador 2 (Big Demon): Setas + N
        self.jogador2.processar_input({
            "esquerda": teclas[pygame.K_LEFT],
            "direita": teclas[pygame.K_RIGHT],
            "cima": teclas[pygame.K_UP],
            "baixo_press": self.j2_baixo_press,
            "ataque_press": self.j2_ataque_press,
        })

        # Atualiza personagens
        self.jogador1.atualizar(self.LARGURA)
        self.jogador2.atualizar(self.LARGURA)

        # Verifica colisoes de ataque
        self._verificar_colisoes()

        # Verifica fim de jogo
        if self.jogador1.vida <= 0:
            self.jogo_ativo = False
            self.vencedor = self.jogador2
        elif self.jogador2.vida <= 0:
            self.jogo_ativo = False
            self.vencedor = self.jogador1

    def _verificar_colisoes(self):
        """Verifica se ataques acertaram"""
        # Jogador 1 atacando Jogador 2
        hitbox1 = self.jogador1.get_hitbox_ataque()
        if hitbox1 and self.jogador1.atacando:
            if hitbox1.colliderect(self.jogador2.get_hitbox()):
                dano = 30 if self.jogador1.especial_ativo else 12
                if self.jogador2.levar_dano(dano):
                    self.jogador1.atacando = False

        # Jogador 2 atacando Jogador 1
        hitbox2 = self.jogador2.get_hitbox_ataque()
        if hitbox2 and self.jogador2.atacando:
            if hitbox2.colliderect(self.jogador1.get_hitbox()):
                dano = 30 if self.jogador2.especial_ativo else 12
                if self.jogador1.levar_dano(dano):
                    self.jogador2.atacando = False

    def desenhar(self):
        """Desenha todos os elementos na tela"""
        self.tela.blit(self.fundo, (0, 0))
        self.jogador1.desenhar(self.tela)
        self.jogador2.desenhar(self.tela)
        self._desenhar_interface()
        if not self.jogo_ativo and self.vencedor:
            self._desenhar_vitoria()

    def _desenhar_interface(self):
        """Desenha barras de vida e informacoes"""
        # Jogador 1 (esquerda)
        pygame.draw.rect(self.tela, (80, 80, 80), (20, 20, 250, 30))
        vida1 = int(250 * (self.jogador1.vida / self.jogador1.vida_max))
        cor1 = (50, 200, 50) if self.jogador1.vida > 30 else (200, 50, 50)
        pygame.draw.rect(self.tela, cor1, (20, 20, vida1, 30))
        pygame.draw.rect(self.tela, (255, 255, 255), (20, 20, 250, 30), 3)

        nome1 = self.fonte_pequena.render(f"{self.jogador1.nome} (WASD + J)", True, (255, 255, 255))
        self.tela.blit(nome1, (20, 55))
        estado1 = self.fonte_pequena.render(f"Estado: {self.jogador1.automato.estado_atual.value.upper()}", True, (200, 200, 100))
        self.tela.blit(estado1, (20, 78))

        # Jogador 2 (direita)
        pygame.draw.rect(self.tela, (80, 80, 80), (self.LARGURA - 270, 20, 250, 30))
        vida2 = int(250 * (self.jogador2.vida / self.jogador2.vida_max))
        cor2 = (200, 50, 50) if self.jogador2.vida > 30 else (100, 0, 0)
        pygame.draw.rect(self.tela, cor2, (self.LARGURA - 20 - vida2, 20, vida2, 30))
        pygame.draw.rect(self.tela, (255, 255, 255), (self.LARGURA - 270, 20, 250, 30), 3)

        nome2 = self.fonte_pequena.render(f"{self.jogador2.nome} (Setas + N)", True, (255, 255, 255))
        self.tela.blit(nome2, (self.LARGURA - 20 - nome2.get_width(), 55))
        estado2 = self.fonte_pequena.render(f"Estado: {self.jogador2.automato.estado_atual.value.upper()}", True, (200, 200, 100))
        self.tela.blit(estado2, (self.LARGURA - 20 - estado2.get_width(), 78))

        # VS no centro
        vs = self.fonte.render("VS", True, (255, 200, 0))
        self.tela.blit(vs, (self.LARGURA // 2 - vs.get_width() // 2, 25))

    def _desenhar_vitoria(self):
        """Desenha tela de vitoria"""
        overlay = pygame.Surface((self.LARGURA, self.ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.tela.blit(overlay, (0, 0))

        texto = self.fonte_grande.render(f"{self.vencedor.nome} VENCEU!", True, (255, 215, 0))
        self.tela.blit(texto, (self.LARGURA // 2 - texto.get_width() // 2, self.ALTURA // 2 - 40))

        reiniciar = self.fonte.render("Pressione R para jogar novamente", True, (255, 255, 255))
        self.tela.blit(reiniciar, (self.LARGURA // 2 - reiniciar.get_width() // 2, self.ALTURA // 2 + 30))

    def executar(self):
        """Loop principal do jogo"""
        while True:
            if not self.processar_eventos():
                break
            self.atualizar()
            self.desenhar()
            pygame.display.flip()
            self.clock.tick(self.FPS)
        pygame.quit()


# ============================================================================
# PONTO DE ENTRADA
# ============================================================================
if __name__ == "__main__":
    jogo = JogoBatalha()
    jogo.executar()
