<template>
  <div class="action-container">
    <!-- 标题区 -->
    <div class="page-header">
      <div class="header-icon">
        <el-icon :size="28"><VideoCamera /></el-icon>
      </div>
      <div class="header-text">
        <h2>AI 动作计数</h2>
        <p>实时识别健身动作，智能语音播报</p>
      </div>
    </div>

    <!-- 视频预览区 -->
    <div class="video-wrapper">
      <div class="video-frame" :class="{ active: isStart }">
        <video ref="videoEl" class="video-feed" autoplay playsinline muted></video>
        <canvas ref="canvasEl" class="overlay-canvas"></canvas>
        <div v-if="!isStart" class="video-idle">
          <div class="idle-icon">
            <el-icon :size="64"><VideoCamera /></el-icon>
          </div>
          <p class="idle-title">摄像头预览</p>
          <p class="idle-desc">选择动作类型后点击开始</p>
        </div>
        <!-- 状态角标 -->
        <div v-if="isStart" class="status-badge" :class="{ paused: isPaused }">
          <span class="status-dot"></span>
          {{ isPaused ? '已暂停' : loadingModel ? '模型加载中...' : '检测中' }}
        </div>
        <div v-if="cameraError" class="camera-error">
          <el-icon :size="20"><WarningFilled /></el-icon>
          <span>{{ cameraError }}</span>
        </div>
        <!-- 调试信息（实时角度/状态） -->
        <div v-if="isStart" class="debug-info">
          <span v-if="debugText">{{ debugText }}</span>
        </div>
      </div>
    </div>

    <!-- 控制栏 -->
    <div class="control-bar">
      <div class="control-left">
        <el-select v-model="actionType" :disabled="isStart" placeholder="选择动作" size="large" class="action-select">
          <el-option label="🦵 深蹲" value="squat" />
          <el-option label="🖐️ 臂展" value="arm" />
          <el-option label="💪 俯卧撑" value="pushup" />
          <el-option label="🤸 开合跳" value="jumpingjack" />
          <el-option label="🏃 高抬腿" value="highknee" />
        </el-select>
      </div>
      <div class="control-right">
        <el-button
          v-if="!isStart"
          type="success"
          size="large"
          :icon="VideoPlay"
          @click="start"
          class="btn-start"
        >
          开始计数
        </el-button>
        <el-button
          v-else
          :type="isPaused ? 'success' : 'warning'"
          size="large"
          :icon="isPaused ? VideoPlay : VideoPause"
          @click="pause"
        >
          {{ isPaused ? '继续' : '暂停' }}
        </el-button>
        <el-button size="large" :icon="RefreshLeft" @click="reset" class="btn-reset">
          重置
        </el-button>
        <el-button size="large" :icon="Close" type="danger" @click="stop" plain>
          结束
        </el-button>
      </div>
    </div>

    <!-- 计数展示 -->
    <transition name="count-fade">
      <div v-if="isStart" class="count-section">
        <div class="count-card">
          <span class="count-label">当前计数</span>
          <div class="count-display">
            <span class="count-number">{{ count }}</span>
            <span class="count-unit">次</span>
          </div>
          <div class="count-bar">
            <div class="count-bar-fill" :style="{ width: countProgress + '%' }"></div>
          </div>
          <span class="count-target">目标 20 次</span>
        </div>
      </div>
    </transition>

    <!-- 动作提示 -->
    <transition name="tip-fade">
      <div v-if="isStart" class="tip-card">
        <div class="tip-icon">
          <el-icon :size="20"><InfoFilled /></el-icon>
        </div>
        <div class="tip-content">
          <template v-if="actionType === 'squat'">
            <p class="tip-title">深蹲动作要领</p>
            <p>双脚与肩同宽，背部挺直 → 缓慢下蹲至大腿与地面平行 → 站起还原</p>
          </template>
          <template v-else-if="actionType === 'arm'">
            <p class="tip-title">臂展动作要领</p>
            <p>双臂平举至与肩同高 → 缓慢放下至身体两侧 → 重复动作</p>
          </template>
          <template v-else-if="actionType === 'pushup'">
            <p class="tip-title">俯卧撑动作要领</p>
            <p>双手撑地，身体保持一条直线 → 屈臂下降至胸部接近地面 → 撑起还原</p>
          </template>
          <template v-else-if="actionType === 'jumpingjack'">
            <p class="tip-title">开合跳动作要领</p>
            <p>双脚并拢站立 → 跳起双脚分开、双臂上举 → 跳回并拢还原</p>
          </template>
          <template v-else>
            <p class="tip-title">高抬腿动作要领</p>
            <p>原地快速交替抬腿，膝盖尽量抬至髋部高度 → 保持节奏</p>
          </template>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { VideoCamera, VideoPlay, VideoPause, RefreshLeft, Close, InfoFilled, WarningFilled } from '@element-plus/icons-vue'

const videoEl = ref(null)
const canvasEl = ref(null)
const actionType = ref('squat')
const isStart = ref(false)
const isPaused = ref(false)
const count = ref(0)
const loadingModel = ref(false)
const cameraError = ref('')
const debugText = ref('')
let bestVoice = null
let stream = null
let poseLandmarker = null
let detectTimer = null
let lastVideoTime = -1

// 动作状态机
let squatState = 'up' // up / down
let armState = 'down' // down / up
let pushupState = 'up' // up / down
let jackState = 'closed' // closed / open
let highKneeState = 'down' // down / up

// 关键点平滑缓冲（滑动平均，消除抖动）
let smoothBuffer = []
const SMOOTH_WINDOW = 3

// 防抖计数（连续 N 帧满足才切换状态）
let downFrames = 0
let upFrames = 0
const DEBOUNCE_FRAMES = 3

// 深蹲基准线（站直时肩膀的 y 坐标，动态标定）
let baselineY = null
const SQUAT_DROP_RATIO = 0.15 // 肩膀下沉超过身高的 15% 算一次
const BASELINE_OFFSET_RATIO = 0.05 // 基准线上移身高的 5%（更灵敏）

// 平滑关键点：对每个关键点的 x/y 做滑动平均
function smoothLandmarks(lm) {
  smoothBuffer.push(lm)
  if (smoothBuffer.length > SMOOTH_WINDOW) smoothBuffer.shift()
  if (smoothBuffer.length < SMOOTH_WINDOW) return lm
  const result = lm.map((p, i) => {
    let sx = 0, sy = 0, count = 0
    for (const buf of smoothBuffer) {
      const bp = buf[i]
      if (bp && bp.visibility > 0.3) {
        sx += bp.x; sy += bp.y; count++
      }
    }
    if (count === 0) return p
    return { ...p, x: sx / count, y: sy / count }
  })
  return result
}

const countProgress = computed(() => Math.min((count.value / 20) * 100, 100))

const loadVoice = () => {
  const synth = window.speechSynthesis
  if (!synth) return
  synth.onvoiceschanged = () => {
    const voices = synth.getVoices()
    bestVoice = voices.find(v => v.name.includes('Xiaoxiao')) || voices.find(v => v.lang.startsWith('zh'))
  }
}
loadVoice()

const speak = (text) => {
  if (!window.speechSynthesis) return
  window.speechSynthesis.cancel()
  const u = new SpeechSynthesisUtterance(text)
  u.lang = 'zh-CN'
  u.rate = 0.95
  u.pitch = 1.05
  if (bestVoice) u.voice = bestVoice
  window.speechSynthesis.speak(u)
}

// ===== 加载 MediaPipe PoseLandmarker =====
async function loadPoseModel() {
  loadingModel.value = true
  try {
    // 动态 import MediaPipe tasks-vision（unpkg CDN）
    const vision = await import('https://unpkg.com/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs')
    const filesetResolver = vision.FilesetResolver
    const visionFiles = await filesetResolver.forVisionTasks('https://unpkg.com/@mediapipe/tasks-vision@0.10.14/wasm')

    poseLandmarker = await vision.PoseLandmarker.createFromOptions(visionFiles, {
      baseOptions: {
        modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task',
        delegate: 'CPU',
      },
      runningMode: 'VIDEO',
      numPoses: 1,
      minPoseDetectionConfidence: 0.5,
      minPosePresenceConfidence: 0.5,
      minTrackingConfidence: 0.5,
    })
    loadingModel.value = false
    return true
  } catch (e) {
    console.error('模型加载失败:', e)
    cameraError.value = '模型加载失败，请检查网络后重试'
    loadingModel.value = false
    return false
  }
}

// ===== 打开摄像头 =====
async function openCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: 640, height: 480 },
      audio: false,
    })
    const video = videoEl.value
    video.srcObject = stream
    await video.play()
    cameraError.value = ''
    return true
  } catch (e) {
    console.error('摄像头打开失败:', e)
    if (e.name === 'NotAllowedError') {
      cameraError.value = '摄像头权限被拒绝，请在浏览器地址栏允许访问摄像头'
    } else if (e.name === 'NotFoundError') {
      cameraError.value = '未检测到摄像头设备'
    } else {
      cameraError.value = '摄像头打开失败：' + e.message
    }
    return false
  }
}

// ===== 开始 =====
async function start() {
  const ok = await openCamera()
  if (!ok) return
  const modelOk = await loadPoseModel()
  if (!modelOk) return

  isStart.value = true
  isPaused.value = false
  count.value = 0
  squatState = 'up'
  armState = 'down'
  pushupState = 'up'
  jackState = 'closed'
  highKneeState = 'down'
  baselineY = null
  smoothBuffer = []
  speak('开始')
  detectLoop()
}

// ===== 暂停/继续 =====
const pause = () => {
  isPaused.value = !isPaused.value
  isPaused.value ? speak('暂停') : speak('继续')
}

// ===== 重置 =====
const reset = () => {
  count.value = 0
  squatState = 'up'
  armState = 'down'
  pushupState = 'up'
  jackState = 'closed'
  highKneeState = 'down'
  baselineY = null
  smoothBuffer = []
  speak('已重置')
}

// ===== 结束 =====
const stop = () => {
  isStart.value = false
  isPaused.value = false
  clearInterval(detectTimer)
  if (stream) {
    stream.getTracks().forEach(t => t.stop())
    stream = null
  }
  count.value = 0
  speak('结束')
}

// ===== 检测循环 =====
function detectLoop() {
  clearInterval(detectTimer)
  detectTimer = setInterval(() => {
    if (isPaused.value) return
    detectPose()
  }, 100)
}

async function detectPose() {
  if (!poseLandmarker || !videoEl.value) return
  const video = videoEl.value
  if (video.readyState < 2) return
  if (video.currentTime === lastVideoTime) return
  lastVideoTime = video.currentTime

  try {
    const result = poseLandmarker.detectForVideo(video, performance.now())
    if (result.landmarks && result.landmarks.length > 0) {
      const rawLm = result.landmarks[0]
      drawSkeleton(rawLm)
      const smLm = smoothLandmarks(rawLm)
      judgeAction(smLm)
    } else {
      clearCanvas()
    }
  } catch (e) {
    // 忽略单帧错误
  }
}

// ===== 关键点索引（MediaPipe Pose 33 点）=====
const KP = {
  nose: 0,
  leftShoulder: 11, rightShoulder: 12,
  leftElbow: 13, rightElbow: 14,
  leftWrist: 15, rightWrist: 16,
  leftHip: 23, rightHip: 24,
  leftKnee: 25, rightKnee: 26,
  leftAnkle: 27, rightAnkle: 28,
}

// 计算三点角度（以 b 为顶点）
function angle3(a, b, c) {
  const ab = Math.atan2(a.y - b.y, a.x - b.x)
  const cb = Math.atan2(c.y - b.y, c.x - b.x)
  let ang = Math.abs(ab - cb) * 180 / Math.PI
  if (ang > 180) ang = 360 - ang
  return ang
}

// ===== 动作判定 =====
function judgeAction(lm) {
  switch (actionType.value) {
    case 'squat': judgeSquat(lm); break
    case 'arm': judgeArm(lm); break
    case 'pushup': judgePushup(lm); break
    case 'jumpingjack': judgeJumpingJack(lm); break
    case 'highknee': judgeHighKnee(lm); break
  }
}

// 取左右腿膝盖角度的平均值
function avgKneeAngle(lm) {
  const l = [lm[KP.leftHip], lm[KP.leftKnee], lm[KP.leftAnkle]]
  const r = [lm[KP.rightHip], lm[KP.rightKnee], lm[KP.rightAnkle]]
  let angles = []
  if (l.every(p => p && p.visibility > 0.4)) angles.push(angle3(l[0], l[1], l[2]))
  if (r.every(p => p && p.visibility > 0.4)) angles.push(angle3(r[0], r[1], r[2]))
  if (angles.length === 0) return null
  return angles.reduce((a, b) => a + b, 0) / angles.length
}

// 身体高度基准：肩膀到脚踝的垂直距离（归一化基准，自适应摄像头距离）
function bodyHeight(lm) {
  const shoulder = lm[KP.leftShoulder] || lm[KP.rightShoulder]
  const ankle = lm[KP.leftAnkle] || lm[KP.rightAnkle]
  if (!shoulder || !ankle) return null
  return Math.abs(shoulder.y - ankle.y)
}

// 深蹲：肩膀相对基准线下沉（动态标定基准线），简单直观
function judgeSquat(lm) {
  const shoulder = lm[KP.leftShoulder] || lm[KP.rightShoulder]
  if (!shoulder || shoulder.visibility < 0.4) return
  const h = bodyHeight(lm)
  if (!h || h < 0.05) return

  // 首次检测到站直姿态时，标定基准线（肩膀的 y 坐标，往上提一点更灵敏）
  if (baselineY === null) {
    baselineY = shoulder.y - h * BASELINE_OFFSET_RATIO
  }

  // 肩膀下沉量（相对基准线），除以身体高度得到比例
  const drop = shoulder.y - baselineY
  const dropRatio = drop / h
  const isDown = dropRatio > SQUAT_DROP_RATIO
  const isUp = dropRatio < 0.04

  // 实时调试信息
  debugText.value = `${squatState === 'up' ? '站立' : '下蹲'} | 下沉 ${(dropRatio * 100).toFixed(0)}% | 基准 ${baselineY.toFixed(2)}`

  if (squatState === 'up') {
    if (isDown) {
      downFrames++
      if (downFrames >= DEBOUNCE_FRAMES) {
        squatState = 'down'
        downFrames = 0
      }
    } else {
      downFrames = 0
    }
  } else {
    if (isUp) {
      upFrames++
      if (upFrames >= DEBOUNCE_FRAMES) {
        squatState = 'up'
        upFrames = 0
        count.value += 1
        speak(count.value + '个')
      }
    } else {
      upFrames = 0
    }
  }
}

// 臂展：手腕高于肩为举臂，低于为放下
function judgeArm(lm) {
  const shoulder = lm[KP.leftShoulder] || lm[KP.rightShoulder]
  const wrist = lm[KP.leftWrist] || lm[KP.rightWrist]
  if (!shoulder || !wrist) return
  const wristAbove = wrist.y < shoulder.y - 0.06
  if (armState === 'down' && wristAbove) {
    armState = 'up'
  } else if (armState === 'up' && !wristAbove) {
    armState = 'down'
    count.value += 1
    speak(count.value + '个')
  }
}

// 俯卧撑：手肘弯曲角度判断（身体水平时，肘从伸直到弯曲再到伸直）
function judgePushup(lm) {
  const lShoulder = lm[KP.leftShoulder]
  const lElbow = lm[KP.leftElbow]
  const lWrist = lm[KP.leftWrist]
  const rShoulder = lm[KP.rightShoulder]
  const rElbow = lm[KP.rightElbow]
  const rWrist = lm[KP.rightWrist]
  let angles = []
  if (lShoulder && lElbow && lWrist && lShoulder.visibility > 0.4 && lElbow.visibility > 0.4 && lWrist.visibility > 0.4)
    angles.push(angle3(lShoulder, lElbow, lWrist))
  if (rShoulder && rElbow && rWrist && rShoulder.visibility > 0.4 && rElbow.visibility > 0.4 && rWrist.visibility > 0.4)
    angles.push(angle3(rShoulder, rElbow, rWrist))
  if (angles.length === 0) return
  const elbowAngle = angles.reduce((a, b) => a + b, 0) / angles.length
  const isDown = elbowAngle < 85
  const isUp = elbowAngle > 135

  if (pushupState === 'up' && isDown) {
    pushupState = 'down'
  } else if (pushupState === 'down' && isUp) {
    pushupState = 'up'
    count.value += 1
    speak(count.value + '个')
  }
}

// 开合跳：双手距离变化判断（并拢→分开→并拢）
function judgeJumpingJack(lm) {
  const lw = lm[KP.leftWrist]
  const rw = lm[KP.rightWrist]
  if (!lw || !rw || lw.visibility < 0.4 || rw.visibility < 0.4) return
  const handDist = Math.abs(lw.x - rw.x)
  const isOpen = handDist > 0.5
  const isClosed = handDist < 0.25

  if (jackState === 'closed' && isOpen) {
    jackState = 'open'
  } else if (jackState === 'open' && isClosed) {
    jackState = 'closed'
    count.value += 1
    speak(count.value + '个')
  }
}

// 高抬腿：大腿抬起角度（髋→膝相对竖直方向），弯折腿部即算
function judgeHighKnee(lm) {
  const lHip = lm[KP.leftHip]
  const rHip = lm[KP.rightHip]
  const lKnee = lm[KP.leftKnee]
  const rKnee = lm[KP.rightKnee]
  if (!lHip || !rHip || !lKnee || !rKnee) return

  // 大腿相对竖直方向（向下为 0°）的抬起角度
  function thighAngle(hip, knee) {
    const dy = knee.y - hip.y
    const dx = knee.x - hip.x
    // 与竖直向下方向的夹角
    const ang = Math.atan2(Math.abs(dx), dy) * 180 / Math.PI
    return ang
  }
  const lAng = thighAngle(lHip, lKnee)
  const rAng = thighAngle(rHip, rKnee)
  // 大腿抬起超过 30° 算弯折（抬腿）
  const lRaised = lAng > 30
  const rRaised = rAng > 30

  // 实时调试信息
  debugText.value = `高抬腿 | 左腿 ${Math.round(lAng)}° 右腿 ${Math.round(rAng)}°`

  if (highKneeState === 'down' && lRaised && !rRaised) {
    highKneeState = 'left'
  } else if (highKneeState === 'left' && rRaised && !lRaised) {
    highKneeState = 'right'
    count.value += 1
    speak(count.value + '个')
  } else if (highKneeState === 'right' && lRaised && !rRaised) {
    highKneeState = 'left'
    count.value += 1
    speak(count.value + '个')
  }
}

// ===== 绘制骨架 =====
const SKELETON_EDGES = [
  [11, 12], [11, 13], [13, 15], [12, 14], [14, 16],
  [11, 23], [12, 24], [23, 24],
  [23, 25], [25, 27], [24, 26], [26, 28],
]

function drawSkeleton(lm) {
  const canvas = canvasEl.value
  const video = videoEl.value
  if (!canvas || !video) return
  canvas.width = video.videoWidth || 640
  canvas.height = video.videoHeight || 480
  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  // 画骨架连线
  ctx.strokeStyle = '#00e676'
  ctx.lineWidth = 3
  SKELETON_EDGES.forEach(([a, b]) => {
    const p1 = lm[a], p2 = lm[b]
    if (p1 && p2 && p1.visibility > 0.4 && p2.visibility > 0.4) {
      ctx.beginPath()
      ctx.moveTo(p1.x * canvas.width, p1.y * canvas.height)
      ctx.lineTo(p2.x * canvas.width, p2.y * canvas.height)
      ctx.stroke()
    }
  })

  // 画关键点
  ctx.fillStyle = '#ff6d00'
  lm.forEach((p, i) => {
    if (p.visibility > 0.4) {
      ctx.beginPath()
      ctx.arc(p.x * canvas.width, p.y * canvas.height, 4, 0, 2 * Math.PI)
      ctx.fill()
    }
  })

  // 深蹲时画基准线（站直肩膀位置）
  if (actionType.value === 'squat' && baselineY !== null) {
    const y = baselineY * canvas.height
    ctx.strokeStyle = '#ffd600'
    ctx.lineWidth = 2
    ctx.setLineDash([8, 6])
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(canvas.width, y)
    ctx.stroke()
    ctx.setLineDash([])
    // 标签
    ctx.fillStyle = '#ffd600'
    ctx.font = '12px sans-serif'
    ctx.fillText('站直基准线', 8, y - 6)
  }
}

function clearCanvas() {
  const canvas = canvasEl.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, canvas.width, canvas.height)
}

onUnmounted(() => {
  clearInterval(detectTimer)
  if (stream) {
    stream.getTracks().forEach(t => t.stop())
  }
})
</script>

<style scoped>
.action-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding: 20px 24px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e8f4fd 100%);
  border-radius: 16px;
  border: 1px solid #d4e7f7;
}
.header-icon {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #ff8c00, #ffb347);
  border-radius: 14px;
  color: #fff;
  flex-shrink: 0;
}
.header-text h2 { margin: 0; font-size: 22px; font-weight: 700; color: #1d2b3a; }
.header-text p { margin: 4px 0 0; font-size: 13px; color: #6b7c8e; }

.video-wrapper { margin-bottom: 20px; }
.video-frame {
  position: relative;
  width: 100%;
  aspect-ratio: 4 / 3;
  max-height: 480px;
  background: #0f1419;
  border-radius: 16px;
  overflow: hidden;
  border: 3px solid #e5e7eb;
  transition: border-color 0.4s, box-shadow 0.4s;
}
.video-frame.active { border-color: #ff8c00; box-shadow: 0 0 0 4px rgba(64, 158, 255, 0.15); }
.video-feed { width: 100%; height: 100%; object-fit: cover; }
.overlay-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
.video-idle {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #8899aa;
  background: #0f1419;
}
.idle-icon { opacity: 0.5; margin-bottom: 12px; }
.idle-title { font-size: 18px; font-weight: 600; color: #a0b0c0; margin: 0 0 6px; }
.idle-desc { font-size: 13px; color: #6b7c8e; margin: 0; }

.camera-error {
  position: absolute;
  bottom: 14px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(245, 108, 108, 0.95);
  color: #fff;
  font-size: 13px;
  border-radius: 20px;
  white-space: nowrap;
}

.debug-info {
  position: absolute;
  bottom: 14px;
  left: 14px;
  padding: 6px 12px;
  background: rgba(0, 0, 0, 0.7);
  color: #00e676;
  font-size: 12px;
  font-family: monospace;
  border-radius: 6px;
  z-index: 2;
  white-space: nowrap;
}

.status-badge {
  position: absolute;
  top: 14px;
  right: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: rgba(0, 180, 42, 0.9);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  border-radius: 20px;
  backdrop-filter: blur(8px);
  z-index: 2;
}
.status-badge.paused { background: rgba(255, 125, 0, 0.9); }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #fff; animation: pulse-dot 1.5s ease-in-out infinite; }
.status-badge.paused .status-dot { animation: none; }
@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.7); }
}

.control-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 16px 20px;
  background: #fff;
  border-radius: 14px;
  border: 1px solid #ebeef5;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  margin-bottom: 20px;
}
.control-right { display: flex; gap: 10px; flex-wrap: wrap; }
.action-select { width: 160px; }
.btn-start { font-weight: 600; letter-spacing: 0.5px; }
.btn-reset { color: #ff8c00; border-color: #ff8c00; }

.count-section { margin-bottom: 20px; }
.count-card {
  text-align: center;
  padding: 28px 20px;
  background: linear-gradient(145deg, #ffffff, #f8fbff);
  border-radius: 16px;
  border: 1px solid #e8edf4;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.08);
}
.count-label { display: block; font-size: 13px; color: #909399; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px; }
.count-display { display: flex; align-items: baseline; justify-content: center; gap: 6px; margin-bottom: 16px; }
.count-number { font-size: 72px; font-weight: 800; color: #ff8c00; line-height: 1; font-variant-numeric: tabular-nums; }
.count-unit { font-size: 20px; color: #909399; font-weight: 500; }
.count-bar { height: 6px; background: #e8edf4; border-radius: 3px; overflow: hidden; max-width: 240px; margin: 0 auto 10px; }
.count-bar-fill { height: 100%; background: linear-gradient(90deg, #ff8c00, #ffb347); border-radius: 3px; transition: width 0.4s ease; }
.count-target { font-size: 12px; color: #b0b8c4; }

.tip-card {
  display: flex;
  gap: 14px;
  padding: 16px 20px;
  background: linear-gradient(135deg, #fff9f0, #fff7e8);
  border-radius: 12px;
  border-left: 4px solid #e6a23c;
}
.tip-icon { color: #e6a23c; flex-shrink: 0; margin-top: 2px; }
.tip-content p { margin: 0; font-size: 14px; color: #6b5e3e; line-height: 1.7; }
.tip-title { font-weight: 700 !important; color: #5a4a2a !important; margin-bottom: 4px !important; }

.count-fade-enter-active, .tip-fade-enter-active { transition: all 0.4s ease; }
.count-fade-leave-active, .tip-fade-leave-active { transition: all 0.25s ease; }
.count-fade-enter-from, .tip-fade-enter-from { opacity: 0; transform: translateY(12px); }
.count-fade-leave-to, .tip-fade-leave-to { opacity: 0; transform: translateY(-8px); }

@media (max-width: 640px) {
  .action-container { padding: 12px; }
  .control-bar { flex-direction: column; align-items: stretch; }
  .control-right { justify-content: center; }
  .action-select { width: 100%; }
  .count-number { font-size: 56px; }
}
</style>
