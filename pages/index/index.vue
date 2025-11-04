<template>
	<view class="container">
		<!-- 顶部按钮区域 -->
		<view class="header">
			<view class="mqtt-status">
				<view class="status-dot" :class="{ online: mqttConnected }"></view>
				<text class="status-text">{{ '服务器:' + (mqttConnected ? '已连接' : '未连接') }}</text>
			</view>
			<view class="header-actions">
				<button class="header-btn small" @click="goToConfig">配置</button>
				<button class="header-btn small" @click="goToDevices">设备</button>
			</view>
		</view>
		
		<!-- 无设备状态 -->
		<view v-if="devices.length === 0" class="no-device">
			<image class="empty-icon" src="/static/empty.png"></image>
			<text class="empty-text">暂无设备</text>
			<button class="add-device-btn" @click="goToAddDevice">添加设备</button>
		</view>
		
		<!-- 有设备状态 -->
		<view v-else class="device-dashboard">
			<!-- 设备信息卡片 -->
			<view class="device-cards">
				<view v-for="device in devices" :key="device.id" class="device-card">
					<image class="device-icon" :src="getDeviceIcon(device)"></image>
					<view class="device-info">
						<text class="device-name">{{ device.name }}</text>
						<!-- 非开关类设备显示数值 -->
						<text v-if="device.type !== 'switch' && device.type !== 'led'" class="device-value">{{ getDeviceValue(device) }}</text>
						<!-- 开关控制按钮放在新一行 -->
						<view v-if="device.type === 'switch' || device.type === 'led'" class="switch-row">
							<button 
								class="switch-btn" 
								:class="{ 'switch-on': !device.status }"
								@click="toggleDevice(device)"
							>
								{{ device.status ? '关闭' : '开启' }}
							</button>
						</view>
					</view>
				</view>
			</view>
			
			<!-- 温度趋势图 -->
			<view v-if="devices.length > 0 && temperatureDevices.length > 0" class="chart-section">
				<view class="section-title">
					<text>温度趋势</text>
					<view class="period-selector">
						<text 
							class="period-btn" 
							:class="{ active: selectedPeriod === '24h' }"
							@click="selectedPeriod = '24h'"
						>24小时</text>
						<text 
							class="period-btn" 
							:class="{ active: selectedPeriod === '7d' }"
							@click="selectedPeriod = '7d'"
						>7天</text>
					</view>
				</view>
				<TemperatureChart 
					:data="chartData" 
					:period="selectedPeriod"
				/>
			</view>
		</view>
	</view>
</template>

<script>
import TemperatureChart from '@/components/TemperatureChart.vue'

export default {
	components: {
		TemperatureChart
	},
	data() {
		return {
			devices: [], // 设备列表
			chartPeriod: '24h', // 图表时间周期
			temperatureData: [], // 温度数据
			mqttConfig: null, // MQTT配置
			mqttConnected: false, // MQTT连接状态
			selectedPeriod: '24h',
			temperatureHistory: {} // 存储各设备的温度历史数据
		}
	},
	computed: {
		hasTemperatureDevice() {
			return this.devices.some(device => device.type === 'temperature')
		},
		temperatureDevices() {
			return this.devices.filter(device => device.type === 'temperature')
		},
		chartData() {
			// 获取第一个温度设备的数据用于显示
			const temperatureDevices = this.devices.filter(device => device.type === 'temperature')
			if (temperatureDevices.length === 0) {
				return []
			}
			
			const firstDevice = temperatureDevices[0]
			const deviceHistory = this.temperatureHistory[firstDevice.id]
			
			if (!deviceHistory) {
				return []
			}
			
			return deviceHistory[this.selectedPeriod] || []
		}
	},
onLoad() {
    this.loadDevices()
    this.loadTemperatureHistory()
    this.loadMqttConfig()
    this.initMqtt()
},
onShow() {
    // 页面显示时重新加载设备列表
    this.loadDevices()
    this.loadTemperatureHistory()
},
	onUnload() {
		// 保持连接，不在卸载时断开
	},
	methods: {
		// 加载设备列表
		loadDevices() {
			const savedDevices = uni.getStorageSync('devices') || []
			this.devices = savedDevices
			
			// 模拟一些示例数据
			if (this.devices.length === 0) {
				// 可以添加一些示例设备用于演示
				// this.addSampleDevices()
			}
		},
		
		// 添加示例设备（用于演示）
		addSampleDevices() {
			const sampleDevices = [
				{
					id: '1',
					name: '客厅温度传感器',
					type: 'temperature',
					topic: 'sensor/temperature/living_room',
					value: 25.6,
					unit: '°C',
					status: true
				},
				{
					id: '2',
					name: '客厅湿度传感器',
					type: 'humidity',
					topic: 'sensor/humidity/living_room',
					value: 65,
					unit: '%',
					status: true
				},
				{
					id: '3',
					name: '客厅灯光开关',
					type: 'switch',
					topic: 'control/switch/living_room',
					status: false,
					onCommand: 'ON',
					offCommand: 'OFF'
				}
			]
			this.devices = sampleDevices
			uni.setStorageSync('devices', this.devices)
		},
		
		// 获取设备图标
		getDeviceIcon(device) {
			const iconMap = {
				temperature: '/static/temperature.png',
				humidity: '/static/humidity.png',
				switch: device.status ? '/static/led01.png' : '/static/led02.png',
				led: '/static/led.png',
				soil: '/static/tr.png',
				water: '/static/waterquality.png',
				wind: '/static/fengsu.png'
			}
			return iconMap[device.type] || '/static/empty.png'
		},
		
		// 获取设备显示值
		getDeviceValue(device) {
			if (device.type === 'switch' || device.type === 'led') {
				return device.status ? '开启' : '关闭'
			}
			return device.value ? `${device.value}${device.unit || ''}` : '--'
		},
		
		// 切换设备状态
		toggleDevice(device) {
			// 根据按钮显示的动作发送对应命令
			// 按钮显示"开启"时发送开启命令，显示"关闭"时发送关闭命令
			const command = device.status ? device.offCommand : device.onCommand
			// 切换状态
			device.status = !device.status
			this.saveDevices()
			if (!device.topic) return
			this.$mqttTool.publish({ topic: device.topic, message: String(command) })
		},
		
		// 保存设备列表（合并最新存储，避免覆盖配置）
		saveDevices() {
			try {
				const latest = uni.getStorageSync('devices') || []
				const merged = latest.map(saved => {
					const mem = this.devices.find(d => d.id === saved.id)
					if (!mem) return saved
					const updated = { ...saved }
					if (mem.hasOwnProperty('status')) updated.status = mem.status
					if (mem.hasOwnProperty('value')) updated.value = mem.value
					if (mem.hasOwnProperty('lastUpdate')) updated.lastUpdate = mem.lastUpdate
					return updated
				})
				uni.setStorageSync('devices', merged)
				this.devices = merged
			} catch (e) {
				console.error('设备保存失败:', e)
			}
		},
		
		// 加载MQTT配置
		loadMqttConfig() {
			this.mqttConfig = uni.getStorageSync('mqttConfig')
		},
		
		// 初始化MQTT连接
		async initMqtt() {
			if (!this.mqttConfig) return
			const url = this.buildMqttUrl(this.mqttConfig)
			const opts = {
				url,
				clientId: this.mqttConfig.clientId,
				username: this.mqttConfig.username,
				password: this.mqttConfig.password,
				clean: true
			}
			try {
				const client = await this.$mqttTool.connect(opts)
				client.on('connect', () => {
					console.log('MQTT连接成功')
					this.mqttConnected = true
					this.subscribeToDevices()
				})
				client.on('reconnect', () => { console.log('MQTT重新连接') })
				client.on('error', (err) => { console.error('MQTT连接错误:', err); this.mqttConnected = false })
				client.on('close', () => { console.log('MQTT连接关闭'); this.mqttConnected = false })
				client.on('message', (topic, message, buffer) => { this.onMqttMessage(topic, message, buffer) })
			} catch (e) {
				console.error('MQTT连接失败:', e)
			}
		},
		
		// 构建MQTT ws/wss/wx/wxs URL
		buildMqttUrl(config) {
			let host = (config.host || '').trim()
			const port = config.port
			if (!host) return ''
			if (host.startsWith('ws://') || host.startsWith('wss://') || host.startsWith('wx://') || host.startsWith('wxs://')) {
				return host.includes('/mqtt') ? host : (host.replace(/\/$/, '') + '/mqtt')
			}
			return `ws://${host}:${port}/mqtt`
		},

		// 处理MQTT消息，订阅真实数据
		onMqttMessage(topic, message, buffer) {
			const msgStr = message ? message.toString() : ''
			console.log('[MQTT] 收到消息:', {
				topic,
				message: msgStr,
				bufferLength: buffer && buffer.length ? buffer.length : 0
			})
			let payload = null
			try { payload = JSON.parse(msgStr) } catch (e) { payload = msgStr }
			const idx = this.devices.findIndex(d => d.topic === topic)
			if (idx === -1) return
			const device = this.devices[idx]
			let val = undefined
			let status = device.status
			if (typeof payload === 'object' && payload) {
				// 优先按设备类型提取数值
				if (device.type === 'temperature' && payload.temperature !== undefined) {
					val = payload.temperature
				} else if (device.type === 'humidity' && payload.humidity !== undefined) {
					val = payload.humidity
				} else if (payload.value !== undefined) {
					val = payload.value
				}
				// 可选状态字段解析
				if (payload.status !== undefined) status = payload.status === 'online' || payload.status === true
			} else {
				const lower = String(payload).toLowerCase()
				if (device.type === 'switch' || device.type === 'led') {
					if (lower === String(device.onCommand).toLowerCase() || lower === 'on') status = true
					else if (lower === String(device.offCommand).toLowerCase() || lower === 'off') status = false
				} else {
					const num = parseFloat(lower)
					if (!isNaN(num)) val = num
				}
			}
			if (val !== undefined) {
				this.$set(this.devices[idx], 'value', typeof val === 'number' ? val : parseFloat(val) || val)
				this.$set(this.devices[idx], 'lastUpdate', new Date().toLocaleTimeString())
				console.log('[MQTT] 已更新设备值:', {
					deviceId: device.id,
					name: device.name,
					type: device.type,
					value: this.devices[idx].value
				})
				if (device.type === 'temperature') {
					this.recordTemperatureData(device.id, this.devices[idx].value)
				}
			}
			if (device.type === 'switch' || device.type === 'led') {
				this.$set(this.devices[idx], 'status', !!status)
				console.log('[MQTT] 已更新设备状态:', {
					deviceId: device.id,
					name: device.name,
					status: !!status
				})
			}
			this.saveDevices()
		},

		// 订阅设备主题
		subscribeToDevices() {
			if (!this.$mqttTool || !this.$mqttTool.client) return
			this.devices.forEach(device => {
				if (!device.topic) return
				this.$mqttTool.subscribe({ topic: device.topic, qos: 0 })
					.then(() => {
						console.log('订阅成功:', device.topic)
					})
					.catch(err => console.error('订阅失败', device.topic, err))
			})
		},
		
		// 更新设备数值
		updateDeviceValue(deviceId, value) {
			const device = this.devices.find(d => d.id === deviceId)
			if (device) {
				device.value = parseFloat(value) || value
				device.lastUpdate = new Date()
				this.saveDevices()
			}
		},
		
		// 设备数据更新事件处理
		onDeviceDataUpdate(data) {
			const deviceIndex = this.devices.findIndex(device => device.topic === data.topic)
			if (deviceIndex !== -1) {
				// 更新设备状态
				this.$set(this.devices[deviceIndex], 'status', data.status)
				this.$set(this.devices[deviceIndex], 'lastUpdate', new Date().toLocaleTimeString())
				
				// 如果是温度设备，记录历史数据
				if (this.devices[deviceIndex].type === 'temperature' && data.value !== undefined) {
					this.recordTemperatureData(this.devices[deviceIndex].id, data.value)
				}
			}
		},
		
		// 记录温度数据
		recordTemperatureData(deviceId, temperature) {
			const now = new Date()
			const dataPoint = {
				time: now.getTime(),
				value: parseFloat(temperature),
				label: now.toLocaleTimeString()
			}
			
			// 初始化设备的温度历史
			if (!this.temperatureHistory[deviceId]) {
				this.$set(this.temperatureHistory, deviceId, {
					'24h': [],
					'7d': []
				})
			}
			
			// 添加到24小时数据
			this.temperatureHistory[deviceId]['24h'].push(dataPoint)
			
			// 保持24小时数据不超过144个点（每10分钟一个点）
			if (this.temperatureHistory[deviceId]['24h'].length > 144) {
				this.temperatureHistory[deviceId]['24h'].shift()
			}
			
			// 每小时添加一个点到7天数据
			const hourlyData = this.temperatureHistory[deviceId]['7d']
			if (hourlyData.length === 0 || now.getTime() - hourlyData[hourlyData.length - 1].time > 3600000) {
				hourlyData.push(dataPoint)
				
				// 保持7天数据不超过168个点（每小时一个点）
				if (hourlyData.length > 168) {
					hourlyData.shift()
				}
			}

			// 清理超过时间窗口的数据（更稳妥，避免长时间运行后数据偏移）
			const DAY_MS = 24 * 3600 * 1000
			const nowTs = now.getTime()
			this.temperatureHistory[deviceId]['24h'] = this.temperatureHistory[deviceId]['24h'].filter(p => nowTs - p.time <= DAY_MS)
			this.temperatureHistory[deviceId]['7d'] = this.temperatureHistory[deviceId]['7d'].filter(p => nowTs - p.time <= 7 * DAY_MS)

			// 持久化本地存储
			this.saveTemperatureHistory()
		},

		// 保存温度历史到本地存储
		saveTemperatureHistory() {
			try {
				uni.setStorageSync('temperatureHistory', this.temperatureHistory)
				console.log('[存储] 温度历史已保存')
			} catch (e) {
				console.error('[存储] 温度历史保存失败:', e)
			}
		},

		// 加载温度历史数据
		loadTemperatureHistory() {
			try {
				const saved = uni.getStorageSync('temperatureHistory') || {}
				// 只加载与当前设备列表相关的历史，避免无效数据占用空间
				const filtered = {}
				this.devices.forEach(d => {
					if (d.type === 'temperature' && saved[d.id]) {
						filtered[d.id] = saved[d.id]
					}
				})
				this.temperatureHistory = filtered
				console.log('[存储] 温度历史已加载，设备数:', Object.keys(filtered).length)
			} catch (e) {
				console.error('[存储] 温度历史加载失败:', e)
			}
		},
		
		// 切换图表时间周期
		switchChartPeriod(period) {
			this.chartPeriod = period
		},
		
		// 导航到配置页面
		goToConfig() {
			uni.navigateTo({
				url: '/pages/config/config'
				// url: '/pages/home/Home'
			})
		},
		
		// 导航到设备列表页面
		goToDevices() {
			uni.navigateTo({
				url: '/pages/devices/devices'
			})
		},
		
		// 导航到添加设备页面
		goToAddDevice() {
			uni.navigateTo({
				url: '/pages/addDevice/addDevice'
			})
		}
	}
}
</script>

<style>
.container {
	padding: 20rpx;
	background-color: #f5f5f5;
	min-height: 100vh;
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30rpx;
}

.header-actions { display: flex; align-items: center; }
.header-btn { margin-left: 12rpx; padding: 20rpx; background-color: #007AFF; color: white; border: none; border-radius: 10rpx; font-size: 32rpx; }
.header-btn.small { padding: 12rpx 32rpx; font-size: 26rpx; min-width: 120rpx; }

.header-btn:active {
    background-color: #0056CC;
}

.mqtt-status { display: flex; align-items: center; }
.status-dot { width: 16rpx; height: 16rpx; border-radius: 50%; background-color: #ccc; margin-right: 10rpx; }
.status-dot.online { background-color: #28a745; }
.status-text { font-size: 26rpx; color: #666; }

/* 无设备状态样式 */
.no-device {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 100rpx 0;
}

.empty-icon {
	width: 200rpx;
	height: 200rpx;
	margin-bottom: 40rpx;
}

.empty-text {
	font-size: 36rpx;
	color: #999;
	margin-bottom: 60rpx;
}

.add-device-btn {
	padding: 20rpx 60rpx;
	background-color: #28a745;
	color: white;
	border: none;
	border-radius: 10rpx;
	font-size: 32rpx;
}

.add-device-btn:active {
	background-color: #1e7e34;
}

/* 设备看板样式 */
.device-dashboard {
	padding-bottom: 40rpx;
}

.device-cards {
    margin-bottom: 40rpx;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    grid-gap: 20rpx;
}

.device-card {
    display: flex;
    align-items: center;
    background-color: white;
    padding: 30rpx;
    border-radius: 15rpx;
    box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.1);
}

.device-icon {
	width: 80rpx;
	height: 80rpx;
	margin-right: 30rpx;
}

.device-info {
	flex: 1;
	display: flex;
	flex-direction: column;
}

.device-name {
	font-size: 32rpx;
	font-weight: bold;
	color: #333;
	margin-bottom: 10rpx;
}

.device-value {
    font-size: 28rpx;
    color: #666;
}

.switch-row { margin-top: 8rpx; }

.switch-btn {
    padding: 6rpx 14rpx;
    border: none;
    border-radius: 18rpx;
    font-size: 22rpx;
    background-color: #dc3545;
    color: white;
}

.switch-btn.switch-on {
	background-color: #28a745;
}

.switch-btn:active {
	opacity: 0.8;
}

/* 图表区域样式 */
.section-title {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20rpx;
	font-size: 32rpx;
	font-weight: bold;
	color: #333;
}

.period-selector {
	display: flex;
	background-color: #f5f5f5;
	border-radius: 20rpx;
	padding: 4rpx;
}

.period-btn {
	padding: 12rpx 24rpx;
	font-size: 28rpx;
	color: #666;
	border-radius: 16rpx;
	transition: all 0.3s;
}

.period-btn.active {
	background-color: #007AFF;
	color: white;
}

.chart-section {
	background-color: white;
	border-radius: 15rpx;
	padding: 30rpx;
	box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.1);
}

.chart-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 30rpx;
}

.chart-title {
	font-size: 36rpx;
	font-weight: bold;
	color: #333;
}

.chart-tabs {
	display: flex;
}

.chart-tab {
	padding: 10rpx 20rpx;
	margin-left: 10rpx;
	background-color: #f8f9fa;
	color: #666;
	border: none;
	border-radius: 20rpx;
	font-size: 24rpx;
}

.chart-tab.active {
	background-color: #007AFF;
	color: white;
}

.chart-container {
	height: 400rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: #f8f9fa;
	border-radius: 10rpx;
}

.chart-canvas {
	width: 100%;
	height: 100%;
}
</style>
