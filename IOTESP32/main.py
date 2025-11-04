import network
import time
import machine
import json
from machine import Pin, ADC
import neopixel
import esp32

# 尝试导入umqtt库，如果失败则使用自定义MQTT客户端
from umqtt.simple import MQTTClient
USE_UMQTT = True

# 导入配置参数
try:
    import config
except ImportError:
    print("错误: 无法导入config.py，请确保配置文件存在")
    raise

# 使用配置参数
WIFI_SSID = config.WIFI_SSID
WIFI_PASSWORD = config.WIFI_PASSWORD
MQTT_CLIENT_ID = config.MQTT_CLIENT_ID
MQTT_BROKER = config.MQTT_BROKER
MQTT_PORT = config.MQTT_PORT
MQTT_USER = config.MQTT_USER
MQTT_PASSWORD = config.MQTT_PASSWORD
TEMP_TOPIC = config.TEMP_TOPIC
CONTROL_TOPIC = config.CONTROL_TOPIC
LED_PIN = config.LED_PIN
NUM_LEDS = config.NUM_LEDS
TEMP_SAMPLE_INTERVAL = config.TEMP_SAMPLE_INTERVAL
MQTT_QOS = config.MQTT_QOS
DEBUG = getattr(config, 'DEBUG', True)
DEFAULT_LED_COLOR = getattr(config, 'DEFAULT_LED_COLOR', {'r': 0, 'g': 0, 'b': 0})
DEFAULT_LED_BRIGHTNESS = getattr(config, 'DEFAULT_LED_BRIGHTNESS', 0.5)
TEMP_CALIBRATION_OFFSET = getattr(config, 'TEMP_CALIBRATION_OFFSET', 0.0)
TEMP_FILTER_ENABLED = getattr(config, 'TEMP_FILTER_ENABLED', True)
TEMP_FILTER_SAMPLES = getattr(config, 'TEMP_FILTER_SAMPLES', 5)
LOG_LEVEL = getattr(config, 'LOG_LEVEL', 'INFO')

# 全局变量
wlan = None
mqtt_client = None
led = None
last_temp_time = 0
led_state = DEFAULT_LED_COLOR.copy()
led_state['brightness'] = DEFAULT_LED_BRIGHTNESS
temp_samples = []  # 用于温度滤波的样本数组

# 日志函数 - 简化版
# 注意：原log函数导致程序异常，已替换为简单的print函数
def log(message, level='INFO'):
    print(f'[{level}] {message}')

# 配置验证函数
def validate_config():
    errors = []
    
    # 验证WiFi配置
    if not WIFI_SSID:
        errors.append('WiFi SSID未配置')
    if not WIFI_PASSWORD:
        errors.append('WiFi密码未配置')
    
    # 验证MQTT配置
    if not MQTT_BROKER:
        errors.append('MQTT代理地址未配置')
    if not MQTT_CLIENT_ID:
        errors.append('MQTT客户端ID未配置')
    if MQTT_PORT < 1 or MQTT_PORT > 65535:
        errors.append('无效的MQTT端口')
    
    # 验证LED配置
    if LED_PIN is None:
        errors.append('LED引脚未配置')
    if NUM_LEDS < 1:
        errors.append('LED数量必须大于0')
    
    # 验证温度采样配置
    if TEMP_SAMPLE_INTERVAL < 100:
        errors.append('温度采样间隔不能小于100ms')
    
    # 验证MQTT QoS
    if MQTT_QOS < 0 or MQTT_QOS > 2:
        errors.append('MQTT QoS必须在0-2之间')
    
    if errors:
        log('配置验证失败:')
        for error in errors:
            log(f'  - {error}', 'ERROR')
        return False
    
    log('配置验证通过')
    return True

# 网络状态监控函数
def monitor_network_status():
    global wlan
    
    try:
        if not wlan:
            log('WiFi接口未初始化', 'WARNING')
            return False
        
        if not wlan.isconnected():
            log('WiFi连接已断开', 'WARNING')
            return False
        
        # 获取网络信息
        ifconfig = wlan.ifconfig()
        log(f'网络状态 - IP: {ifconfig[0]}, 子网掩码: {ifconfig[1]}, 网关: {ifconfig[2]}, DNS: {ifconfig[3]}', 'DEBUG')
        
        # 获取WiFi信号强度
        try:
            rssi = wlan.status('rssi')
            log(f'WiFi信号强度: {rssi} dBm', 'DEBUG')
        except:
            pass  # 不是所有MicroPython实现都支持RSSI
        
        return True
    except Exception as e:
        log(f'网络状态监控错误: {e}', 'ERROR')
        return False

# WiFi连接功能
def do_connect():
    global wlan
    print('connecting to network...')
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    return True

# 为了兼容性，添加connect_wifi函数
def connect_wifi():
    return do_connect()

# 检查WiFi连接状态并自动重连
def check_wifi_connection():
    global wlan
    if not wlan or not wlan.isconnected():
        log('WiFi连接断开，尝试重新连接...')
        return do_connect()
    return True

# 温度采集功能
def read_internal_temperature():
    global temp_samples
    try:
        # 直接使用ESP32片内温度传感器（摄氏度）
        try:
            temperature = esp32.mcu_temperature()
        except AttributeError:
            # 某些固件可能不提供mcu_temperature，尝试raw_temperature作为近似
            try:
                temperature = esp32.raw_temperature()
            except Exception as e:
                log(f'固件不支持片内温度接口: {e}', 'ERROR')
                return None

        # 应用校准偏移量
        temperature = float(temperature) + TEMP_CALIBRATION_OFFSET

        # 温度滤波（可选）
        if TEMP_FILTER_ENABLED:
            temp_samples.append(temperature)
            # 保持样本数量不超过配置值
            if len(temp_samples) > TEMP_FILTER_SAMPLES:
                temp_samples.pop(0)

            # 计算平均值
            if len(temp_samples) >= TEMP_FILTER_SAMPLES:
                temperature = sum(temp_samples) / len(temp_samples)
                log(f'温度滤波处理，样本数: {len(temp_samples)}, 平均值: {temperature:.2f}°C', 'DEBUG')

        return temperature
    except Exception as e:
        log(f'读取温度错误: {e}', 'ERROR')
        return None

# MQTT回调函数
def mqtt_callback(topic, msg):
    global led_state
    try:
        log(f'收到MQTT消息: 主题={topic.decode()}, 内容={msg.decode()}', 'DEBUG')
        
        # 验证主题
        if topic != CONTROL_TOPIC:
            log(f'收到未知主题消息: {topic.decode()}', 'WARNING')
            return
            
        # 解析控制消息
        try:
            control_data = json.loads(msg.decode())
            log(f'解析控制消息成功: {control_data}', 'DEBUG')
            
            # 验证消息格式
            if not isinstance(control_data, dict):
                log('控制消息格式错误: 不是字典类型', 'WARNING')
                return
                
            # 验证颜色值范围
            valid_keys = ['r', 'g', 'b', 'brightness']
            for key in control_data:
                if key not in valid_keys:
                    log(f'控制消息包含未知键: {key}', 'WARNING')
                    continue
                    
            # 更新LED状态
            updated = False
            if 'r' in control_data:
                new_r = max(0, min(255, int(control_data['r'])))
                if new_r != led_state['r']:
                    led_state['r'] = new_r
                    updated = True
                    
            if 'g' in control_data:
                new_g = max(0, min(255, int(control_data['g'])))
                if new_g != led_state['g']:
                    led_state['g'] = new_g
                    updated = True
                    
            if 'b' in control_data:
                new_b = max(0, min(255, int(control_data['b'])))
                if new_b != led_state['b']:
                    led_state['b'] = new_b
                    updated = True
                    
            if 'brightness' in control_data:
                new_brightness = max(0, min(1.0, float(control_data['brightness'])))
                if new_brightness != led_state['brightness']:
                    led_state['brightness'] = new_brightness
                    updated = True
            
            # 更新LED
            if updated:
                update_led()
                log(f'LED状态更新: R={led_state["r"]}, G={led_state["g"]}, B={led_state["b"]}, 亮度={led_state["brightness"]}')
            else:
                log('LED状态无变化', 'DEBUG')
                
        except json.JSONDecodeError:
            log('无效的JSON控制消息', 'ERROR')
        except (ValueError, TypeError) as e:
            log(f'控制消息值类型错误: {e}', 'ERROR')
        except Exception as e:
            log(f'处理控制消息错误: {e}', 'ERROR')
    except Exception as e:
        log(f'MQTT回调错误: {e}', 'ERROR')

# MQTT连接功能
def connect_mqtt():
    global mqtt_client, USE_UMQTT
    try:
        # 验证配置参数
        if not MQTT_CLIENT_ID or not MQTT_BROKER:
            log('MQTT配置参数缺失', 'ERROR')
            return False
            
        log(f'尝试连接MQTT代理: {MQTT_BROKER}:{MQTT_PORT}', 'INFO')
        
        # 创建MQTT客户端（仅使用umqtt.simple）
        mqtt_client = MQTTClient(
            MQTT_CLIENT_ID,
            MQTT_BROKER,
            MQTT_PORT,
            MQTT_USER,
            MQTT_PASSWORD,
            keepalive=getattr(config, 'MQTT_KEEPALIVE', 60)
        )
        mqtt_client.set_callback(mqtt_callback)
        
        # 尝试连接
        mqtt_client.connect()
        
        # 订阅控制主题
        mqtt_client.subscribe(CONTROL_TOPIC, MQTT_QOS)
        
        log(f'MQTT连接成功: {MQTT_BROKER}:{MQTT_PORT}, 客户端ID: {MQTT_CLIENT_ID}')
        return True
    except OSError as e:
        log(f'MQTT网络错误: {e}', 'ERROR')
        return False
    except Exception as e:
        log(f'MQTT连接错误: {e}', 'ERROR')
        return False

# 检查MQTT连接状态（仅使用umqtt.simple）
def check_mqtt_connection():
    global mqtt_client
    try:
        if not mqtt_client:
            log('MQTT客户端未初始化，尝试连接...')
            return connect_mqtt()
        
        # 使用ping进行连接活性检查
        ping_interval = getattr(config, 'MQTT_PING_INTERVAL', 30)
        current_time = time.ticks_ms()
        last_ping = getattr(mqtt_client, '_last_ping', 0)
        
        if time.ticks_diff(current_time, last_ping) > ping_interval * 1000:
            try:
                mqtt_client.ping()
                mqtt_client._last_ping = current_time
            except Exception as e:
                log(f'MQTT ping失败: {e}', 'WARNING')
                return connect_mqtt()
        
        return True
    except Exception as e:
        log(f'检查MQTT连接状态失败: {e}', 'ERROR')
        return False

# 发布温度数据
def publish_temperature(temperature):
    global mqtt_client, USE_UMQTT
    try:
        if not check_mqtt_connection():
            return False

        # 验证温度值
        if temperature is None or not isinstance(temperature, (int, float)):
            log('无效的温度值', 'ERROR')
            return False

        # 创建消息
        device_id = MQTT_CLIENT_ID.decode('utf-8') if isinstance(MQTT_CLIENT_ID, bytes) else MQTT_CLIENT_ID

        # 添加额外字段
        message_data = {
            'temperature': round(temperature, 2),  # 保留两位小数
            'timestamp': time.ticks_ms(),
            'device_id': device_id,
            'unit': '°C'
        }

        # 添加电池状态（如果可用）
        if hasattr(config, 'INCLUDE_BATTERY_STATUS') and config.INCLUDE_BATTERY_STATUS:
            try:
                battery_level = machine.ADC(machine.Pin(machine.ADC.VOLTAGE)).read()
                message_data['battery'] = round(battery_level / 4096 * 3.3, 2)  # 假设3.3V参考电压
            except Exception as e:
                log(f'读取电池状态失败: {e}', 'WARNING')

        message = json.dumps(message_data)
        msg_payload = message if isinstance(message, bytes) else message.encode()

        # 发布消息（仅使用umqtt.simple）
        try:
            mqtt_client.publish(TEMP_TOPIC, msg_payload, retain=False, qos=MQTT_QOS)
            log(f'温度数据已发布: {temperature:.2f}°C', 'DEBUG')
            return True
        except OSError as e:
            # 处理网络连接错误，尝试重连后重试一次
            err = e.args[0] if hasattr(e, 'args') and e.args else None
            if err in (104, 128):  # ECONNRESET, ENOTCONN
                log(f'发布失败({err})，尝试重连MQTT后重试', 'WARNING')
                try:
                    if mqtt_client:
                        try:
                            mqtt_client.disconnect()
                        except:
                            pass
                    mqtt_client = None
                    if connect_mqtt():
                        try:
                            mqtt_client.publish(TEMP_TOPIC, msg_payload, retain=False, qos=MQTT_QOS)
                            log(f'温度数据已发布(重试成功): {temperature:.2f}°C', 'DEBUG')
                            return True
                        except Exception as e2:
                            log(f'重连后发布仍失败: {e2}', 'ERROR')
                            return False
                    else:
                        log('MQTT重连失败，无法发布温度数据', 'ERROR')
                        return False
                except Exception as e3:
                    log(f'处理重连过程异常: {e3}', 'ERROR')
                    return False
            else:
                log(f'发布温度数据失败: {e}', 'ERROR')
                return False
        except Exception as e:
            log(f'发布温度数据失败: {e}', 'ERROR')
            return False
    except Exception as e:
        log(f'发布温度数据失败: {e}', 'ERROR')
        return False

# WS2812B LED控制功能
def init_led():
    global led
    try:
        # 验证配置参数
        if LED_PIN is None or NUM_LEDS is None:
            log('LED配置参数缺失', 'ERROR')
            return False
            
        log(f'初始化LED: PIN={LED_PIN}, 数量={NUM_LEDS}', 'INFO')
        led = neopixel.NeoPixel(Pin(LED_PIN), NUM_LEDS)
        
        # 初始设置为关闭所有LED
        for i in range(NUM_LEDS):
            led[i] = (0, 0, 0)
        led.write()
        log(f'LED初始化成功，引脚: {LED_PIN}, 数量: {NUM_LEDS}')
        return True
    except ValueError as e:
        log(f'LED参数值错误: {e}', 'ERROR')
        return False
    except OSError as e:
        log(f'LED硬件访问错误: {e}', 'ERROR')
        return False
    except Exception as e:
        log(f'LED初始化失败: {e}', 'ERROR')
        return False

# 更新LED状态
def update_led():
    global led, led_state
    try:
        if not led:
            log('LED未初始化', 'WARNING')
            return False
            
        # 验证LED状态
        if not all(key in led_state for key in ['r', 'g', 'b', 'brightness']):
            log('LED状态数据不完整', 'ERROR')
            return False
            
        # 应用亮度调节
        r = int(led_state['r'] * led_state['brightness'])
        g = int(led_state['g'] * led_state['brightness'])
        b = int(led_state['b'] * led_state['brightness'])
        
        # 确保颜色值在有效范围内
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        log(f'设置LED颜色: R={r}, G={g}, B={b}, 亮度={led_state["brightness"]}', 'DEBUG')
        
        # 设置所有LED颜色
        for i in range(NUM_LEDS):
            led[i] = (r, g, b)
        led.write()
        return True
    except Exception as e:
        log(f'更新LED失败: {e}', 'ERROR')
        return False

# 程序初始化
def init():
    log('初始化ESP32-S3 IoT传感器程序')
    
    # 验证配置
    if not validate_config():
        log('配置验证失败，程序退出', 'ERROR')
        return False
    
    # 显示系统信息
    log(f'系统信息:')
    try:
        import sys
        log(f'  - MicroPython版本: {sys.implementation[0]} {sys.implementation[1]}')
    except Exception as e:
        log(f'  - 获取MicroPython版本失败: {e}', 'WARNING')
    
    log(f'  - 设备ID: {MQTT_CLIENT_ID.decode("utf-8") if isinstance(MQTT_CLIENT_ID, bytes) else MQTT_CLIENT_ID}')
    log(f'  - WiFi SSID: {WIFI_SSID}')
    log(f'  - MQTT代理: {MQTT_BROKER}:{MQTT_PORT}')
    log(f'  - 温度采样间隔: {TEMP_SAMPLE_INTERVAL}ms')
    log(f'  - LED引脚: {LED_PIN}, 数量: {NUM_LEDS}')
    log(f'  - 温度滤波: {"启用" if TEMP_FILTER_ENABLED else "禁用"}')
    if TEMP_FILTER_ENABLED:
        log(f'  - 滤波样本数: {TEMP_FILTER_SAMPLES}')
    log(f'  - 温度校准偏移: {TEMP_CALIBRATION_OFFSET}°C')
    log(f'  - 日志级别: {LOG_LEVEL}')
    
    # 初始化LED
    if not init_led():
        log('LED初始化失败，程序退出', 'ERROR')
        return False
    
    # 连接WiFi
    if not do_connect():
        log('WiFi连接失败，程序退出', 'ERROR')
        return False
    
    # 连接MQTT
    if not connect_mqtt():
        log('MQTT连接失败，程序退出', 'ERROR')
        return False
    
    log('初始化完成')
    return True

# 主循环
def main_loop():
    global last_temp_time, mqtt_client
    
    log('进入主循环')
    
    # 错误计数器字典
    error_counts = {
        'wifi': 0,
        'mqtt': 0,
        'temp': 0
    }
    max_error_count = 5
    
    # 状态检查时间跟踪
    last_status_check = 0
    last_mqtt_ping = 0
    
    while True:
        try:
            current_time = time.ticks_ms()
            
            # 定期检查网络状态(每30秒)
            if time.ticks_diff(current_time, last_status_check) > 30000:
                last_status_check = current_time
                
                # 监控网络状态
                monitor_network_status()
                
                # 检查WiFi连接
                if not check_wifi_connection():
                    error_counts['wifi'] += 1
                    log(f'WiFi连接失败 ({error_counts["wifi"]}/{max_error_count})，等待后重试', 'ERROR')
                    if error_counts['wifi'] >= max_error_count:
                        log('WiFi连接错误次数过多，重启网络模块', 'ERROR')
                        wlan.active(False)
                        time.sleep(2)
                        wlan.active(True)
                        error_counts['wifi'] = 0
                    time.sleep(5)
                    continue
                else:
                    if error_counts['wifi'] > 0:
                        log(f'WiFi连接已恢复，重置错误计数器(之前: {error_counts["wifi"]})', 'INFO')
                        error_counts['wifi'] = 0
            
            # 检查MQTT连接
            if not check_mqtt_connection():
                error_counts['mqtt'] += 1
                log(f'MQTT连接失败 ({error_counts["mqtt"]}/{max_error_count})，等待后重试', 'ERROR')
                if error_counts['mqtt'] >= max_error_count:
                    log('MQTT连接错误次数过多，尝试重新连接', 'ERROR')
                    if mqtt_client:
                        try:
                            mqtt_client.disconnect()
                        except:
                            pass
                    mqtt_client = None
                    error_counts['mqtt'] = 0
                time.sleep(5)
                continue
            else:
                if error_counts['mqtt'] > 0:
                    log(f'MQTT连接已恢复，重置错误计数器(之前: {error_counts["mqtt"]})', 'INFO')
                    error_counts['mqtt'] = 0
            
            # 定期MQTT ping检查(每分钟)
            if time.ticks_diff(current_time, last_mqtt_ping) > 60000:
                last_mqtt_ping = current_time
                try:
                    # 使用umqtt.simple：调用ping，如果失败则重连
                    try:
                        mqtt_client.ping()
                        log('MQTT ping成功', 'INFO')
                        error_counts['mqtt'] = 0
                    except Exception as e:
                        log(f'MQTT ping失败: {e}', 'WARNING')
                        raise
                except Exception as e:
                    log(f'MQTT状态检查失败: {e}', 'ERROR')
                    error_counts['mqtt'] += 1
                    try:
                        log('尝试断开并重新连接MQTT', 'INFO')
                        mqtt_client.disconnect()
                    except Exception as e2:
                        log(f'断开MQTT失败: {e2}', 'WARNING')
                    connect_mqtt()
            
            # 检查MQTT消息（忽略非阻塞无数据错误）
            try:
                mqtt_client.check_msg()
            except OSError as e:
                err = e.args[0] if hasattr(e, 'args') and e.args else None
                # MicroPython 非阻塞读取可能抛出 -1 或 11 (EAGAIN)，此处视为无消息可读
                if err in (-1, 11):
                    pass
                else:
                    log(f'检查MQTT消息错误: {e}', 'ERROR')
                    error_counts['mqtt'] += 1
            except Exception as e:
                log(f'检查MQTT消息错误: {e}', 'ERROR')
                error_counts['mqtt'] += 1
            
            # 定时读取和发布温度
            if time.ticks_diff(current_time, last_temp_time) >= TEMP_SAMPLE_INTERVAL:
                temperature = read_internal_temperature()
                if temperature is not None:
                    if not publish_temperature(temperature):
                        error_counts['temp'] += 1
                        log(f'发布温度数据失败 ({error_counts["temp"]}/{max_error_count})', 'ERROR')
                        if error_counts['temp'] >= max_error_count:
                            log('温度数据发布错误次数过多，尝试重新连接MQTT', 'ERROR')
                            if mqtt_client:
                                try:
                                    mqtt_client.disconnect()
                                except:
                                    pass
                            mqtt_client = None
                            error_counts['temp'] = 0
                    else:
                        if error_counts['temp'] > 0:
                            log(f'温度数据发布已恢复，重置错误计数器(之前: {error_counts["temp"]})', 'INFO')
                            error_counts['temp'] = 0
                else:
                    error_counts['temp'] += 1
                    log(f'读取温度失败 ({error_counts["temp"]}/{max_error_count})', 'ERROR')
                    if error_counts['temp'] >= max_error_count:
                        log('温度读取错误次数过多，跳过本次采样', 'ERROR')
                        error_counts['temp'] = 0
                        
                last_temp_time = current_time
            
            # 短暂休眠以降低CPU使用率
            time.sleep(0.1)
            
        except Exception as e:
            log(f'主循环异常: {e}', 'ERROR')
            time.sleep(1)

# 主函数
def main():
    try:
        if init():
            main_loop()
        else:
            log('初始化失败，程序退出', 'ERROR')
            return
    except KeyboardInterrupt:
        log('用户中断程序', 'INFO')
    except Exception as e:
        log(f'程序异常: {e}', 'ERROR')
        # 打印异常堆栈
        try:
            import sys
            sys.print_exception(e)
        except:
            pass
    finally:
        # 清理资源
        try:
            cleanup()
        except Exception as e:
            log(f'资源清理失败: {e}', 'ERROR')
        log('程序结束', 'INFO')

# 资源清理函数
def cleanup():
    global led, mqtt_client, wlan, USE_UMQTT
    
    log('开始清理资源')
    
    # 清理LED资源
    try:
        if led:
            log('关闭LED')
            # 将所有LED设置为黑色(关闭)
            for i in range(NUM_LEDS):
                led[i] = (0, 0, 0)
            led.write()
            log('LED已关闭', 'DEBUG')
        else:
            log('LED未初始化，跳过', 'DEBUG')
    except Exception as e:
        log(f'关闭LED失败: {e}', 'ERROR')
    
    # 清理MQTT连接
    try:
        if mqtt_client:
            log('断开MQTT连接')
            try:
                mqtt_client.disconnect()
                log('MQTT连接已断开', 'DEBUG')
            except Exception as e:
                log(f'MQTT断开操作失败: {e}', 'WARNING')
            finally:
                mqtt_client = None
        else:
            log('MQTT客户端未初始化，跳过', 'DEBUG')
    except Exception as e:
        log(f'清理MQTT连接失败: {e}', 'ERROR')
    
    # 清理WiFi连接
    try:
        if wlan:
            log('断开WiFi连接')
            try:
                wlan.disconnect()
                log('WiFi已断开', 'DEBUG')
                wlan.active(False)
                log('WiFi模块已禁用', 'DEBUG')
            except Exception as e:
                log(f'WiFi断开操作失败: {e}', 'WARNING')
        else:
            log('WiFi未初始化，跳过', 'DEBUG')
    except Exception as e:
        log(f'清理WiFi连接失败: {e}', 'ERROR')
    
    # 清理其他资源
    try:
        # 强制垃圾回收
        import gc
        gc.collect()
        log('垃圾回收完成', 'DEBUG')
    except Exception as e:
        log(f'垃圾回收失败: {e}', 'WARNING')
    
    log('资源清理完成')

# 程序入口
if __name__ == '__main__':
    try:
        # 导入sys模块以获取系统信息
        import sys
        
        # 显示启动信息
        print('=' * 50)
        print('ESP32-S3 IoT传感器程序启动')
        print('=' * 50)
        
        # 运行主程序
        main()
        
    except Exception as e:
        print(f'程序启动失败: {e}')
        try:
            import sys
            sys.print_exception(e)
        except:
            pass
        # 系统重启
        try:
            import machine
            print('系统将在5秒后重启...')
            time.sleep(5)
            machine.reset()
        except:
            pass