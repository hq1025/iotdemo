<template>
	<view class="container">
		<!-- 设备列表 -->
		<view v-if="devices.length > 0" class="device-list">
			<view v-for="device in devices" :key="device.id" class="device-item">
				<image class="device-icon" :src="getDeviceIcon(device)"></image>
				<view class="device-info">
					<text class="device-name">{{ device.name }}</text>
					<text class="device-topic">{{ device.topic }}</text>
					<text class="device-type">{{ getDeviceTypeName(device.type) }}</text>
				</view>
				<view class="device-actions">
					<button class="edit-btn" @click="editDevice(device)">编辑</button>
					<button class="delete-btn" @click="deleteDevice(device)">删除</button>
				</view>
			</view>
		</view>
		
		<!-- 无设备状态 -->
		<view v-else class="no-device">
			<image class="empty-icon" src="/static/empty.png"></image>
			<text class="empty-text">暂无设备</text>
		</view>
		
		<!-- 添加设备按钮 -->
		<view class="add-button-section">
			<button class="add-btn" @click="goToAddDevice">添加设备</button>
		</view>
	</view>
</template>

<script>
export default {
	data() {
		return {
			devices: [],
			deleteDeviceId: null,
			deleteDeviceName: ''
		}
	},
	onLoad() {
		this.loadDevices()
	},
	onShow() {
		// 页面显示时重新加载设备列表
		this.loadDevices()
	},
	methods: {
		// 加载设备列表
		loadDevices() {
			const savedDevices = uni.getStorageSync('devices') || []
			this.devices = savedDevices
		},
		
		// 获取设备图标
		getDeviceIcon(device) {
			const iconMap = {
				temperature: '/static/temperature.png',
				humidity: '/static/humidity.png',
				switch: '/static/switch.png',
				led: '/static/led.png',
				soil: '/static/tr.png',
				water: '/static/waterquality.png',
				wind: '/static/fengsu.png'
			}
			return iconMap[device.type] || '/static/empty.png'
		},
		
		// 获取设备类型名称
		getDeviceTypeName(type) {
			const typeMap = {
				temperature: '温度传感器',
				humidity: '湿度传感器',
				switch: '开关设备',
				led: '灯带设备',
				soil: '土壤检测',
				water: '水质检测',
				wind: '风速检测'
			}
			return typeMap[type] || '未知设备'
		},
		
		// 编辑设备
		editDevice(device) {
			uni.navigateTo({
				url: `/pages/addDevice/addDevice?id=${device.id}&mode=edit`
			})
		},
		
		// 删除设备
		deleteDevice(device) {
			this.deleteDeviceId = device.id
			this.deleteDeviceName = device.name
			
			// 使用系统弹窗替代uni-popup（因为可能没有安装uni-ui）
			uni.showModal({
				title: '确认删除',
				content: `确定要删除设备 ${device.name} 吗？`,
				confirmText: '删除',
				confirmColor: '#dc3545',
				success: (res) => {
					if (res.confirm) {
						this.confirmDelete()
					}
				}
			})
		},
		
		// 确认删除
		confirmDelete() {
			if (this.deleteDeviceId) {
				this.devices = this.devices.filter(device => device.id !== this.deleteDeviceId)
				uni.setStorageSync('devices', this.devices)
				
				uni.showToast({
					title: '删除成功',
					icon: 'success'
				})
				
				this.deleteDeviceId = null
				this.deleteDeviceName = ''
			}
		},
		
		// 取消删除
		cancelDelete() {
			this.deleteDeviceId = null
			this.deleteDeviceName = ''
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

.device-list {
	margin-bottom: 30rpx;
}

.device-item {
	display: flex;
	align-items: center;
	background-color: white;
	padding: 30rpx;
	margin-bottom: 20rpx;
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
	margin-bottom: 8rpx;
}

.device-topic {
	font-size: 26rpx;
	color: #666;
	margin-bottom: 8rpx;
}

.device-type {
	font-size: 24rpx;
	color: #999;
}

.device-actions {
	display: flex;
	flex-direction: column;
	gap: 10rpx;
}

.edit-btn, .delete-btn {
	padding: 12rpx 24rpx;
	border: none;
	border-radius: 20rpx;
	font-size: 24rpx;
	min-width: 80rpx;
}

.edit-btn {
	background-color: #007AFF;
	color: white;
}

.edit-btn:active {
	background-color: #0056CC;
}

.delete-btn {
	background-color: #dc3545;
	color: white;
}

.delete-btn:active {
	background-color: #c82333;
}

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

/* 添加按钮区域 */
.add-button-section {
	position: fixed;
	bottom: 40rpx;
	left: 20rpx;
	right: 20rpx;
}

.add-btn {
	width: 100%;
	padding: 18rpx;
	background-color: #28a745;
	color: white;
	border: none;
	border-radius: 10rpx;
	font-size: 32rpx;
	font-weight: bold;
}

.add-btn:active {
	background-color: #1e7e34;
}
</style>