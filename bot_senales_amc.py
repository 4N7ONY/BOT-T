import tkinter as tk
from tkinter import messagebox, scrolledtext
import pandas as pd
import ta
import time
import threading
from iqoptionapi.stable_api import IQ_Option
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- LÓGICA GLOBAL ---
api = None
ACTIVO = "EURUSD"
conexion_exitosa = False
df_global = pd.DataFrame()

def intentar_conexion():
    global api, conexion_exitosa
    correo = entry_correo.get()
    clave = entry_clave.get()
    
    if not correo or not clave:
        messagebox.showerror("Error", "¡Pon tus datos pues! No soy adivina 🙄")
        return
        
    btn_login.config(text="Conectando...", state=tk.DISABLED)
    ventana.update()
    
    api = IQ_Option(correo, clave)
    check, reason = api.connect()
    
    if check:
        conexion_exitosa = True
        # Magia: Ocultamos el login y mostramos el dashboard principal
        frame_login.pack_forget()
        frame_dashboard.pack(fill=tk.BOTH, expand=True)
        
        # Jalar los saldos de tu cuenta
        api.change_balance("REAL")
        saldo_real = api.get_balance()
        api.change_balance("PRACTICE")
        saldo_demo = api.get_balance()
        
        lbl_saldos.config(text=f"💰 SALDO REAL: ${saldo_real}   |   🛡️ SALDO DEMO: ${saldo_demo}")
        
        # Volvemos a la de práctica por seguridad antes de operar
        api.change_balance("PRACTICE")
        
        # Arrancamos el gráfico en vivo en segundo plano
        iniciar_grafico()
    else:
        messagebox.showerror("Error", f"Fallo al conectar: {reason} ❌")
        btn_login.config(text="ENTRAR AL MATRIX", state=tk.NORMAL)

def actualizar_grafico():
    while conexion_exitosa:
        try:
            # Jalamos 50 velas para el gráfico
            velas = api.get_candles(ACTIVO, 60, 50, time.time())
            if velas:
                cierres = [v['close'] for v in velas]
                global df_global
                df_global = pd.DataFrame({'close': cierres})
                
                # Actualizamos el dibujito del gráfico
                ax.clear()
                ax.plot(df_global['close'], color='#00ff00', linewidth=2)
                ax.set_title(f"Gráfico en vivo: {ACTIVO}", color='white', pad=10)
                ax.set_facecolor('#1e1e1e')
                fig.patch.set_facecolor('#1e1e1e')
                ax.tick_params(colors='white')
                canvas.draw()
        except Exception:
            pass # Si hay un mini corte de internet, lo ignoramos y sigue
        time.sleep(2) # Se actualiza cada 2 segundos

def iniciar_grafico():
    hilo = threading.Thread(target=actualizar_grafico)
    hilo.daemon = True
    hilo.start()

def calcular_prediccion():
    if df_global.empty:
        caja_texto.insert(tk.END, "⚠️ Aguanta, el gráfico recién está cargando...\n", "venta")
        return

    caja_texto.insert(tk.END, f"\n🔍 Calculando francotirador en {ACTIVO}...\n")
    ventana.update()

    # Copiamos la tabla actual para no cruzar cables
    df = df_global.copy()
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    indicator_bb = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
    df['bb_alta'] = indicator_bb.bollinger_hband()
    df['bb_baja'] = indicator_bb.bollinger_lband()

    ultima_vela = df.iloc[-1]
    precio = ultima_vela['close']
    rsi = ultima_vela['rsi']
    bb_alta = ultima_vela['bb_alta']
    bb_baja = ultima_vela['bb_baja']

    caja_texto.insert(tk.END, f"📊 Precio: {precio:.5f} | RSI: {rsi:.2f}\n")
    
    # Estrategia Francotirador
    if precio < bb_baja and rsi < 30:
        caja_texto.insert(tk.END, "🟢 ¡COMPRA! (Sube ⬆️) - Rebote inminente.\n", "compra")
    elif precio > bb_alta and rsi > 70:
        caja_texto.insert(tk.END, "🔴 ¡VENTA! (Baja ⬇️) - Caída inminente.\n", "venta")
    else:
        caja_texto.insert(tk.END, "⏳ NEUTRAL. Mercado quieto.\n", "neutral")
    
    caja_texto.insert(tk.END, "-"*45 + "\n")
    caja_texto.see(tk.END)

# --- INTERFAZ GRÁFICA MAESTRA ---
ventana = tk.Tk()
ventana.title("AMC Digital - Sistema Central")
ventana.geometry("600x750")
ventana.configure(bg="#1e1e1e")

# --- FRAME 1: LOGIN ---
frame_login = tk.Frame(ventana, bg="#1e1e1e")
frame_login.pack(pady=150)

tk.Label(frame_login, text="🔥 AMC DIGITAL 🔥", font=("Helvetica", 28, "bold"), bg="#1e1e1e", fg="#00ff00").pack(pady=15)

tk.Label(frame_login, text="Correo de IQ Option:", font=("Helvetica", 12), bg="#1e1e1e", fg="white").pack()
entry_correo = tk.Entry(frame_login, width=35, font=("Helvetica", 12), bg="#2d2d2d", fg="white", insertbackground="white")
entry_correo.pack(pady=5)

tk.Label(frame_login, text="Contraseña:", font=("Helvetica", 12), bg="#1e1e1e", fg="white").pack()
entry_clave = tk.Entry(frame_login, width=35, font=("Helvetica", 12), show="*", bg="#2d2d2d", fg="white", insertbackground="white")
entry_clave.pack(pady=5)

btn_login = tk.Button(frame_login, text="ENTRAR AL MATRIX", font=("Helvetica", 14, "bold"), bg="#2196F3", fg="white", command=intentar_conexion, cursor="hand2")
btn_login.pack(pady=25)

# --- FRAME 2: DASHBOARD (Oculto hasta hacer login) ---
frame_dashboard = tk.Frame(ventana, bg="#1e1e1e")

# Saldos
lbl_saldos = tk.Label(frame_dashboard, text="Cargando tus millones...", font=("Helvetica", 14, "bold"), bg="#1e1e1e", fg="#ffcc00")
lbl_saldos.pack(pady=15)

# Gráfico Visual (Matplotlib dentro de Tkinter)
fig, ax = plt.subplots(figsize=(6, 3), dpi=100)
fig.patch.set_facecolor('#1e1e1e')
ax.set_facecolor('#1e1e1e')
ax.tick_params(colors='white')
canvas = FigureCanvasTkAgg(fig, master=frame_dashboard)
canvas.get_tk_widget().pack(pady=5)

# Botón Predicción Gigante
btn_predecir = tk.Button(frame_dashboard, text="⚡ LANZAR PREDICCIÓN", font=("Helvetica", 16, "bold"), bg="#4CAF50", fg="white", command=calcular_prediccion, cursor="hand2")
btn_predecir.pack(pady=15)

# Consola de Resultados
caja_texto = scrolledtext.ScrolledText(frame_dashboard, width=70, height=8, bg="#2d2d2d", fg="white", font=("Consolas", 10))
caja_texto.pack(pady=5)
caja_texto.tag_config("compra", foreground="#00ff00", font=("Consolas", 10, "bold")) 
caja_texto.tag_config("venta", foreground="#ff3333", font=("Consolas", 10, "bold"))
caja_texto.tag_config("neutral", foreground="#ffcc00") 
caja_texto.insert(tk.END, "🤖 Central AMC inicializada. Monitoreando...\n")

ventana.mainloop()