# ESP32-S3 MicroPython IoT传感器程序

这是一个基于ESP32-S3芯片的MicroPython程序，实现了WiFi连接、温度采集、MQTT通信和WS2812B LED控制功能。

## 功能特性

1. **网络连接功能**
   - 稳定的WiFi连接
   - 网络连接异常处理机制
   - 自动重连功能

2. **温度采集功能**
   - 读取芯片片内温度传感器数据
   - 1Hz采样频率
   - 温度数据格式转换和校验

3. **MQTT通信功能**
   - 建立MQTT客户端连接
   - 发布温度数据到指定Topic
   - 订阅控制Topic接收指令
   - MQTT连接状态监控
   - QoS等级1设置

4. **WS2812B LED控制功能**
   - 在PIN48脚上初始化NeoPixel驱动
   - 根据订阅消息内容解析RGB颜色值
   - 控制LED亮灭状态
   - 支持亮度调节
   - 非法颜色值处理机制

5. **系统集成要求**
   - 各功能模块的协同工作
   - 合理的程序架构
   - 完善的异常处理
   - 调试日志输出

## 硬件要求

- ESP32-S3开发板
- WS2812B LED (连接到GPIO48)

## 软件依赖

- MicroPython固件 (ESP32-S3版本)
- umqtt.simple库 (通常包含在MicroPython中)
- neopixel库 (通常包含在MicroPython中)

## 配置参数

在程序顶部，你可以修改以下配置参数:

```python
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
TEMP_SAMPLE_INTERVAL = 1000  # 温度采样间隔(毫秒)
MQTT_QOS = 1  # MQTT服务质量等级
```

## 使用说明

1. 将程序上传到ESP32-S3开发板
2. 根据你的环境修改配置参数
3. 连接WS2812B LED到GPIO48引脚
4. 运行程序

## MQTT消息格式

### 温度数据发布

程序会定期发布温度数据到`esp32/s3/temperature`主题，格式如下:

```json
{
  "temperature": 25.6,
  "timestamp": 1234567890,
  "device_id": "esp32_s3_temp_sensor"
}
```

### LED控制订阅

程序会订阅`esp32/s3/control`主题，接收LED控制指令，格式如下:

```json
{
  "r": 255,         // 红色值 (0-255)
  "g": 0,           // 绿色值 (0-255)
  "b": 0,           // 蓝色值 (0-255)
  "brightness": 0.5 // 亮度 (0.0-1.0)
}
```

## 示例MQTT控制命令

- 设置LED为红色:
  ```json
  {"r": 255, "g": 0, "b": 0}
  ```

- 设置LED为蓝色，亮度50%:
  ```json
  {"r": 0, "g": 0, "b": 255, "brightness": 0.5}
  ```

- 关闭LED:
  ```json
  {"r": 0, "g": 0, "b": 0}
  ```

## 故障排除

### WiFi连接问题

- 检查SSID和密码是否正确
- 确保ESP32-S3在WiFi覆盖范围内
- 尝试重启设备

### MQTT连接问题

- 检查MQTT代理地址和端口是否正确
- 确认网络连接正常
- 检查防火墙设置

### ImportError: no module named 'umqtt'

如果遇到 `ImportError: no module named 'umqtt'` 错误，本项目已经提供了自定义MQTT客户端作为替代方案，无需安装额外的库。程序会自动检测并使用自定义MQTT客户端。

如果您仍想使用官方的 umqtt 库，有以下几种安装方法：

#### 方法1: 安装umqtt库(推荐)
1. 使用Thonny IDE连接到ESP32-S3
2. 在Thonny中打开工具 → 管理包
3. 搜索并安装`micropython-umqtt.simple`包

#### 方法2: 手动安装umqtt库
1. 从[MicroPython官方仓库](https://github.com/micropython/micropython-lib)下载umqtt.simple
2. 将下载的文件上传到ESP32-S3的根目录
3. 确保文件名为`umqtt`，包含`simple.py`子模块

#### 方法3: 使用预编译固件
1. 下载包含umqtt库的预编译MicroPython固件
2. 刷写固件到ESP32-S3

### 自定义MQTT客户端

本项目包含一个自定义的MQTT客户端实现 (`mqtt_client.py`)，它提供了与 umqtt.simple 兼容的API，包括以下功能：

- 连接/断开MQTT服务器
- 发布/订阅消息
- 设置回调函数处理接收到的消息
- 连接状态检查
- Ping功能

自定义MQTT客户端已经与主程序完全集成，无需额外配置。

### LED不工作

- 确认LED连接到GPIO48引脚
- 检查LED供电是否正常
- 确认LED型号为WS2812B

### 温度读数异常

- 温度传感器读数可能需要根据具体硬件进行校准
- 修改`read_internal_temperature()`函数中的转换公式

## 性能优化

- 温度采样间隔可根据需要调整
- 在不使用时可以降低MQTT消息频率以节省电量
- 调整主循环中的休眠时间以平衡响应性和功耗

## 安全考虑

- 在生产环境中，应使用加密的MQTT连接(MQTT over SSL)
- 考虑添加设备认证机制
- 对控制消息进行更严格的合法性验证

## 测试

项目包含两个测试脚本，用于验证各个模块的功能。

### 功能测试 (test.py)

`test.py` 脚本用于测试硬件功能，运行测试:

```python
# 在ESP32-S3上运行测试脚本
import test
```

测试脚本将检查:
- 系统信息
- LED功能
- 温度传感器
- WiFi连接

### MQTT客户端测试 (test_mqtt.py)

`test_mqtt.py` 脚本用于测试自定义MQTT客户端的功能，运行测试:

```python
# 在MicroPython REPL中执行
import test_mqtt
```

或者直接上传文件后运行:

```python
# 在MicroPython REPL中执行
exec(open('test_mqtt.py').read())
```

MQTT测试脚本将执行以下测试:
1. MQTT连接测试
2. 连接状态检查
3. Ping功能测试
4. 消息发布测试
5. 消息接收测试

默认使用公共MQTT测试服务器 `test.mosquitto.org`，您可以在脚本中修改连接参数以使用自己的MQTT服务器。

## 许可证

本项目采用MIT许可证。详见[LICENSE]文件。

## 贡献

欢迎提交问题报告和拉取请求。