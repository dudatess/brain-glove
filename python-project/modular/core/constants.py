"""
constants.py
Constantes e configurações globais do sistema de neuroreabilitação
Versão 2.0 - Com detecção automática e validação robusta
"""

import os
import platform
import logging
from pathlib import Path

# Configurar logger
logger = logging.getLogger('Constants')

# ============================================================
# PATHS E ARQUIVOS
# ============================================================
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(ROOT_DIR)  # Pasta acima de 'core'
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
IMAGES_FOLDER = os.path.join(ASSETS_DIR, "gesture-images")
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Criar diretórios se não existirem
for directory in [ASSETS_DIR, DATA_DIR, LOG_DIR, IMAGES_FOLDER]:
    Path(directory).mkdir(parents=True, exist_ok=True)

# Caminho para o executável do driver
PATH_TO_C_EXE = os.path.join(BASE_DIR, "TestGlove64.exe")

# Verificar caminhos alternativos se não encontrar
if not os.path.exists(PATH_TO_C_EXE):
    alternative_paths = [
        "./TestGlove64.exe",
        "../TestGlove64.exe",
        "TestGlove64.exe",
        os.path.join(os.getcwd(), "TestGlove64.exe")
    ]
    
    for alt_path in alternative_paths:
        if os.path.exists(alt_path):
            PATH_TO_C_EXE = os.path.abspath(alt_path)
            logger.info(f"Executável encontrado em: {PATH_TO_C_EXE}")
            break
    else:
        logger.warning(f"⚠️  Executável não encontrado em nenhum caminho padrão")

# ============================================================
# DETECÇÃO AUTOMÁTICA DE PORTA
# ============================================================
def detect_glove_port(preferred_port=None):
    """
    Detecta automaticamente a porta COM da luva 5DT.
    
    Args:
        preferred_port: Porta preferencial a tentar primeiro (ex: "COM3")
    
    Returns:
        str: Porta detectada ou porta padrão
    """
    system = platform.system()
    
    # Se porta preferencial foi especificada, tentar ela primeiro
    if preferred_port:
        logger.info(f"Usando porta especificada: {preferred_port}")
        return preferred_port
    
    try:
        import serial.tools.list_ports
        
        ports = list(serial.tools.list_ports.comports())
        
        if not ports:
            logger.warning("Nenhuma porta COM detectada")
            default = "COM3" if system == "Windows" else "/dev/ttyUSB0"
            logger.info(f"Usando porta padrão: {default}")
            return default
        
        # Log de todas as portas disponíveis
        logger.info(f"Portas disponíveis ({len(ports)}):")
        for port in ports:
            logger.info(f"  • {port.device}: {port.description}")
        
        # Critérios de busca para a luva 5DT
        priority_keywords = ['5dt', 'glove']  # Alta prioridade
        usb_keywords = ['usb', 'serial', 'ftdi', 'ch340', 'cp210', 'prolific']  # Média prioridade
        
        candidates = []
        
        for port in ports:
            description = port.description.lower()
            hwid = port.hwid.lower()
            combined = f"{description} {hwid}"
            
            # Pontuação de prioridade
            score = 0
            
            # Alta prioridade: menção direta à luva ou 5DT
            for keyword in priority_keywords:
                if keyword in combined:
                    score += 10
                    logger.debug(f"{port.device} pontuou +10 (keyword: {keyword})")
            
            # Média prioridade: dispositivos USB-Serial
            for keyword in usb_keywords:
                if keyword in combined:
                    score += 1
                    logger.debug(f"{port.device} pontuou +1 (keyword: {keyword})")
            
            if score > 0:
                candidates.append((score, port.device, port.description))
        
        # Ordenar por pontuação (maior primeiro)
        candidates.sort(reverse=True, key=lambda x: x[0])
        
        if candidates:
            selected_score, selected_port, selected_desc = candidates[0]
            logger.info(f"✓ Porta selecionada: {selected_port} (pontuação: {selected_score})")
            logger.info(f"  Descrição: {selected_desc}")
            return selected_port
        
        # Se não encontrou candidatos com keywords, usar primeira porta
        first_port = ports[0].device
        logger.warning(f"Nenhuma porta específica encontrada, usando primeira: {first_port}")
        return first_port
        
    except ImportError:
        logger.error("❌ Biblioteca 'pyserial' não instalada!")
        logger.error("   Instale com: pip install pyserial")
        default = "COM3" if system == "Windows" else "/dev/ttyUSB0"
        logger.info(f"Usando porta padrão: {default}")
        return default
    
    except Exception as e:
        logger.error(f"Erro ao detectar porta: {e}", exc_info=True)
        default = "COM3" if system == "Windows" else "/dev/ttyUSB0"
        return default


# ============================================================
# SERIAL / CONEXÃO
# ============================================================

# Porta padrão (pode ser sobrescrita)
_DEFAULT_PORT = "COM3" if platform.system() == "Windows" else "/dev/ttyUSB0"

# Detectar porta automaticamente ou usar padrão
# Para forçar uma porta específica, passe como argumento:
# GLOVE_CONNECTION_PORT = detect_glove_port("COM4")
GLOVE_CONNECTION_PORT = detect_glove_port()

# Configurações de comunicação serial (caso seja necessário no futuro)
BAUD_RATE = 115200
SERIAL_TIMEOUT = 0.05

# Intervalo de reconexão automática
RECONNECT_INTERVAL = 2.0  # segundos

# Número máximo de tentativas de reconexão
MAX_RECONNECT_ATTEMPTS = 5

# ============================================================
# SENSOR CONFIG
# ============================================================

SENSOR_NAMES = [
    "Thumb Near",       # 0  - Sensor próximo do polegar
    "Thumb Far",        # 1  - Sensor distal do polegar
    "Thumb/Index",      # 2  - Sensor entre polegar e indicador
    "Index Near",       # 3  - Sensor próximo do indicador
    "Index Far",        # 4  - Sensor distal do indicador
    "Index/Middle",     # 5  - Sensor entre indicador e médio
    "Middle Near",      # 6  - Sensor próximo do médio
    "Middle Far",       # 7  - Sensor distal do médio
    "Middle/Ring",      # 8  - Sensor entre médio e anelar
    "Ring Near",        # 9  - Sensor próximo do anelar
    "Ring Far",         # 10 - Sensor distal do anelar
    "Ring/Little",      # 11 - Sensor entre anelar e mínimo
    "Little Near",      # 12 - Sensor próximo do mínimo
    "Little Far",       # 13 - Sensor distal do mínimo
    "Thumb Palm",       # 14 - Sensor da palma (polegar)
    "Wrist Bend",       # 15 - Sensor de flexão do punho
    "Roll",             # 16 - Sensor de rotação (rolagem)
    "Pitch"             # 17 - Sensor de inclinação
]

NUM_SENSORS = len(SENSOR_NAMES)
DEFAULT_SAMPLE_RATE_HZ = 60  # Frequência de amostragem padrão

# ============================================================
# CALIBRAÇÃO
# ============================================================

# Configurações padrão de calibração
DEFAULT_CALIBRATION_CYCLES = 10         # Número de ciclos
DEFAULT_CYCLE_DURATION = 5.0            # Duração de cada fase (segundos)
DEFAULT_CONTINUOUS_MODE = False         # Modo contínuo desabilitado por padrão

# Tempos específicos por fase
CALIBRATION_OPEN_TIME = 5    # Tempo para manter mão aberta (segundos)
CALIBRATION_CLOSE_TIME = 5   # Tempo para manter mão fechada (segundos)
CALIBRATION_REST_TIME = 1    # Tempo de descanso entre ciclos (segundos)

# Modos de calibração
CALIBRATION_MODES = {
    "continuous": 0,  # Calibração contínua (fluxo livre)
    "cycle": 1,       # Calibração por ciclos (guiada)
    "manual": 2       # Calibração manual (usuário controla)
}

# Validação de dados de calibração
MIN_CALIBRATION_CYCLES = 3   # Mínimo de ciclos necessários
MAX_CALIBRATION_CYCLES = 50  # Máximo de ciclos permitidos

# ============================================================
# PROCESSAMENTO DE DADOS
# ============================================================

# Filtro de artefatos (remoção de outliers)
ARTIFACT_WINDOW_SIZE = 5      # Tamanho da janela para média móvel
ARTIFACT_THRESHOLD = 0.15     # Threshold para detectar outliers (0-1)

# Filtro passa-baixa (suavização)
SMOOTHING_ENABLED = True      # Habilitar suavização
SMOOTHING_ALPHA = 0.3         # Fator de suavização (0-1, menor = mais suave)

# Limites de valores válidos dos sensores
SENSOR_MIN_VALUE = 0.0        # Valor mínimo esperado
SENSOR_MAX_VALUE = 1.0        # Valor máximo esperado

# ============================================================
# LED COLORS / STATUS
# ============================================================

LED_COLORS = {
    "connected": "#10b981",      # Verde (conectado)
    "disconnected": "#ef4444",   # Vermelho (desconectado)
    "reading": "#f59e0b",        # Laranja (lendo dados)
    "calibrating": "#3b82f6",    # Azul (calibrando)
    "error": "#dc2626",          # Vermelho escuro (erro)
    "idle": "#6b7280"            # Cinza (ocioso)
}

# Cores da interface (para consistência visual)
COLORS = {
    'primary': '#3b82f6',        # Azul
    'success': '#10b981',        # Verde
    'danger': '#ef4444',         # Vermelho
    'warning': '#f59e0b',        # Laranja
    'background': '#f0f4f8',     # Cinza claro
    'card': '#ffffff',           # Branco
    'text_primary': '#1a202c',   # Preto
    'text_secondary': '#4a5568', # Cinza escuro
    'border': '#e5e7eb'          # Cinza borda
}

# ============================================================
# IMAGEM DE GESTOS
# ============================================================

# Mapeamento de IDs de gestos para arquivos de imagem
IMAGE_MAP = {
    i: f"{i}.png" for i in range(16)
}

# Adicionar imagem padrão para gesto desconhecido
IMAGE_MAP[-1] = "unknown.png"

# Tamanho padrão das imagens (pixels)
DEFAULT_IMAGE_SIZE = (400, 400)

# ============================================================
# INTERFACE / UI
# ============================================================

# Tamanho da janela (percentual da tela)
WINDOW_SCREEN_RATIO = 0.90    # 90% da tela

# Tamanho mínimo da janela
MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 600

# Taxa de atualização da interface (ms)
UI_UPDATE_INTERVAL_STATUS = 200   # Verificação de status
UI_UPDATE_INTERVAL_DATA = 20      # Processamento de dados

# ============================================================
# LOGGING
# ============================================================

LOG_LEVEL = logging.INFO
LOG_FILE = os.path.join(LOG_DIR, "glove_app.log")
LOG_FORMAT = "%(asctime)s [%(name)s][%(levelname)s] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Tamanho máximo do arquivo de log (bytes)
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB

# Número de backups de log
LOG_BACKUP_COUNT = 3

# ============================================================
# DATABASE / HISTÓRICO
# ============================================================

# Arquivo de banco de dados para histórico de sessões
DB_FILE = os.path.join(DATA_DIR, "sessions.db")

# Número máximo de sessões a manter no histórico
MAX_HISTORY_SESSIONS = 100

# ============================================================
# APLICAÇÃO
# ============================================================

APP_NAME = "Sistema de Neuroreabilitação"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Brain Glove Team"
APP_DESCRIPTION = "Sistema de reabilitação com Luva 5DT Data Glove"

# ============================================================
# VALIDAÇÃO DE CONFIGURAÇÕES
# ============================================================

def validate_configuration():
    """
    Valida todas as configurações do sistema.
    
    Returns:
        tuple: (is_valid, warnings, errors)
    """
    warnings = []
    errors = []
    is_valid = True
    
    # Validar executável
    if not os.path.exists(PATH_TO_C_EXE):
        errors.append(f"❌ Executável não encontrado: {PATH_TO_C_EXE}")
        is_valid = False
    else:
        logger.info(f"✓ Executável encontrado: {PATH_TO_C_EXE}")
    
    # Validar pasta de imagens
    if not os.path.exists(IMAGES_FOLDER):
        warnings.append(f"⚠️  Pasta de imagens não encontrada: {IMAGES_FOLDER}")
        logger.warning(f"Pasta de imagens será criada: {IMAGES_FOLDER}")
        Path(IMAGES_FOLDER).mkdir(parents=True, exist_ok=True)
    else:
        # Verificar se há imagens
        image_count = len([f for f in os.listdir(IMAGES_FOLDER) if f.endswith('.png')])
        if image_count == 0:
            warnings.append(f"⚠️  Nenhuma imagem encontrada em {IMAGES_FOLDER}")
        else:
            logger.info(f"✓ {image_count} imagens encontradas")
    
    # Validar biblioteca pyserial
    try:
        import serial
        logger.info("✓ Biblioteca 'pyserial' instalada")
    except ImportError:
        errors.append("❌ Biblioteca 'pyserial' não instalada")
        errors.append("   Execute: pip install pyserial")
        is_valid = False
    
    # Validar número de sensores
    if NUM_SENSORS != 18:
        warnings.append(f"⚠️  Número não padrão de sensores: {NUM_SENSORS} (esperado: 18)")
    
    # Validar porta
    if not GLOVE_CONNECTION_PORT:
        errors.append("❌ Porta de conexão não definida")
        is_valid = False
    else:
        logger.info(f"✓ Porta configurada: {GLOVE_CONNECTION_PORT}")
    
    # Validar configurações de calibração
    if DEFAULT_CALIBRATION_CYCLES < MIN_CALIBRATION_CYCLES:
        warnings.append(
            f"⚠️  Número de ciclos muito baixo: {DEFAULT_CALIBRATION_CYCLES} "
            f"(mínimo recomendado: {MIN_CALIBRATION_CYCLES})"
        )
    
    # Validar diretórios
    for name, path in [("DATA", DATA_DIR), ("LOG", LOG_DIR), ("ASSETS", ASSETS_DIR)]:
        if not os.path.exists(path):
            logger.info(f"Criando diretório {name}: {path}")
            Path(path).mkdir(parents=True, exist_ok=True)
    
    return is_valid, warnings, errors


def print_configuration_summary():
    """Imprime resumo das configurações para debug"""
    print("\n" + "="*70)
    print("📋 CONFIGURAÇÃO DO SISTEMA")
    print("="*70)
    print(f"Aplicação:     {APP_NAME} v{APP_VERSION}")
    print(f"Executável:    {PATH_TO_C_EXE}")
    print(f"Porta:         {GLOVE_CONNECTION_PORT}")
    print(f"Sensores:      {NUM_SENSORS}")
    print(f"Taxa:          {DEFAULT_SAMPLE_RATE_HZ} Hz")
    print(f"Calibração:    {DEFAULT_CALIBRATION_CYCLES} ciclos")
    print(f"Imagens:       {IMAGES_FOLDER}")
    print(f"Logs:          {LOG_FILE}")
    print("="*70 + "\n")


# ============================================================
# EXECUÇÃO AUTOMÁTICA DE VALIDAÇÃO
# ============================================================

# Validar ao importar o módulo
if __name__ != "__main__":
    is_valid, warnings, errors = validate_configuration()
    
    # Exibir avisos
    for warning in warnings:
        logger.warning(warning)
    
    # Exibir erros
    for error in errors:
        logger.error(error)
    
    # Se houver erros críticos, alertar
    if not is_valid:
        logger.error("⚠️  CONFIGURAÇÃO INVÁLIDA - O sistema pode não funcionar corretamente")
    else:
        logger.info("✓ Configuração validada com sucesso")
    
    # Log resumido das configurações
    logger.info(f"Sistema configurado: {APP_NAME} v{APP_VERSION}")
    logger.info(f"  Executável: {os.path.basename(PATH_TO_C_EXE)}")
    logger.info(f"  Porta: {GLOVE_CONNECTION_PORT}")
    logger.info(f"  Sensores: {NUM_SENSORS}")


# Para debug, descomentar a linha abaixo:
# print_configuration_summary()