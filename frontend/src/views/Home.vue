<template>
  <div class="home-container">
    <!-- 顶部横幅 Hero 区 -->
    <section class="hero-banner">
      <div class="hero-content">
        <div class="hero-text">
          <span class="hero-badge">💪 智能健身 · 科学训练</span>
          <h1 class="hero-title">打造你的专属健身计划</h1>
          <p class="hero-desc">AI 识别食物热量、实时动作计数、肌肉图谱与训练视频，一站式管理你的健康生活。</p>
          <div class="hero-actions">
            <el-button type="warning" size="large" round @click="navigateTo('/food')">
              <el-icon><Camera /></el-icon> 开始记录饮食
            </el-button>
            <el-button size="large" round class="ghost-btn" @click="navigateTo('/action')">
              <el-icon><VideoCamera /></el-icon> 体验动作计数
            </el-button>
          </div>
        </div>
      </div>

      <!-- 数据统计 -->
      <div class="hero-stats">
        <div class="stat-item">
          <span class="stat-number">70+</span>
          <span class="stat-label">食物营养库</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">2</span>
          <span class="stat-label">AI 动作识别</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">24h</span>
          <span class="stat-label">饮食记录追踪</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">6</span>
          <span class="stat-label">核心功能模块</span>
        </div>
      </div>
    </section>

    <!-- 功能卡片区 -->
    <section class="feature-section">
      <div class="section-header">
        <h2 class="section-title">核心功能</h2>
        <span class="section-subtitle">选择模块开始你的健身之旅</span>
      </div>

      <div class="feature-grid">
        <div class="feature-card" @click="navigateTo('/food')">
          <div class="card-icon icon-food">
            <el-icon><Dish /></el-icon>
          </div>
          <h3 class="card-title">食物热量识别</h3>
          <p class="card-desc">上传图片识别食物，自动计算热量与营养</p>
          <span class="card-tag">AI 视觉</span>
        </div>

        <div class="feature-card" @click="navigateTo('/action')">
          <div class="card-icon icon-action">
            <el-icon><VideoCamera /></el-icon>
          </div>
          <h3 class="card-title">AI 动作计数</h3>
          <p class="card-desc">实时识别深蹲、臂展，智能语音播报次数</p>
          <span class="card-tag">实时检测</span>
        </div>

        <div class="feature-card" @click="navigateTo('/muscle3d')">
          <div class="card-icon icon-muscle">
            <el-icon><Avatar /></el-icon>
          </div>
          <h3 class="card-title">3D肌肉模型</h3>
          <p class="card-desc">查看人体肌肉分布，了解训练目标肌群</p>
          <span class="card-tag">知识库</span>
        </div>

        <div class="feature-card" @click="navigateTo('/video')">
          <div class="card-icon icon-video">
            <el-icon><Film /></el-icon>
          </div>
          <h3 class="card-title">健身视频专区</h3>
          <p class="card-desc">观看配套训练视频，跟着练更标准</p>
          <span class="card-tag">视频教学</span>
        </div>

        <div class="feature-card" @click="navigateTo('/community')">
          <div class="card-icon icon-community">
            <el-icon><ChatDotRound /></el-icon>
          </div>
          <h3 class="card-title">社区功能</h3>
          <p class="card-desc">分享健身心得，交流训练经验</p>
          <span class="card-tag">互动</span>
        </div>

        <div class="feature-card" @click="navigateTo('/food')">
          <div class="card-icon icon-data">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <h3 class="card-title">数据统计</h3>
          <p class="card-desc">近 7 天热量趋势，掌握每日营养摄入</p>
          <span class="card-tag">可视化</span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import {
  Dish, VideoCamera, Avatar, Film, ChatDotRound,
  TrendCharts, Camera
} from '@element-plus/icons-vue'

const router = useRouter()
const navigateTo = (path) => router.push(path)
</script>

<style scoped>
.home-container {
  padding: 24px;
  min-height: 100%;
}

/* ===== Hero 横幅 ===== */
.hero-banner {
  position: relative;
  padding: 48px 40px;
  border-radius: 20px;
  background:
    radial-gradient(circle at 85% 20%, rgba(255, 140, 0, 0.35), transparent 50%),
    radial-gradient(circle at 15% 80%, rgba(255, 100, 0, 0.25), transparent 45%),
    linear-gradient(135deg, #1a1a1a 0%, #2b2b2b 50%, #3a2a1a 100%);
  color: #fff;
  overflow: hidden;
  margin-bottom: 32px;
}

.hero-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.hero-text {
  max-width: 560px;
}

.hero-badge {
  display: inline-block;
  padding: 6px 14px;
  background: rgba(255, 140, 0, 0.2);
  border: 1px solid rgba(255, 140, 0, 0.5);
  border-radius: 20px;
  font-size: 13px;
  color: #ffb366;
  margin-bottom: 16px;
}

.hero-title {
  font-size: 34px;
  font-weight: 800;
  line-height: 1.25;
  margin: 0 0 12px;
  letter-spacing: 0.5px;
}

.hero-desc {
  font-size: 15px;
  color: #c9c9c9;
  line-height: 1.7;
  margin: 0 0 24px;
}

.hero-actions {
  display: flex;
  gap: 14px;
}

.ghost-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.4);
  color: #fff;
}
.ghost-btn:hover {
  border-color: #ff8c00;
  color: #ff8c00;
}

.hero-stats {
  display: flex;
  gap: 0;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
}

.stat-item {
  flex: 1;
  text-align: center;
  border-right: 1px solid rgba(255, 255, 255, 0.12);
}
.stat-item:last-child {
  border-right: none;
}

.stat-number {
  display: block;
  font-size: 28px;
  font-weight: 800;
  color: #ff8c00;
  line-height: 1;
}

.stat-label {
  display: block;
  font-size: 13px;
  color: #b0b0b0;
  margin-top: 6px;
}

/* ===== 功能卡片区 ===== */
.feature-section {
  margin-top: 8px;
}

.section-header {
  margin-bottom: 20px;
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0;
  display: inline-block;
  position: relative;
  padding-left: 14px;
}

.section-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 20px;
  background: #ff8c00;
  border-radius: 2px;
}

.section-subtitle {
  font-size: 13px;
  color: #999;
  margin-left: 14px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.feature-card {
  position: relative;
  background: #fff;
  border-radius: 16px;
  padding: 28px 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #f0f0f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.feature-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
  border-color: #ffd9a6;
}

.card-icon {
  width: 56px;
  height: 56px;
  margin-bottom: 18px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  color: #fff;
}

.icon-food { background: linear-gradient(135deg, #ff8c00, #ffb347); }
.icon-action { background: linear-gradient(135deg, #ff5e3a, #ff8c00); }
.icon-muscle { background: linear-gradient(135deg, #f5576c, #ff8c00); }
.icon-video { background: linear-gradient(135deg, #3a8dff, #6bb5ff); }
.icon-community { background: linear-gradient(135deg, #00c6a7, #00e0b8); }
.icon-data { background: linear-gradient(135deg, #7b5cff, #a78bff); }

.card-title {
  font-size: 17px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 8px;
}

.card-desc {
  font-size: 13px;
  color: #888;
  line-height: 1.6;
  margin: 0;
}

.card-tag {
  position: absolute;
  top: 20px;
  right: 20px;
  font-size: 11px;
  color: #ff8c00;
  background: #fff4e6;
  padding: 3px 10px;
  border-radius: 12px;
}

@media (max-width: 1200px) {
  .feature-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 640px) {
  .feature-grid { grid-template-columns: 1fr; }
  .hero-title { font-size: 26px; }
}
</style>
