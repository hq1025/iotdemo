<template>
	<view class="container">
		<view class="form-section">
			<!-- 设备名称 -->
			<view class="form-item">
				<text class="label">设备名称</text>
			<uni-easyinput
				v-model="device.name"
				placeholder="请输入设备名称"
				:styles="easyInputStyles"
			/>
			</view>
			
			<!-- 设备类型 -->
			<view class="form-item">
				<text class="label">设备类型</text>
				<picker 
					:range="deviceTypes" 
					:range-key="'name'"
					:value="selectedTypeIndex"
					@change="onTypeChange"
				>
					<view class="picker-display">
						<text class="picker-text">{{ selectedTypeName }}</text>
						<text class="picker-arrow">></text>
					</view>
				</picker>
			</view>
			
			<!-- 订阅主题 -->
			<view class="form-item">
				<text class="label">订阅主题</text>
			<uni-easyinput
				v-model="device.topic"
				placeholder="请输入MQTT订阅主题"
				:styles="easyInputStyles"
			/>
			</view>
			
			<!-- 开关设备的命令配置 -->
			<view v-if="needCommands" class="command-section">
				<view class="form-item">
					<text class="label">开启命令</text>
				<uni-easyinput
					v-model="device.onCommand"
					placeholder="请输入开启命令"
					:styles="easyInputStyles"
				/>
				</view>
				
				<view class="form-item">
					<text class="label">关闭命令</text>
				<uni-easyinput
					v-model="device.offCommand"
					placeholder="请输入关闭命令"
					:styles="easyInputStyles"
				/>
				</view>
			</view>
			
			<!-- 传感器设备的单位配置 -->
			<view v-if="needUnit" class="form-item">
				<text class="label">数值单位</text>
			<uni-easyinput
				v-model="device.unit"
				placeholder="请输入数值单位"
				:styles="easyInputStyles"
			/>
			</view>
		</view>
		
		<!-- 设备预览 -->
		<view class="preview-section">
			<text class="preview-title">设备预览</text>
			<view class="device-preview">
				<image class="preview-icon" :src="getDeviceIcon()"></image>
				<view class="preview-info">
					<text class="preview-name">{{ device.name || '设备名称' }}</text>
					<text class="preview-topic">{{ device.topic || '订阅主题' }}</text>
					<text class="preview-type">{{ selectedTypeName }}</text>
				</view>
			</view>
		</view>
		
		<!-- 操作按钮 -->
		<view class="button-section">
			<button class="cancel-btn" @click="goBack">取消</button>
			<button class="save-btn" @click="saveDevice">{{ isEditMode ? '更新' : '添加' }}</button>
		</view>
	</view>
</template>

<script>
export default {
	data() {
		return {
			isEditMode: false,
			editDeviceId: null,
			device: {
				name: '',
				type: 'temperature',
				topic: '',
				onCommand: 'ON',
				offCommand: 'OFF',
				unit: '',
				status: false,
				value: null
			},
			deviceTypes: [
				{ key: 'temperature', name: '温度传感器' },
				{ key: 'humidity', name: '湿度传感器' },
				{ key: 'switch', name: '开关设备' },
				{ key: 'led', name: '灯带设备' },
				{ key: 'soil', name: '土壤检测' },
				{ key: 'water', name: '水质检测' },
				{ key: 'wind', name: '风速检测' }
			],
			selectedTypeIndex: 0,
			easyInputStyles: {
				color: '#333',
				backgroundColor: '#fafafa',
				borderColor: '#e0e0e0'
			}
		}
	},
	computed: {
		selectedTypeName() {
			return this.deviceTypes[this.selectedTypeIndex]?.name || '温度传感器'
		},
		needCommands() {
			const type = this.deviceTypes[this.selectedTypeIndex]?.key
			return ['switch', 'led', 'wind'].includes(type)
		},
		needUnit() {
			const type = this.deviceTypes[this.selectedTypeIndex]?.key
			return ['temperature', 'humidity', 'soil', 'water', 'wind'].includes(type)
		}
	},
	onLoad(options) {
		if (options.id && options.mode === 'edit') {
			this.isEditMode = true
			this.editDeviceId = options.id
			this.loadDevice(options.id)
		}
		this.setDefaultUnit()
	},
	methods: {
		// 加载设备信息（编辑模式）
		loadDevice(deviceId) {
			const devices = uni.getStorageSync('devices') || []
			const device = devices.find(d => d.id === deviceId)
			if (device) {
				this.device = { ...device }
				// 设置设备类型索引
				const typeIndex = this.deviceTypes.findIndex(t => t.key === device.type)
				this.selectedTypeIndex = typeIndex >= 0 ? typeIndex : 0
			}
		},
		
		// 设备类型改变
		onTypeChange(e) {
			this.selectedTypeIndex = e.detail.value
			const selectedType = this.deviceTypes[this.selectedTypeIndex]
			this.device.type = selectedType.key
			this.setDefaultUnit()
			this.setDefaultCommands()
		},
		
		// 设置默认单位
		setDefaultUnit() {
			const type = this.deviceTypes[this.selectedTypeIndex]?.key
			const unitMap = {
				temperature: '°C',
				humidity: '%',
				soil: '%',
				water: 'ppm',
				wind: 'm/s'
			}
			if (unitMap[type] && !this.device.unit) {
				this.device.unit = unitMap[type]
			}
		},
		
		// 设置默认命令
		setDefaultCommands() {
			if (this.needCommands && !this.device.onCommand) {
				this.device.onCommand = 'ON'
				this.device.offCommand = 'OFF'
			}
		},
		
		// 获取设备图标
		getDeviceIcon() {
			const type = this.deviceTypes[this.selectedTypeIndex]?.key
			const iconMap = {
				temperature: '/static/temperature.png',
				humidity: '/static/humidity.png',
				switch: '/static/switch.png',
				led: '/static/led.png',
				soil: '/static/tr.png',
				water: '/static/waterquality.png',
				wind: '/static/fengsu.png'
			}
			return iconMap[type] || '/static/empty.png'
		},
		
		// 保存设备
		saveDevice() {
			if (!this.validateDevice()) {
				return
			}
			
			const devices = uni.getStorageSync('devices') || []
			
			if (this.isEditMode) {
				// 编辑模式：更新现有设备
				const index = devices.findIndex(d => d.id === this.editDeviceId)
				if (index >= 0) {
					devices[index] = { ...this.device, id: this.editDeviceId }
				}
			} else {
				// 添加模式：创建新设备
				const newDevice = {
					...this.device,
					id: Date.now().toString() + Math.random().toString(36).substr(2, 5)
				}
				devices.push(newDevice)
			}
			
			try {
				uni.setStorageSync('devices', devices)
				uni.showToast({
					title: this.isEditMode ? '更新成功' : '添加成功',
					icon: 'success'
				})
				
				setTimeout(() => {
					uni.navigateBack()
				}, 1500)
			} catch (error) {
				uni.showToast({
					title: '保存失败',
					icon: 'error'
				})
			}
		},
		
		// 验证设备信息
		validateDevice() {
			if (!this.device.name.trim()) {
				uni.showToast({
					title: '请输入设备名称',
					icon: 'none'
				})
				return false
			}
			
			if (!this.device.topic.trim()) {
				uni.showToast({
					title: '请输入订阅主题',
					icon: 'none'
				})
				return false
			}
			
			if (this.needCommands) {
				if (!this.device.onCommand.trim()) {
					uni.showToast({
						title: '请输入开启命令',
						icon: 'none'
					})
					return false
				}
				
				if (!this.device.offCommand.trim()) {
					uni.showToast({
						title: '请输入关闭命令',
						icon: 'none'
					})
					return false
				}
			}
			
			return true
		},
		
		// 返回上一页
		goBack() {
			uni.navigateBack()
		}
	}
}
</script>

<style>
.container {
	padding: 30rpx;
	background-color: #f5f5f5;
	min-height: 100vh;
}

.form-section {
	background-color: white;
	border-radius: 15rpx;
	padding: 30rpx;
	margin-bottom: 30rpx;
	box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.1);
}

.form-item {
	margin-bottom: 40rpx;
}

.form-item:last-child {
	margin-bottom: 0;
}

.label {
	display: block;
	font-size: 32rpx;
	color: #333;
	margin-bottom: 15rpx;
	font-weight: bold;
}

/* 使用 uni-easyinput 默认样式，通过 :styles 属性调整外观 */

.picker-display {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 25rpx;
	border: 2rpx solid #e0e0e0;
	border-radius: 10rpx;
	background-color: #fafafa;
}

.picker-text {
	font-size: 30rpx;
	color: #333;
}

.picker-arrow {
	font-size: 24rpx;
	color: #999;
}

.command-section {
	margin-top: 30rpx;
	padding-top: 30rpx;
	border-top: 2rpx solid #f0f0f0;
}

/* 设备预览样式 */
.preview-section {
	background-color: white;
	border-radius: 15rpx;
	padding: 30rpx;
	margin-bottom: 30rpx;
	box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.1);
}

.preview-title {
	font-size: 32rpx;
	font-weight: bold;
	color: #333;
	margin-bottom: 20rpx;
}

.device-preview {
	display: flex;
	align-items: center;
	padding: 20rpx;
	background-color: #f8f9fa;
	border-radius: 10rpx;
}

.preview-icon {
	width: 80rpx;
	height: 80rpx;
	margin-right: 30rpx;
}

.preview-info {
	flex: 1;
	display: flex;
	flex-direction: column;
}

.preview-name {
	font-size: 32rpx;
	font-weight: bold;
	color: #333;
	margin-bottom: 8rpx;
}

.preview-topic {
	font-size: 26rpx;
	color: #666;
	margin-bottom: 8rpx;
}

.preview-type {
	font-size: 24rpx;
	color: #999;
}

/* 按钮区域 */
.button-section {
	display: flex;
	gap: 20rpx;
}

.cancel-btn, .save-btn {
	flex: 1;
	padding: 18rpx;
	border: none;
	border-radius: 10rpx;
	font-size: 32rpx;
	font-weight: bold;
}

.cancel-btn {
	background-color: #6c757d;
	color: white;
}

.cancel-btn:active {
	background-color: #545b62;
}

.save-btn {
	background-color: #28a745;
	color: white;
}

.save-btn:active {
	background-color: #1e7e34;
}
</style>