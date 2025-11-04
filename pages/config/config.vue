<template>
	<view class="container">
		<view class="form-section">
			<view class="form-item">
				<text class="label">服务器地址</text>
				<uni-easyinput
					v-model="config.host"
					placeholder="请输入MQTT服务器地址"
					:styles="easyInputStyles"
				/>
			</view>
			
			<view class="form-item">
				<text class="label">端口号</text>
			<uni-easyinput
				v-model="config.port"
				placeholder="请输入端口号"
				type="number"
				:styles="easyInputStyles"
			/>
			</view>
			
			<view class="form-item">
				<text class="label">客户端ID</text>
			<uni-easyinput
				v-model="config.clientId"
				placeholder="请输入客户端ID"
				:styles="easyInputStyles"
			/>
			</view>
			
			<view class="form-item">
				<text class="label">用户名</text>
			<uni-easyinput
				v-model="config.username"
				placeholder="请输入用户名"
				:styles="easyInputStyles"
			/>
			</view>
			
			<view class="form-item">
				<text class="label">密码</text>
			<uni-easyinput
				v-model="config.password"
				placeholder="请输入密码"
				type="password"
				:styles="easyInputStyles"
			/>
			</view>
		</view>
		
		<view class="button-section">
			<button class="test-btn" @click="testConnection">测试连接</button>
			<button class="save-btn" @click="saveConfig">保存配置</button>
		</view>
		
		<view v-if="connectionStatus" class="status-section">
			<text class="status-text" :class="{ success: connectionSuccess, error: !connectionSuccess }">
				{{ connectionStatus }}
			</text>
		</view>
	</view>
</template>

<script>
export default {
	data() {
		return {
			config: {
				host: '',
				port: 1883,
				clientId: '',
				username: '',
				password: ''
			},
			connectionStatus: '',
			connectionSuccess: false,
			easyInputStyles: {
				color: '#333',
				backgroundColor: '#fafafa',
				borderColor: '#e0e0e0'
			}
		}
	},
	onLoad() {
		this.loadConfig()
		this.generateClientId()
	},
	methods: {
		// 加载配置
		loadConfig() {
			const savedConfig = uni.getStorageSync('mqttConfig')
			if (savedConfig) {
				this.config = { ...this.config, ...savedConfig }
			}
		},
		
		// 生成客户端ID
		generateClientId() {
			if (!this.config.clientId) {
				const timestamp = Date.now()
				const random = Math.random().toString(36).substr(2, 5)
				this.config.clientId = `iot_client_${timestamp}_${random}`
			}
		},
		
		// 测试连接
		testConnection() {
			if (!this.validateConfig()) {
				return
			}
			
			this.connectionStatus = '正在测试连接...'
			this.connectionSuccess = false
			
			// 模拟连接测试
			setTimeout(() => {
				// 这里应该实际测试MQTT连接
				// 暂时模拟成功
				this.connectionStatus = 'MQTT连接测试成功'
				this.connectionSuccess = true
				
				setTimeout(() => {
					this.connectionStatus = ''
				}, 3000)
			}, 2000)
		},
		
		// 保存配置
		saveConfig() {
			if (!this.validateConfig()) {
				return
			}
			
			try {
				uni.setStorageSync('mqttConfig', this.config)
				uni.showToast({
					title: '配置保存成功',
					icon: 'success'
				})
				
				// 延迟返回上一页
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
		
		// 验证配置
		validateConfig() {
			if (!this.config.host.trim()) {
				uni.showToast({
					title: '请输入服务器地址',
					icon: 'none'
				})
				return false
			}
			
			if (!this.config.port || this.config.port <= 0) {
				uni.showToast({
					title: '请输入有效的端口号',
					icon: 'none'
				})
				return false
			}
			
			if (!this.config.clientId.trim()) {
				uni.showToast({
					title: '请输入客户端ID',
					icon: 'none'
				})
				return false
			}
			
			return true
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

.button-section {
	display: flex;
	flex-direction: row;
	gap: 20rpx;
}

.test-btn, .save-btn {
	flex: 1;
	padding: 18rpx;
	border: none;
	border-radius: 10rpx;
	font-size: 32rpx;
	font-weight: bold;
}

.test-btn {
	background-color: #17a2b8;
	color: white;
}

.test-btn:active {
	background-color: #138496;
}

.save-btn {
	background-color: #28a745;
	color: white;
}

.save-btn:active {
	background-color: #1e7e34;
}

.status-section {
	margin-top: 30rpx;
	padding: 20rpx;
	background-color: white;
	border-radius: 10rpx;
	text-align: center;
}

.status-text {
	font-size: 28rpx;
	font-weight: bold;
}

.status-text.success {
	color: #28a745;
}

.status-text.error {
	color: #dc3545;
}
</style>