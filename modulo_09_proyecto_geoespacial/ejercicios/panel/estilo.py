"""Estilo de "sala de control": CSS propio y componentes HTML (cabecera, tarjetas, alertas…).

Todo lo visual del dashboard sale de aquí: el CSS global (fondo, paneles de
cristal, barra de navegación, animaciones de entrada), los componentes HTML
que dibujan las páginas y ``grafico``, que da a todos los gráficos de ECharts
el mismo aspecto.
"""

import base64
import copy
from datetime import datetime
from html import escape

import streamlit as st

from estaciones import escalas

CIAN = "#22D3EE"
VIOLETA = "#A78BFA"
VERDE = "#34D399"
ROJO = "#FF5050"
AMBAR = "#FBBF24"
ROSA = "#F472B6"
AZUL = "#60A5FA"

# Colores de las series cuando un gráfico no los fija (mismo orden que el tema)
PALETA = [CIAN, VIOLETA, VERDE, AMBAR, ROSA, AZUL, "#FB923C", "#94A3B8"]

CSS = """
<style>
/* ===================================================================== */
/*  Variables                                                             */
/* ===================================================================== */
:root {
  --sc-fondo: #060A14;
  --sc-panel: rgba(17, 26, 46, .72);
  --sc-panel-2: rgba(10, 16, 31, .78);
  --sc-borde: rgba(148, 163, 184, .13);
  --sc-borde-2: rgba(148, 163, 184, .22);
  --sc-cian: 34, 211, 238;
  --sc-violeta: 167, 139, 250;
  --sc-texto: #E2E8F0;
  --sc-tenue: #94A3B8;
  --sc-apagado: #64748B;
  --sc-mono: 'JetBrains Mono', ui-monospace, Consolas, monospace;
  --sc-titulos: 'Space Grotesk', Inter, sans-serif;
  --sc-sombra: 0 18px 40px -22px rgba(0, 0, 0, .85), 0 2px 6px -2px rgba(0, 0, 0, .4);
}

/* ===================================================================== */
/*  Animaciones                                                           */
/* ===================================================================== */
@keyframes sc-latido {
  0% { box-shadow: 0 0 0 0 rgba(52, 211, 153, .65); }
  70% { box-shadow: 0 0 0 9px rgba(52, 211, 153, 0); }
  100% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }
}
@keyframes sc-entrar {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: none; }
}
@keyframes sc-giro { to { transform: rotate(1turn); } }
@keyframes sc-brillo {
  0%, 100% { opacity: .55; }
  50% { opacity: 1; }
}
@keyframes sc-crecer { from { transform: scaleX(0); } to { transform: scaleX(1); } }

/* ===================================================================== */
/*  Fondo de la aplicación: auroras suaves y una rejilla de coordenadas  */
/* ===================================================================== */
.stApp {
  background:
    radial-gradient(1100px 620px at 12% -8%, rgba(34, 211, 238, .10), transparent 60%),
    radial-gradient(900px 600px at 105% 12%, rgba(167, 139, 250, .09), transparent 60%),
    radial-gradient(1000px 700px at 50% 120%, rgba(52, 211, 153, .06), transparent 60%),
    var(--sc-fondo) !important;
}
.stApp::before {
  content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image:
    linear-gradient(rgba(148, 163, 184, .045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, .045) 1px, transparent 1px);
  background-size: 56px 56px;
  -webkit-mask-image: radial-gradient(ellipse at 50% 30%, #000 20%, transparent 75%);
  mask-image: radial-gradient(ellipse at 50% 30%, #000 20%, transparent 75%);
}
[data-testid="stMain"], [data-testid="stSidebar"] { position: relative; z-index: 1; }
::selection { background: rgba(34, 211, 238, .35); color: #fff; }
* { scrollbar-width: thin; scrollbar-color: rgba(148, 163, 184, .28) transparent; }
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, .25); border-radius: 8px; }
::-webkit-scrollbar-track { background: transparent; }

/* ===================================================================== */
/*  Barra superior con la navegación                                      */
/* ===================================================================== */
[data-testid="stHeader"] {
  background: linear-gradient(180deg, rgba(6, 10, 20, .92), rgba(6, 10, 20, .62)) !important;
  backdrop-filter: blur(14px) saturate(140%); -webkit-backdrop-filter: blur(14px) saturate(140%);
  border-bottom: 1px solid var(--sc-borde);
}
[data-testid="stHeader"]::after {
  content: ""; position: absolute; left: 0; right: 0; bottom: -1px; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(34, 211, 238, .55) 30%,
                              rgba(167, 139, 250, .55) 70%, transparent);
  opacity: .6;
}
[data-testid="stTopNav"] { gap: 4px; }
[data-testid="stTopNavLink"] {
  border-radius: 999px !important; padding: 6px 14px !important;
  border: 1px solid transparent; transition: all .2s ease;
}
[data-testid="stTopNavLink"]:hover {
  background: rgba(148, 163, 184, .08) !important; border-color: var(--sc-borde);
}
[data-testid="stTopNavLink"][aria-current="page"] {
  background: linear-gradient(135deg, rgba(34, 211, 238, .18), rgba(167, 139, 250, .14)) !important;
  border-color: rgba(34, 211, 238, .45);
  box-shadow: 0 0 0 1px rgba(34, 211, 238, .08), 0 6px 20px -6px rgba(34, 211, 238, .45),
              inset 0 1px 0 rgba(255, 255, 255, .08);
}
[data-testid="stTopNavLink"][aria-current="page"] p { color: #F8FAFC !important; font-weight: 600; }
[data-testid="stTopNavLink"][aria-current="page"] [data-testid="stIconMaterial"] {
  color: #22D3EE !important; filter: drop-shadow(0 0 6px rgba(34, 211, 238, .8));
}
[data-testid="stAppDeployButton"] { display: none !important; }

/* ===================================================================== */
/*  Barra lateral                                                         */
/* ===================================================================== */
[data-testid="stSidebar"] > div:first-child {
  background:
    radial-gradient(420px 300px at 0% 0%, rgba(34, 211, 238, .10), transparent 70%),
    linear-gradient(180deg, #0A1122 0%, #070C18 100%) !important;
}
[data-testid="stSidebar"] { border-right: 1px solid var(--sc-borde) !important; }
[data-testid="stSidebarLogo"] { height: 3.4rem !important; max-width: 15rem !important;
  filter: drop-shadow(0 4px 14px rgba(34, 211, 238, .25)); }
[data-testid="stHeaderLogo"] { height: 2.6rem !important; }
[data-testid="stSidebarHeader"] { height: auto !important; min-height: 4rem; align-items: center; }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
  font: 600 10.5px var(--sc-mono) !important; letter-spacing: .18em; text-transform: uppercase;
  color: var(--sc-tenue) !important;
}

/* ===================================================================== */
/*  Contenido principal                                                   */
/* ===================================================================== */
[data-testid="stMainBlockContainer"] { padding-top: 4.6rem; padding-bottom: 2rem; }
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"] > * {
  animation: sc-entrar .55s cubic-bezier(.2, .7, .2, 1) both;
}
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"] > *:nth-child(2) { animation-delay: .05s; }
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"] > *:nth-child(3) { animation-delay: .10s; }
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"] > *:nth-child(4) { animation-delay: .15s; }
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"] > *:nth-child(n+5) { animation-delay: .2s; }

/* Etiquetas de los controles, en el estilo de los rótulos */
[data-testid="stMain"] [data-testid="stWidgetLabel"] p {
  font: 600 10.5px var(--sc-mono) !important; letter-spacing: .16em; text-transform: uppercase;
  color: var(--sc-tenue) !important;
}
/* Deslizadores con brillo */
[data-testid="stSlider"] [role="slider"] {
  box-shadow: 0 0 0 4px rgba(34, 211, 238, .18), 0 0 16px rgba(34, 211, 238, .7) !important;
}
[data-testid="stSliderThumbValue"] { font-family: var(--sc-mono) !important; font-weight: 600;
  text-shadow: 0 0 10px rgba(34, 211, 238, .6); }
/* Pestañas */
[data-testid="stTabs"] [role="tablist"] { gap: 4px; border-bottom: 1px solid var(--sc-borde); }
[data-testid="stTabs"] [role="tab"] { padding: 6px 12px; border-radius: 8px 8px 0 0; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  background: linear-gradient(180deg, rgba(34, 211, 238, .12), transparent);
}
/* Botones de descarga y principales */
[data-testid="stMain"] button[kind="primary"], [data-testid="stDownloadButton"] button {
  transition: transform .15s ease, box-shadow .2s ease !important;
}
[data-testid="stDownloadButton"] button:hover, [data-testid="stMain"] button[kind="primary"]:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 22px -8px rgba(34, 211, 238, .7) !important;
}

/* ===================================================================== */
/*  Paneles de cristal (contenedores con key "panel-…")                   */
/* ===================================================================== */
[class*="st-key-panel"] {
  position: relative;
  background: linear-gradient(180deg, var(--sc-panel), var(--sc-panel-2)) !important;
  border: 1px solid var(--sc-borde) !important; border-radius: 16px; padding: 16px 18px;
  box-shadow: var(--sc-sombra), inset 0 1px 0 rgba(255, 255, 255, .045);
  backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  transition: border-color .25s ease;
}
[class*="st-key-panel"]:hover { border-color: var(--sc-borde-2) !important; }
/* Filo de luz en el borde superior */
[class*="st-key-panel"]::before {
  content: ""; position: absolute; top: -1px; left: 18px; right: 18px; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(34, 211, 238, .55), transparent);
  pointer-events: none;
}

/* Panel del mapa: esquinas de visor, viñeta y línea de barrido */
[class*="st-key-panel-mapa"] [data-testid="stDeckGlJsonChart"],
[class*="st-key-panel-mapa"] iframe { border-radius: 12px; overflow: hidden; }
.st-key-panel-mapa, .st-key-panel-mapa-prevision, .st-key-panel-mini-mapa {
  background:
    radial-gradient(600px 300px at 50% 0%, rgba(34, 211, 238, .06), transparent 70%),
    linear-gradient(180deg, var(--sc-panel), var(--sc-panel-2)) !important;
}
/* Marco de visor sobre los mapas: viñeta, línea de barrido y esquinas luminosas.
   Va en pseudoelementos del contenedor del mapa: no añade nada al DOM ni tapa el ratón. */
[class*="st-key-panel"] [data-testid="stElementContainer"]:has([data-testid="stDeckGlJsonChart"]),
[class*="st-key-panel"] [data-testid="stElementContainer"]:has(iframe) { position: relative; }
[class*="st-key-panel"] [data-testid="stElementContainer"]:has([data-testid="stDeckGlJsonChart"])::before,
[class*="st-key-panel"] [data-testid="stElementContainer"]:has(iframe)::before {
  content: ""; position: absolute; inset: 0; z-index: 3; pointer-events: none; border-radius: 12px;
  background:
    linear-gradient(180deg, transparent 0, rgba(34, 211, 238, .035) 80%, rgba(34, 211, 238, .14) 100%)
      0 -40% / 100% 18% no-repeat,
    radial-gradient(ellipse at center, transparent 58%, rgba(6, 10, 20, .6) 100%);
  animation: sc-barrido-fondo 8s linear infinite; }
[class*="st-key-panel"] [data-testid="stElementContainer"]:has([data-testid="stDeckGlJsonChart"])::after,
[class*="st-key-panel"] [data-testid="stElementContainer"]:has(iframe)::after {
  content: ""; position: absolute; inset: 10px; z-index: 3; pointer-events: none;
  --l: rgba(34, 211, 238, .8);
  background:
    linear-gradient(var(--l), var(--l)) top left / 22px 2px,
    linear-gradient(var(--l), var(--l)) top left / 2px 22px,
    linear-gradient(var(--l), var(--l)) top right / 22px 2px,
    linear-gradient(var(--l), var(--l)) top right / 2px 22px,
    linear-gradient(var(--l), var(--l)) bottom left / 22px 2px,
    linear-gradient(var(--l), var(--l)) bottom left / 2px 22px,
    linear-gradient(var(--l), var(--l)) bottom right / 22px 2px,
    linear-gradient(var(--l), var(--l)) bottom right / 2px 22px;
  background-repeat: no-repeat; filter: drop-shadow(0 0 4px rgba(34, 211, 238, .9)); }
@keyframes sc-barrido-fondo {
  from { background-position: 0 -40%, 0 0; } to { background-position: 0 140%, 0 0; } }

/* ===================================================================== */
/*  Cabecera de la barra lateral                                          */
/* ===================================================================== */
.sc-cabecera { position: relative; display: flex; flex-direction: column; align-items: flex-start;
  gap: 14px; padding: 16px 16px 18px; border-radius: 16px; overflow: hidden; isolation: isolate;
  box-shadow: var(--sc-sombra); }
/* Borde de degradado que gira lentamente: un cono que rota detrás y una capa que lo tapa
   dejando ver solo un filo de 1 px */
.sc-cabecera::before { content: ""; position: absolute; inset: -60%; z-index: -2;
  background: conic-gradient(rgba(34, 211, 238, .95), rgba(167, 139, 250, .2) 25%,
                             rgba(52, 211, 153, .75) 50%, rgba(34, 211, 238, .12) 75%,
                             rgba(34, 211, 238, .95));
  animation: sc-giro 10s linear infinite; }
.sc-cabecera::after { content: ""; position: absolute; inset: 1px; z-index: -1; border-radius: 15px;
  background:
    radial-gradient(260px 160px at 100% 0%, rgba(167, 139, 250, .16), transparent 70%),
    radial-gradient(260px 160px at 0% 100%, rgba(34, 211, 238, .14), transparent 70%),
    #0B1324;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .06); }
.sc-vivo { display: inline-flex; align-items: center; gap: 8px; padding: 3px 10px 3px 8px;
  border-radius: 999px; background: rgba(52, 211, 153, .1); border: 1px solid rgba(52, 211, 153, .3);
  font: 600 10px var(--sc-mono); letter-spacing: .2em; color: #34D399; }
.sc-punto { width: 7px; height: 7px; border-radius: 50%; background: #34D399;
  box-shadow: 0 0 8px #34D399; }
.sc-activo .sc-punto { animation: sc-latido 1.6s infinite; }
.sc-titulo { font: 700 22px var(--sc-titulos); margin: 10px 0 4px; line-height: 1.15;
  letter-spacing: -.01em;
  background: linear-gradient(120deg, #FFFFFF 30%, #A5F3FC 70%, #C4B5FD);
  -webkit-background-clip: text; background-clip: text; color: transparent; }
.sc-subtitulo { color: var(--sc-tenue); font-size: 12.5px; line-height: 1.45; }
.sc-reloj { width: 100%; padding-top: 12px; border-top: 1px dashed rgba(148, 163, 184, .18); }
.sc-hora { font: 600 38px var(--sc-mono); color: #F8FAFC; line-height: 1; letter-spacing: -.02em;
  text-shadow: 0 0 18px rgba(34, 211, 238, .55), 0 0 2px rgba(34, 211, 238, .9); }
.sc-hora em { font-style: normal; animation: sc-brillo 1s steps(2) infinite; color: #22D3EE; }
.sc-fecha { font: 500 11px var(--sc-mono); color: var(--sc-tenue); letter-spacing: .18em;
  margin-top: 8px; text-transform: uppercase; }
.sc-chips { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 12px; }
.sc-chip { font: 500 10.5px var(--sc-mono); padding: 4px 9px; border-radius: 7px;
  background: rgba(148, 163, 184, .07); border: 1px solid rgba(148, 163, 184, .18);
  color: var(--sc-tenue); letter-spacing: .06em; }
.sc-chip b { color: #67E8F9; font-weight: 600; }

/* ===================================================================== */
/*  Tarjetas de indicadores                                               */
/* ===================================================================== */
.sc-kpis { display: grid; grid-template-columns: repeat(var(--n), minmax(0, 1fr)); gap: 14px; }
.sc-kpi { position: relative; overflow: hidden; padding: 15px 16px 0; border-radius: 16px;
  display: flex; flex-direction: column;
  background:
    radial-gradient(220px 120px at 100% 0%, rgba(var(--c), .16), transparent 70%),
    linear-gradient(180deg, rgba(17, 26, 46, .85), rgba(10, 16, 31, .9));
  border: 1px solid rgba(var(--c), .22);
  box-shadow: var(--sc-sombra), inset 0 1px 0 rgba(255, 255, 255, .05);
  animation: sc-entrar .6s cubic-bezier(.2, .7, .2, 1) both;
  transition: transform .25s ease, border-color .25s ease, box-shadow .25s ease; }
.sc-kpi:nth-child(2) { animation-delay: .06s; } .sc-kpi:nth-child(3) { animation-delay: .12s; }
.sc-kpi:nth-child(4) { animation-delay: .18s; } .sc-kpi:nth-child(5) { animation-delay: .24s; }
.sc-kpi:hover { transform: translateY(-3px); border-color: rgba(var(--c), .5);
  box-shadow: 0 22px 40px -20px rgba(var(--c), .45), inset 0 1px 0 rgba(255, 255, 255, .06); }
.sc-kpi::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, transparent, rgb(var(--c)), transparent);
  box-shadow: 0 0 14px rgb(var(--c)); transform-origin: left;
  animation: sc-crecer .9s cubic-bezier(.2, .7, .2, 1) both; }
.sc-kpi-titulo { display: flex; align-items: center; gap: 8px;
  font: 600 10px var(--sc-mono); letter-spacing: .16em; text-transform: uppercase;
  color: var(--sc-tenue); }
.sc-kpi-titulo::before { content: ""; width: 6px; height: 6px; border-radius: 2px;
  background: rgb(var(--c)); box-shadow: 0 0 8px rgb(var(--c)); flex: none; }
.sc-kpi-valor { font: 700 clamp(24px, 2.15vw, 34px) var(--sc-titulos); color: #F8FAFC;
  line-height: 1.1; margin-top: 8px; white-space: nowrap; letter-spacing: -.02em;
  font-variant-numeric: tabular-nums; text-shadow: 0 0 22px rgba(var(--c), .35); }
.sc-kpi-valor.sc-texto { font-size: clamp(15px, 1.25vw, 19px); white-space: normal;
  line-height: 1.25; min-height: 2.5em; display: flex; align-items: center; letter-spacing: 0;
  color: rgb(var(--c)); text-shadow: 0 0 16px rgba(var(--c), .4); }
.sc-kpi-unidad { font: 500 13px Inter, sans-serif; color: var(--sc-tenue); margin-left: 6px;
  letter-spacing: 0; text-shadow: none; }
.sc-kpi-sub { font-size: 12px; color: #CBD5E1; margin-top: 3px; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; }
.sc-kpi-sub::first-letter { text-transform: uppercase; }
.sc-spark { display: block; width: calc(100% + 32px); height: 40px; margin: 10px -16px 0;
  opacity: .95; }
.sc-kpi-pie { height: 14px; }
.sc-nota { display: flex; align-items: center; gap: 6px; font-size: 11.5px; color: var(--sc-apagado);
  margin: 8px 2px 0; }
.sc-nota::before { content: ""; width: 14px; height: 2px; border-radius: 2px;
  background: linear-gradient(90deg, #22D3EE, transparent); }

/* ===================================================================== */
/*  Rótulos de sección y ayudas                                           */
/* ===================================================================== */
.sc-seccion { display: flex; align-items: center; gap: 10px; margin: 2px 0 10px;
  font: 600 11px var(--sc-mono); letter-spacing: .18em; text-transform: uppercase;
  color: #67E8F9; }
.sc-seccion::before { content: ""; width: 8px; height: 8px; transform: rotate(45deg);
  border: 1.5px solid #22D3EE; box-shadow: 0 0 10px rgba(34, 211, 238, .8); flex: none; }
.sc-seccion::after { content: ""; flex: 1; height: 1px;
  background: linear-gradient(90deg, rgba(34, 211, 238, .35), rgba(148, 163, 184, .08) 60%, transparent); }
.sc-ayuda { font-size: 12.5px; color: var(--sc-tenue); line-height: 1.5; margin: -4px 0 12px; }
.sc-intro { display: flex; align-items: center; gap: 14px; margin: 0 0 18px; padding: 14px 18px;
  border-radius: 14px; border: 1px solid var(--sc-borde);
  background: linear-gradient(90deg, rgba(34, 211, 238, .08), rgba(167, 139, 250, .05) 60%, transparent); }
.sc-intro-icono { width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center;
  background: linear-gradient(135deg, rgba(34, 211, 238, .25), rgba(167, 139, 250, .2));
  border: 1px solid rgba(34, 211, 238, .4); color: #A5F3FC; font-size: 22px;
  box-shadow: 0 0 24px -6px rgba(34, 211, 238, .8); flex: none; }
.sc-intro-texto { color: #CBD5E1; font-size: 13.5px; line-height: 1.5; }
.sc-intro-texto b { color: #F8FAFC; }

/* Iconos de Material dentro del HTML propio */
.sc-ico { font-family: 'Material Symbols Rounded'; font-weight: normal; font-style: normal;
  line-height: 1; letter-spacing: normal; text-transform: none; white-space: nowrap;
  font-feature-settings: 'liga'; -webkit-font-smoothing: antialiased; user-select: none; }

/* ===================================================================== */
/*  Alertas                                                               */
/* ===================================================================== */
.sc-alerta { position: relative; display: grid; grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 10px; align-items: center; padding: 10px 12px; border-radius: 11px; margin-bottom: 8px;
  background: linear-gradient(90deg, color-mix(in srgb, var(--c) 13%, transparent), rgba(15, 23, 42, .55) 55%);
  border: 1px solid color-mix(in srgb, var(--c) 28%, transparent);
  animation: sc-entrar .45s cubic-bezier(.2, .7, .2, 1) both; transition: transform .2s ease; }
.sc-alerta:hover { transform: translateX(3px); }
.sc-alerta-icono { width: 26px; height: 26px; border-radius: 8px; display: grid; place-items: center;
  background: color-mix(in srgb, var(--c) 18%, transparent); color: var(--c); font-size: 17px;
  box-shadow: 0 0 14px -2px color-mix(in srgb, var(--c) 70%, transparent); }
.sc-alerta-texto { font-size: 12.5px; line-height: 1.35; color: #F1F5F9; font-weight: 600;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sc-alerta-texto span { display: block; color: var(--sc-tenue); font-size: 11.5px; font-weight: 400;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sc-alerta-cifra { font: 700 13px var(--sc-mono); color: var(--c); text-align: right;
  text-shadow: 0 0 10px color-mix(in srgb, var(--c) 60%, transparent); }
.sc-alerta-cifra small { display: block; font: 500 9.5px var(--sc-mono); color: var(--sc-apagado);
  letter-spacing: .08em; text-shadow: none; }
.sc-alerta-nivel { grid-column: 1 / -1; height: 3px; border-radius: 3px; overflow: hidden;
  background: rgba(148, 163, 184, .12); margin-top: -2px; }
.sc-alerta-nivel div { height: 100%; border-radius: 3px; background: var(--c);
  box-shadow: 0 0 8px var(--c); transform-origin: left;
  animation: sc-crecer .8s cubic-bezier(.2, .7, .2, 1) both; }
.sc-alerta.sc-ok { grid-template-columns: auto minmax(0, 1fr); }

/* ===================================================================== */
/*  Ranking con barras luminosas                                          */
/* ===================================================================== */
.sc-fila { display: grid; grid-template-columns: 22px minmax(0, 1fr) auto; align-items: center;
  gap: 10px; padding: 6px 4px; border-radius: 8px; font-size: 12px; transition: background .2s; }
.sc-fila:hover { background: rgba(148, 163, 184, .06); }
.sc-fila-pos { font: 600 10.5px var(--sc-mono); color: var(--sc-apagado); text-align: center;
  height: 20px; line-height: 20px; border-radius: 6px; }
.sc-fila:nth-child(-n+3) .sc-fila-pos { color: #0B1120; background: var(--c);
  box-shadow: 0 0 10px -1px var(--c); }
.sc-fila-nombre { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #CBD5E1; }
.sc-fila-barra { height: 5px; border-radius: 5px; background: rgba(148, 163, 184, .1);
  margin-top: 5px; overflow: hidden; }
.sc-fila-barra div { height: 100%; border-radius: 5px; transform-origin: left;
  background: linear-gradient(90deg, color-mix(in srgb, var(--c) 35%, transparent), var(--c));
  box-shadow: 0 0 10px color-mix(in srgb, var(--c) 70%, transparent);
  animation: sc-crecer .9s cubic-bezier(.2, .7, .2, 1) both; }
.sc-fila-valor { min-width: 48px; text-align: right; font: 600 12px var(--sc-mono); color: #F8FAFC; }
.sc-fila.sc-sin-pos { grid-template-columns: minmax(0, 1fr) auto; }

/* ===================================================================== */
/*  Leyenda flotante del mapa                                             */
/* ===================================================================== */
.st-key-leyenda-mapa { position: absolute; left: 34px; bottom: 30px; z-index: 5;
  width: auto !important; pointer-events: none; }
.sc-leyenda { pointer-events: auto; padding: 9px 13px; border-radius: 12px;
  background: rgba(6, 10, 20, .78); border: 1px solid rgba(34, 211, 238, .25);
  backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  box-shadow: 0 12px 30px -10px rgba(0, 0, 0, .8);
  font-size: 12px; color: #CBD5E1; max-width: 240px; }
.sc-leyenda summary { cursor: pointer; list-style: none; display: flex; align-items: center;
  gap: 9px; user-select: none; }
.sc-leyenda summary::-webkit-details-marker { display: none; }
.sc-leyenda summary::after { content: "▸"; color: var(--sc-tenue); font-size: 11px; }
.sc-leyenda[open] summary::after { content: "▾"; }
.sc-leyenda summary b { color: #F8FAFC; font-weight: 600; }
.sc-tira { display: inline-flex; border-radius: 3px; overflow: hidden;
  box-shadow: 0 0 10px rgba(34, 211, 238, .25); }
.sc-tira i { width: 10px !important; height: 8px !important; margin: 0 !important;
  border-radius: 0 !important; }
.sc-leyenda-clases { display: flex; flex-direction: column; gap: 5px; margin-top: 9px; }
.sc-leyenda i { display: inline-block; width: 18px; height: 10px; border-radius: 3px;
  margin-right: 8px; vertical-align: middle; }
.sc-leyenda small { color: var(--sc-apagado); font-size: 10.5px; line-height: 1.3; margin-top: 2px; }

/* ===================================================================== */
/*  Ficha de estación                                                     */
/* ===================================================================== */
.sc-ficha { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
@media (max-width: 900px) { .sc-ficha { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.sc-ficha div { position: relative; padding: 10px 12px 10px 40px; border-radius: 11px;
  background: rgba(148, 163, 184, .045); border: 1px solid rgba(148, 163, 184, .1);
  font: 500 9.5px var(--sc-mono); color: var(--sc-tenue); letter-spacing: .14em;
  text-transform: uppercase; }
.sc-ficha div .sc-ico { position: absolute; left: 11px; top: 50%; transform: translateY(-50%);
  font-size: 19px; color: #22D3EE; letter-spacing: 0;
  filter: drop-shadow(0 0 6px rgba(34, 211, 238, .6)); }
.sc-ficha b { display: block; font: 600 14.5px var(--sc-titulos); color: #F8FAFC;
  letter-spacing: 0; text-transform: none; margin-top: 3px; line-height: 1.3; }

/* ===================================================================== */
/*  Pie de la barra lateral                                               */
/* ===================================================================== */
.sc-pie { display: flex; flex-direction: column; gap: 10px; }
.sc-pie-fuente { display: flex; align-items: center; gap: 10px; padding: 10px 12px;
  border-radius: 12px; background: rgba(148, 163, 184, .05); border: 1px solid var(--sc-borde); }
.sc-pie-fuente .sc-ico { font-size: 20px; color: #22D3EE; }
.sc-pie-fuente b { display: block; font-size: 12.5px; color: #F1F5F9; line-height: 1.3; }
.sc-pie-fuente div span { font: 500 10.5px var(--sc-mono); color: var(--sc-tenue); }
.sc-pie-cifras { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.sc-pie-cifras div { padding: 9px 11px; border-radius: 11px; border: 1px solid var(--sc-borde);
  background: rgba(148, 163, 184, .035); font: 500 9.5px var(--sc-mono); color: var(--sc-apagado);
  letter-spacing: .14em; text-transform: uppercase; }
.sc-pie-cifras b { display: block; font: 700 17px var(--sc-titulos); color: #F8FAFC;
  letter-spacing: -.01em; text-transform: none; margin-top: 2px; }
.sc-pie-texto { font-size: 11px; color: var(--sc-apagado); line-height: 1.5; }

/* ===================================================================== */
/*  Ideas de ampliación                                                   */
/* ===================================================================== */
.sc-idea-cab { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.sc-idea-icono { width: 42px; height: 42px; border-radius: 12px; display: grid; place-items: center;
  font-size: 22px; color: var(--c);
  background: color-mix(in srgb, var(--c) 14%, transparent);
  border: 1px solid color-mix(in srgb, var(--c) 40%, transparent);
  box-shadow: 0 0 22px -6px var(--c); flex: none; }
.sc-idea-titulo { font: 600 15.5px var(--sc-titulos); color: #F8FAFC; line-height: 1.25; }
.sc-esfuerzo { display: flex; align-items: center; gap: 4px; margin-top: 5px;
  font: 500 9.5px var(--sc-mono); letter-spacing: .14em; text-transform: uppercase;
  color: var(--sc-tenue); }
.sc-esfuerzo i { width: 14px; height: 4px; border-radius: 3px; background: rgba(148, 163, 184, .18); }
.sc-esfuerzo i.on { background: var(--c); box-shadow: 0 0 8px var(--c); }
.sc-esfuerzo em { font-style: normal; margin-left: 6px; color: var(--c); }
[class*="st-key-panel-idea"] { transition: transform .25s ease, border-color .25s ease,
  box-shadow .25s ease !important; }
[class*="st-key-panel-idea"]:hover { transform: translateY(-4px);
  border-color: rgba(34, 211, 238, .35) !important;
  box-shadow: 0 26px 50px -24px rgba(34, 211, 238, .45), inset 0 1px 0 rgba(255, 255, 255, .06); }
[class*="st-key-panel-idea"] p { font-size: 13px; line-height: 1.55; color: #CBD5E1; }
[class*="st-key-panel-idea"] strong { color: #67E8F9; font-weight: 600; }

/* Tarjetas de exportación */
.sc-exportar { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.sc-exportar .sc-idea-icono { width: 38px; height: 38px; font-size: 20px; }
.sc-exportar b { display: block; font: 600 14.5px var(--sc-titulos); color: #F8FAFC; }
.sc-exportar > div:last-child span { font-size: 12px; color: var(--sc-tenue); }

/* Vista previa del informe: títulos a escala del panel */
.st-key-panel-vista-informe h1 { font-size: 1.55rem !important; letter-spacing: -.01em;
  background: linear-gradient(120deg, #FFFFFF 30%, #A5F3FC); -webkit-background-clip: text;
  background-clip: text; color: transparent !important; }
.st-key-panel-vista-informe h2 { font-size: 1.15rem !important; color: #67E8F9 !important; }
.st-key-panel-vista-informe h3 { font-size: 1rem !important; }

/* ===================================================================== */
/*  Ajustes de maquetación                                                */
/* ===================================================================== */
/* Sin hueco bajo el mapa: el panel que lleva leyenda termina donde termina el mapa */
[class*="st-key-panel"]:has(.st-key-leyenda-mapa) { padding-bottom: 12px; }
[class*="st-key-panel"]:has(.st-key-leyenda-mapa) [data-testid="stDeckGlJsonChart"] {
  margin-bottom: -6px; }
/* Paneles "ajustados": miden exactamente lo que su columna vecina (el mapa) y, si su
   contenido no cabe, hacen scroll por dentro. Solo con columnas lado a lado (>= 640 px). */
@media (min-width: 640px) {
  [data-testid="stHorizontalBlock"]:has([class*="-ajustado"]) { align-items: stretch; }
  [data-testid="stColumn"]:has([class*="-ajustado"]) { position: relative; align-self: stretch; }
  [class*="st-key-panel"][class*="-ajustado"] { position: absolute; inset: 0; overflow-y: auto; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
</style>
"""


def aplicar() -> None:
    """Inyecta el CSS de la sala de control."""
    st.html(CSS)


def _rgb(color: str) -> str:
    """'#22D3EE' -> '34, 211, 238' para usarlo en ``rgba(var(--c), …)``."""
    return ", ".join(str(canal) for canal in escalas.rgb(color))


def icono(nombre: str) -> str:
    """Un icono de Material Symbols (el mismo juego que ``:material/…:``) como HTML."""
    return f'<span class="sc-ico">{escape(nombre)}</span>'


def cabecera(titulo: str, subtitulo: str, momento: datetime | None,
             chips: list[str] = (), etiqueta: str = "EN DIRECTO", destino=None,
             activo: bool = False) -> None:
    """Cabecera con indicador de estado, título, reloj y chips.

    Por defecto va en la barra lateral, en formato vertical. ``destino`` es otro
    sitio donde dibujarla (por ejemplo, un hueco reservado fuera de un
    fragmento). ``activo=True`` hace latir el indicador (solo mientras algo se reproduce).
    """
    reloj = ""
    if momento is not None:
        separador = "<em>:</em>" if activo else ":"
        reloj = (f'<div class="sc-reloj"><div class="sc-hora">{momento:%H}{separador}'
                 f'{momento:%M}</div><div class="sc-fecha">{fecha_larga(momento)}</div></div>')
    fichas = "".join(f'<span class="sc-chip">{chip}</span>' for chip in chips)
    lugar = destino if destino is not None else st.sidebar
    clases = "sc-cabecera sc-activo" if activo else "sc-cabecera"
    lugar.html(f'<div class="{clases}"><div>'
               f'<div class="sc-vivo"><span class="sc-punto"></span>{escape(etiqueta)}</div>'
               f'<div class="sc-titulo">{escape(titulo)}</div>'
               f'<div class="sc-subtitulo">{escape(subtitulo)}</div>'
               f'<div class="sc-chips">{fichas}</div></div>{reloj}</div>')


DIAS = ("lun", "mar", "mié", "jue", "vie", "sáb", "dom")
MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")


def fecha_larga(momento: datetime) -> str:
    """'jue · 10 nov 2026', sin depender del idioma del sistema."""
    return f"{DIAS[momento.weekday()]} · {momento.day:02d} {MESES[momento.month - 1]} {momento.year}"


def chip(etiqueta: str, valor: str) -> str:
    """Texto HTML de un chip ``ETIQUETA valor`` para la cabecera."""
    return f"{escape(etiqueta)} <b>{escape(valor)}</b>"


def sparkline(serie: list[float], color: str) -> str:
    """Minigráfico de área con degradado y brillo, como imagen SVG.

    Va como ``<img>`` con el SVG dentro: ``st.html`` limpia las etiquetas ``<svg>``
    sueltas, pero deja pasar una imagen.
    """
    serie = [valor for valor in serie if valor == valor]
    if len(serie) < 2:
        return ""
    minimo, maximo = min(serie), max(serie)
    rango = (maximo - minimo) or 1
    puntos = [(200 * i / (len(serie) - 1), 36 - 30 * (valor - minimo) / rango)
              for i, valor in enumerate(serie)]
    linea = " ".join(f"{x:.1f},{y:.1f}" for x, y in puntos)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 40" '
           f'preserveAspectRatio="none">'
           f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
           f'<stop offset="0" stop-color="{color}" stop-opacity=".42"/>'
           f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient>'
           f'<filter id="b" x="-5%" y="-50%" width="110%" height="200%">'
           f'<feGaussianBlur stdDeviation="2"/></filter></defs>'
           f'<polygon points="0,40 {linea} 200,40" fill="url(#g)"/>'
           f'<polyline points="{linea}" fill="none" stroke="{color}" stroke-width="3" '
           f'stroke-opacity=".7" filter="url(#b)" vector-effect="non-scaling-stroke"/>'
           f'<polyline points="{linea}" fill="none" stroke="{color}" stroke-width="1.6" '
           f'stroke-linejoin="round" vector-effect="non-scaling-stroke"/></svg>')
    datos = base64.b64encode(svg.encode()).decode()
    return f'<img class="sc-spark" alt="" src="data:image/svg+xml;base64,{datos}">'


def _es_numero(texto: str) -> bool:
    """Indica si el valor de una tarjeta es una cifra (y no un texto como una categoría)."""
    return texto.replace(".", "", 1).replace("-", "", 1).isdigit()


def tarjetas(lista: list[dict], nota: str = "") -> None:
    """Tarjetas KPI, todas en una sola fila. Cada una: ``titulo``, ``valor``, ``unidad``,
    ``sub``, ``color`` y, opcional, ``serie`` (minigráfico). Un valor de texto se escribe
    más pequeño para que quepa. ``nota`` explica debajo qué muestran los minigráficos."""
    html = "".join(
        f'<div class="sc-kpi" style="--c:{_rgb(t["color"])}">'
        f'<div class="sc-kpi-titulo">{escape(t["titulo"])}</div>'
        f'<div class="sc-kpi-valor{"" if _es_numero(t["valor"]) else " sc-texto"}">'
        f'{escape(t["valor"])}<span class="sc-kpi-unidad">{escape(t.get("unidad", ""))}</span>'
        f'</div><div class="sc-kpi-sub">{escape(t.get("sub", ""))}</div>'
        f'{sparkline(t.get("serie") or [], t["color"]) or "<div class=sc-kpi-pie></div>"}</div>'
        for t in lista)
    pie = f'<div class="sc-nota">{escape(nota)}</div>' if nota else ""
    st.html(f'<div class="sc-kpis" style="--n:{len(lista)}">{html}</div>{pie}')


def seccion(texto: str, ayuda: str = "") -> None:
    """Rótulo de sección y, debajo, una línea que explica cómo leer lo que sigue."""
    explicacion = f'<div class="sc-ayuda">{escape(ayuda)}</div>' if ayuda else ""
    st.html(f'<div class="sc-seccion">{escape(texto)}</div>{explicacion}')


def ayuda(texto: str) -> None:
    """Una línea gris que explica cómo leer lo que sigue (sin rótulo de sección)."""
    st.html(f'<div class="sc-ayuda" style="margin-top:6px">{escape(texto)}</div>')


def intro(nombre_icono: str, texto_html: str) -> None:
    """Franja de presentación de una página: icono grande y una frase (admite ``<b>``)."""
    st.html(f'<div class="sc-intro"><div class="sc-intro-icono">{icono(nombre_icono)}</div>'
            f'<div class="sc-intro-texto">{texto_html}</div></div>')


def alertas(lista: list[dict], vacio: str = "Sin alertas en este momento") -> None:
    """Lista de alertas. Cada una: ``titulo``, ``detalle`` y ``color``; opcionales:
    ``cifra`` (texto a la derecha), ``unidad`` (debajo de la cifra), ``nivel`` (0-1,
    barra de intensidad) e ``icono`` (nombre de Material Symbols)."""
    if not lista:
        st.html(f'<div class="sc-alerta sc-ok" style="--c:{VERDE}">'
                f'<span class="sc-alerta-icono">{icono("verified")}</span>'
                f'<div class="sc-alerta-texto">{escape(vacio)}'
                f'<span>Todas las estaciones en valores normales</span></div></div>')
        return
    partes = []
    for numero, a in enumerate(lista):
        cifra = ""
        if "cifra" in a:
            cifra = (f'<div class="sc-alerta-cifra">{escape(a["cifra"])}'
                     f'<small>{escape(a.get("unidad", ""))}</small></div>')
        nivel = ""
        if "nivel" in a:
            nivel = (f'<div class="sc-alerta-nivel"><div style="width:'
                     f'{100 * max(0.04, min(1, a["nivel"])):.0f}%"></div></div>')
        partes.append(
            f'<div class="sc-alerta{"" if cifra else " sc-ok"}" style="--c:{a["color"]};'
            f'animation-delay:{min(numero, 12) * 0.035:.3f}s">'
            f'<span class="sc-alerta-icono">{icono(a.get("icono", "warning"))}</span>'
            f'<div class="sc-alerta-texto">{escape(a["titulo"])}'
            f'<span>{escape(a["detalle"])}</span></div>{cifra}{nivel}</div>')
    st.html("".join(partes))


def barras(filas: list[tuple[str, float, str, str]], maximo: float,
           posiciones: bool = True) -> None:
    """Ranking con barras luminosas. Cada fila: ``(nombre, valor, color, texto)``.

    Con ``posiciones`` se numera cada fila y las tres primeras llevan su color."""
    maximo = maximo or 1
    clase = "sc-fila" if posiciones else "sc-fila sc-sin-pos"
    st.html("".join(
        f'<div class="{clase}" style="--c:{color}">'
        f'{f"<div class=sc-fila-pos>{numero}</div>" if posiciones else ""}'
        f'<div><div class="sc-fila-nombre" title="{escape(nombre)}">{escape(nombre)}</div>'
        f'<div class="sc-fila-barra"><div style="width:{max(2, 100 * valor / maximo):.0f}%;'
        f'animation-delay:{numero * 0.04:.2f}s"></div></div></div>'
        f'<div class="sc-fila-valor">{escape(texto)}</div></div>'
        for numero, (nombre, valor, color, texto) in enumerate(filas, start=1)))


def piezas_echarts(variable: str) -> list[dict]:
    """Las clases de la escala oficial como ``visualMap.pieces`` de ECharts."""
    datos = escalas.escala(variable)
    cortes = datos["cortes"]
    limites = [{"lte": cortes[0]},
               *({"gt": a, "lte": b} for a, b in zip(cortes, cortes[1:])),
               {"gt": cortes[-1]}]
    return [{**limite, "color": tono, "label": nombre}
            for limite, tono, nombre in zip(limites, datos["colores"], escalas.etiquetas(variable))]


def leyenda(variable: str) -> None:
    """Leyenda de la escala oficial, flotando en la esquina inferior izquierda del mapa.

    Se llama justo después del mapa, dentro de su panel: el contenedor ``leyenda-mapa``
    se coloca encima del mapa con CSS, así que no ocupa sitio debajo.
    Es plegable (``<details>`` de HTML, sin recargar la página): cerrada solo
    muestra la variable y una tira con los colores de la escala.
    """
    datos = escalas.escala(variable)
    muestras = "".join(f'<span><i style="background:{tono};box-shadow:0 0 8px {tono}88"></i>'
                       f'{escape(nombre)}</span>'
                       for tono, nombre in zip(datos["colores"], escalas.etiquetas(variable)))
    tira = "".join(f'<i style="background:{tono}"></i>' for tono in datos["colores"])
    with st.container(key="leyenda-mapa", width="content"):
        st.html(f'<details class="sc-leyenda"><summary><span class="sc-tira">{tira}</span>'
                f'<b>{escape(datos["nombre"])} ({escape(datos["unidad"])})</b></summary>'
                f'<div class="sc-leyenda-clases">{muestras}'
                f'<small>{escape(datos["fuente"])}</small></div></details>')


ICONOS_FICHA = {"Coordenadas": "my_location", "Sistema": "public", "Altitud": "landscape",
                "Vecina más cercana": "hub", "Distancia y rumbo": "explore",
                "Mediciones válidas": "monitoring"}


def ficha(campos: dict[str, str]) -> None:
    """Rejilla de datos de una ficha: icono, etiqueta pequeña y valor grande."""
    st.html('<div class="sc-ficha">' + "".join(
        f'<div>{icono(ICONOS_FICHA.get(etiqueta, "info"))}{escape(etiqueta)}'
        f'<b title="{escape(valor)}">{escape(valor)}</b></div>'
        for etiqueta, valor in campos.items()) + "</div>")


def pie_lateral(fuente: str, estaciones: int, mediciones: int, periodo: str) -> None:
    """Resumen de la fuente de datos al pie de la barra lateral."""
    st.html(f'<div class="sc-pie"><div class="sc-pie-fuente">{icono("database")}'
            f'<div><b>{escape(fuente)}</b><span>{escape(periodo)}</span></div></div>'
            f'<div class="sc-pie-cifras"><div>Estaciones<b>{estaciones}</b></div>'
            f'<div>Mediciones<b>{f"{mediciones:,}".replace(",", ".")}</b></div></div>'
            + '<div class="sc-pie-texto">Coordenadas WGS84 (EPSG:4326). Calidad del aire: '
              'categorías del ICA (MITECO) y guía OMS 2021. Temperatura y humedad con '
              'clases al estilo de AEMET.</div></div>')


def cabecera_idea(nombre_icono: str, titulo: str, esfuerzo: str, color: str) -> None:
    """Cabecera de una tarjeta de idea: icono en un recuadro luminoso, título y esfuerzo."""
    nivel = {"Bajo": 1, "Medio": 2, "Alto": 3}[esfuerzo]
    marcas = "".join(f'<i class="{"on" if i < nivel else ""}"></i>' for i in range(3))
    st.html(f'<div class="sc-idea-cab" style="--c:{color}">'
            f'<div class="sc-idea-icono">{icono(nombre_icono)}</div>'
            f'<div><div class="sc-idea-titulo">{escape(titulo)}</div>'
            f'<div class="sc-esfuerzo">Esfuerzo {marcas}<em>{escape(esfuerzo)}</em></div>'
            f'</div></div>')


def cabecera_exportar(nombre_icono: str, titulo: str, texto: str, color: str = CIAN) -> None:
    """Cabecera de una tarjeta de exportación: icono, nombre del formato y para qué sirve."""
    st.html(f'<div class="sc-exportar" style="--c:{color}">'
            f'<div class="sc-idea-icono">{icono(nombre_icono)}</div>'
            f'<div><b>{escape(titulo)}</b><span>{escape(texto)}</span></div></div>')


# --- Gráficos de ECharts con el mismo aspecto -------------------------------------

_EJE = {
    "axisLine": {"lineStyle": {"color": "rgba(148,163,184,0.25)"}},
    "axisTick": {"show": False},
    "axisLabel": {"color": "#64748B", "fontFamily": "JetBrains Mono, monospace",
                  "fontSize": 10.5},
    "splitLine": {"lineStyle": {"color": "rgba(148,163,184,0.07)", "type": "dashed"}},
    "nameTextStyle": {"color": "#64748B", "fontFamily": "JetBrains Mono, monospace"},
}
_BASE = {
    "backgroundColor": "transparent",
    "textStyle": {"fontFamily": "Inter, sans-serif", "color": "#94A3B8"},
    "animationDuration": 1100, "animationEasing": "cubicOut",
    "tooltip": {"backgroundColor": "rgba(6,10,20,0.92)", "borderColor": "rgba(34,211,238,0.35)",
                "borderWidth": 1, "padding": [8, 12],
                "textStyle": {"color": "#E2E8F0", "fontSize": 12},
                "extraCssText": "border-radius:10px;backdrop-filter:blur(8px);"
                                "box-shadow:0 12px 30px -10px rgba(0,0,0,.8);",
                "axisPointer": {"lineStyle": {"color": "rgba(34,211,238,0.5)"},
                                "crossStyle": {"color": "rgba(34,211,238,0.5)"}}},
    "legend": {"top": 0, "icon": "roundRect", "itemWidth": 14, "itemHeight": 4, "itemGap": 18,
               "textStyle": {"color": "#CBD5E1", "fontSize": 12}},
}


def _fundir(base: dict, propio: dict) -> dict:
    """``propio`` encima de ``base``, entrando en los diccionarios anidados."""
    salida = copy.deepcopy(base)
    for clave, valor in propio.items():
        if isinstance(valor, dict) and isinstance(salida.get(clave), dict):
            salida[clave] = _fundir(salida[clave], valor)
        else:
            salida[clave] = valor
    return salida


def _degradado(color: str, arriba: float, abajo: float = 0.0) -> dict:
    """Relleno de ECharts que va de ``color`` con opacidad ``arriba`` a ``abajo``."""
    r, g, b = escalas.rgb(color)
    return {"type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
            "colorStops": [{"offset": 0, "color": f"rgba({r},{g},{b},{arriba})"},
                           {"offset": 1, "color": f"rgba({r},{g},{b},{abajo})"}]}


def _serie(serie: dict, indice: int) -> dict:
    """Da color, brillo y degradado a una serie que no los trae."""
    serie = copy.deepcopy(serie)
    linea = serie.setdefault("lineStyle", {})
    punto = serie.setdefault("itemStyle", {})
    color = linea.get("color") or punto.get("color")
    if not isinstance(color, str) or not color.startswith("#"):
        if color is None and serie.get("type") in ("line", "bar"):
            color = PALETA[indice % len(PALETA)]
            linea.setdefault("color", color)
            punto.setdefault("color", color)
        else:
            return serie
    if serie.get("type") == "line" and linea.get("opacity", 1) > 0:
        linea.setdefault("shadowBlur", 12)
        linea.setdefault("shadowColor", color + "AA")
        area = serie.get("areaStyle")
        if area is not None and "color" not in area:
            area["color"] = _degradado(color, area.pop("opacity", 0.25) + 0.1)
    if serie.get("type") == "bar":
        punto["color"] = _degradado(color, 0.95, 0.35)
    return serie


def grafico(opciones: dict, height: int = 340, alt: str = "", **argumentos) -> None:
    """``st.echarts_chart`` con el aspecto de la sala de control: tooltip de cristal,
    ejes discretos, leyenda fina, líneas con brillo y áreas con degradado."""
    opciones = _fundir(_BASE, opciones)
    for eje in ("xAxis", "yAxis"):
        if isinstance(opciones.get(eje), dict):
            opciones[eje] = _fundir(_EJE, opciones[eje])
    opciones.setdefault("grid", {"left": 48, "right": 18, "top": 44, "bottom": 34})
    for zoom in opciones.get("dataZoom", []):
        if zoom.get("type") == "slider":
            zoom.update({
                "borderColor": "rgba(148,163,184,0.15)", "backgroundColor": "rgba(148,163,184,0.04)",
                "fillerColor": "rgba(34,211,238,0.12)",
                "handleStyle": {"color": "#22D3EE", "borderColor": "#0B1120",
                                "shadowBlur": 8, "shadowColor": "rgba(34,211,238,0.8)"},
                "moveHandleStyle": {"color": "rgba(34,211,238,0.5)"},
                "dataBackground": {"lineStyle": {"color": "rgba(148,163,184,0.35)"},
                                   "areaStyle": {"color": "rgba(148,163,184,0.12)"}},
                "selectedDataBackground": {"lineStyle": {"color": "#22D3EE"},
                                           "areaStyle": {"color": "rgba(34,211,238,0.2)"}},
                "textStyle": {"color": "#64748B"}, "brushSelect": False})
    if "series" in opciones:
        opciones["series"] = [_serie(s, i) for i, s in enumerate(opciones["series"])]
    st.echarts_chart(opciones, height=height, alt=alt, **argumentos)
