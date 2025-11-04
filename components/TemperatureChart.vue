<template>
	<view class="chart-container">
		<canvas 
			:canvas-id="canvasId" 
			class="chart-canvas"
			@touchstart="onTouchStart"
			@touchmove="onTouchMove"
			@touchend="onTouchEnd"
		></canvas>
		<view v-if="showTooltip" class="tooltip" :style="tooltipStyle">
			<text class="tooltip-text">{{ tooltipText }}</text>
		</view>
	</view>
</template>

<script>
export default {
	name: 'TemperatureChart',
	props: {
		data: {
			type: Array,
			default: () => []
		},
		period: {
			type: String,
			default: '24h'
		}
	},
	data() {
		return {
			canvasId: 'temperatureChart_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
			ctx: null,
			canvasWidth: 0,
			canvasHeight: 0,
			showTooltip: false,
			tooltipText: '',
			tooltipStyle: {}
		}
	},
	watch: {
		data: {
			handler() {
				this.$nextTick(() => {
					this.drawChart()
				})
			},
			deep: true
		},
		period() {
			this.$nextTick(() => {
				this.drawChart()
			})
		}
	},
	mounted() {
		this.initCanvas()
	},
	methods: {
		// 初始化Canvas
		initCanvas() {
			// #ifdef APP-PLUS
			// APP环境下需要延迟获取canvas上下文
			setTimeout(() => {
				const query = uni.createSelectorQuery().in(this)
				query.select('.chart-canvas').boundingClientRect(rect => {
					if (rect) {
						this.canvasWidth = rect.width
						this.canvasHeight = rect.height
						
						// APP环境下使用不同的canvas上下文获取方式
						this.ctx = uni.createCanvasContext(this.canvasId, this)
						this.$nextTick(() => {
							this.drawChart()
						})
					}
				}).exec()
			}, 100)
			// #endif
			
			// #ifndef APP-PLUS
			// H5和小程序环境
			const query = uni.createSelectorQuery().in(this)
			query.select('.chart-canvas').boundingClientRect(rect => {
				if (rect) {
					this.canvasWidth = rect.width
					this.canvasHeight = rect.height
					
					this.ctx = uni.createCanvasContext(this.canvasId, this)
					this.drawChart()
				}
			}).exec()
			// #endif
		},
		
		// 绘制图表
		drawChart() {
			if (!this.ctx || !this.data || this.data.length === 0) {
				return
			}
			
			// 清空画布
			this.ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight)
			
			// 设置画布样式
			this.ctx.setFillStyle('#ffffff')
			this.ctx.fillRect(0, 0, this.canvasWidth, this.canvasHeight)
			
			// 计算绘图区域
			const padding = 40
			const chartWidth = this.canvasWidth - padding * 2
			const chartHeight = this.canvasHeight - padding * 2
			const chartX = padding
			const chartY = padding
			
			// 计算数据范围
			const values = this.data.map(item => item.value)
			const minValue = Math.min(...values)
			const maxValue = Math.max(...values)
			const valueRange = maxValue - minValue || 1
			
			// 绘制网格线
			this.drawGrid(chartX, chartY, chartWidth, chartHeight, minValue, maxValue)
			
			// 绘制数据线
			this.drawDataLine(chartX, chartY, chartWidth, chartHeight, minValue, valueRange)
			
			// 绘制数据点
			this.drawDataPoints(chartX, chartY, chartWidth, chartHeight, minValue, valueRange)
			
			// 绘制坐标轴标签
			this.drawLabels(chartX, chartY, chartWidth, chartHeight, minValue, maxValue)
			
			// APP-PLUS环境下需要调用draw(true)来确保绘制完成
			// #ifdef APP-PLUS
			this.ctx.draw(true)
			// #endif
			
			// #ifndef APP-PLUS
			this.ctx.draw()
			// #endif
		},
		
		// 绘制网格线
		drawGrid(x, y, width, height, minValue, maxValue) {
			this.ctx.setStrokeStyle('#f0f0f0')
			this.ctx.setLineWidth(1)
			
			// 水平网格线
			for (let i = 0; i <= 4; i++) {
				const gridY = y + (height / 4) * i
				this.ctx.beginPath()
				this.ctx.moveTo(x, gridY)
				this.ctx.lineTo(x + width, gridY)
				this.ctx.stroke()
			}
			
			// 垂直网格线
			const timePoints = this.period === '24h' ? 6 : 7 // 24小时显示6条线，7天显示7条线
			for (let i = 0; i <= timePoints; i++) {
				const gridX = x + (width / timePoints) * i
				this.ctx.beginPath()
				this.ctx.moveTo(gridX, y)
				this.ctx.lineTo(gridX, y + height)
				this.ctx.stroke()
			}
		},
		
		// 绘制数据线
		drawDataLine(x, y, width, height, minValue, valueRange) {
			if (this.data.length < 2) return
			
			this.ctx.setStrokeStyle('#007AFF')
			this.ctx.setLineWidth(2)
			this.ctx.beginPath()
			
			this.data.forEach((item, index) => {
				const pointX = x + (width / (this.data.length - 1)) * index
				const pointY = y + height - ((item.value - minValue) / valueRange) * height
				
				if (index === 0) {
					this.ctx.moveTo(pointX, pointY)
				} else {
					this.ctx.lineTo(pointX, pointY)
				}
			})
			
			this.ctx.stroke()
		},
		
		// 绘制数据点
		drawDataPoints(x, y, width, height, minValue, valueRange) {
			this.ctx.setFillStyle('#007AFF')
			
			this.data.forEach((item, index) => {
				const pointX = x + (width / (this.data.length - 1)) * index
				const pointY = y + height - ((item.value - minValue) / valueRange) * height
				
				this.ctx.beginPath()
				this.ctx.arc(pointX, pointY, 3, 0, 2 * Math.PI)
				this.ctx.fill()
			})
		},
		
		// 绘制坐标轴标签
		drawLabels(x, y, width, height, minValue, maxValue) {
			this.ctx.setFillStyle('#666666')
			this.ctx.setFontSize(12)
			
			// Y轴标签（温度值）
			for (let i = 0; i <= 4; i++) {
				const value = minValue + (maxValue - minValue) * (1 - i / 4)
				const labelY = y + (height / 4) * i
				this.ctx.fillText(value.toFixed(1) + '°C', 5, labelY + 4)
			}
			
			// X轴标签（时间）
			const timePoints = this.period === '24h' ? 6 : 7
			for (let i = 0; i <= timePoints; i++) {
				const labelX = x + (width / timePoints) * i
				let timeLabel = ''
				
				if (this.period === '24h') {
					timeLabel = (i * 4) + ':00' // 每4小时一个标签
				} else {
					const date = new Date()
					date.setDate(date.getDate() - (6 - i))
					timeLabel = (date.getMonth() + 1) + '/' + date.getDate()
				}
				
				this.ctx.fillText(timeLabel, labelX - 15, y + height + 20)
			}
		},
		
		// 触摸开始
		onTouchStart(e) {
			// 可以实现触摸交互功能
		},
		
		// 触摸移动
		onTouchMove(e) {
			// 可以实现数据点提示功能
		},
		
		// 触摸结束
		onTouchEnd(e) {
			this.showTooltip = false
		}
	}
}
</script>

<style scoped>
.chart-container {
	position: relative;
	width: 100%;
	height: 400rpx;
}

.chart-canvas {
	width: 100%;
	height: 100%;
	background-color: #ffffff;
	border-radius: 10rpx;
}

.tooltip {
	position: absolute;
	background-color: rgba(0, 0, 0, 0.8);
	color: white;
	padding: 10rpx 15rpx;
	border-radius: 8rpx;
	font-size: 24rpx;
	pointer-events: none;
	z-index: 10;
}

.tooltip-text {
	color: white;
	font-size: 24rpx;
}
</style>