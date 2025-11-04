# ESP32-S3 IoT传感器配置文件
# 修改这些参数以适应你的环境

# WiFi配置
WIFI_SSID = 'your_wifi_ssid'
WIFI_PASSWORD = 'your_wifi_password'

# MQTT配置
MQTT_CLIENT_ID = b'esp32_s3_temp_sensor'
MQTT_BROKER = 'mqtt.eclipseprojects.io'  # MQTT代理地址
MQTT_PORT = 1883
MQTT_USER = b''  # MQTT用户名
MQTT_PASSWORD = b''  # MQTT密码

# 主题配置
TEMP_TOPIC = b'esp32/s3/temperature'  # 温度数据发布主题
CONTROL_TOPIC = b'esp32/s3/control'   # LED控制订阅主题

# 硬件配置
LED_PIN = 48  # WS2812B LED连接的GPIO引脚
NUM_LEDS = 1  # LED数量

# 性能配置
TEMP_SAMPLE_INTERVAL = 15000  # 温度采样间隔(毫秒)
MQTT_QOS = 1  # MQTT服务质量等级

# 调试配置
DEBUG = True  # 是否启用调试日志
LOG_INTERVAL = 5000  # 日志输出间隔(毫秒)，0表示每次都输出
LOG_LEVEL = 'INFO'  # 日志级别: DEBUG, INFO, WARNING, ERROR

# 安全配置
ENABLE_AUTH = False  # 是否启用MQTT认证
AUTH_TOKEN = ''  # 认证令牌

# LED默认配置
DEFAULT_LED_COLOR = {'r': 0, 'g': 0, 'b': 0}
DEFAULT_LED_BRIGHTNESS = 0.5

# 温度传感器配置
TEMP_CALIBRATION_OFFSET = 0.0  # 温度校准偏移量
TEMP_FILTER_ENABLED = True  # 是否启用温度滤波
TEMP_FILTER_SAMPLES = 5  # 温度滤波样本数