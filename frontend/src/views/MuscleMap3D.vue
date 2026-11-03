<template>
  <div class="muscle3d-container">
    <!-- 顶部：性别切换 + 肌群筛选 -->
    <div class="top-controls">
      <div class="sex-tabs">
        <el-button
          v-for="tab in tabs"
          :key="tab.key"
          :class="{ active: activeTab === tab.key }"
          @click="switchTab(tab.key)"
        >
          {{ tab.name }}
        </el-button>
      </div>

      <div class="group-tabs">
        <el-button
          v-for="g in muscleGroups"
          :key="g.key"
          :class="{ active: currentGroup === g.key }"
          @click="selectGroup(g.key)"
        >
          {{ g.name }}
        </el-button>
      </div>
    </div>

    <div class="main-layout">
      <!-- 左侧：3D 人体模型 -->
      <div class="map-section">
        <div class="canvas-wrap" ref="canvasWrap">
          <div ref="canvasContainer" class="canvas-container"></div>

          <!-- 加载提示 -->
          <div v-if="loading" class="loading-overlay">
            <div class="loading-spinner"></div>
            <p>正在加载 3D 人体模型…</p>
          </div>

          <!-- 操作提示 -->
          <div class="hint-bar">
            <span>🖱️ 左键拖拽旋转</span>
            <span>🔍 滚轮缩放</span>
            <span>👆 点击肌肉查看详情</span>
          </div>
        </div>
      </div>

      <!-- 右侧：教程详情 -->
      <div class="tutorial-section">
        <div v-if="!currentGroup" class="empty-state">
          <div class="empty-icon">🏋️</div>
          <p>点击上方肌群按钮，或直接点击 3D 模型上的肌肉</p>
        </div>
        <div v-else class="tutorial-container">
          <div class="muscle-header">
            <h2 class="muscle-title">{{ currentInfo.name }}</h2>
            <el-tag type="danger" effect="dark" size="small">{{ currentInfo.group }}</el-tag>
          </div>

          <div class="muscle-intro">
            <h3>📖 肌群介绍</h3>
            <p>{{ currentInfo.description }}</p>
          </div>

          <div class="exercise-card" v-for="(item, idx) in currentInfo.exercises" :key="idx">
            <h3 class="exercise-name">{{ item.name }}</h3>

            <div class="video-wrapper" v-if="item.videoUrl">
              <video class="exercise-video" :src="item.videoUrl" controls preload="metadata" playsinline>
                您的浏览器不支持视频播放
              </video>
            </div>
            <div class="video-placeholder" v-else>
              <img src="@/assets/video-cover.png" alt="动作示范图" class="demo-img">
              <div class="placeholder-text"><span>🎬 视频待添加</span></div>
            </div>

            <div class="exercise-details">
              <h4>动作步骤：</h4>
              <ol class="steps-list">
                <li v-for="(step, sIdx) in item.steps" :key="sIdx">{{ step }}</li>
              </ol>
              <div class="tags">
                <el-tag size="small" type="info">{{ item.level }}</el-tag>
                <el-tag size="small" type="success">{{ item.equipment }}</el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'

// ============ 6 大肌群定义 ============
const muscleGroups = [
  { key: 'chest', name: '胸部', color: 0xe53935 },
  { key: 'shoulder', name: '肩部', color: 0xe53935 },
  { key: 'back', name: '背部', color: 0xe53935 },
  { key: 'abdomen', name: '腹部', color: 0xe53935 },
  { key: 'arm', name: '手臂', color: 0xe53935 },
  { key: 'glute', name: '臀部', color: 0xe53935 },
  { key: 'leg', name: '腿部', color: 0xe53935 }
]

// 模型里肌肉节点名 -> 6 大肌群 key 的映射
// 只保留常用肌群，其余（脚、手、颈部、膈肌、盆底肌等）归入 ignore
const nodeToGroup = {
  // 胸部
  chest_muscles_l: 'chest',
  chest_muscles_r: 'chest',
  // 肩部
  deltoid_l: 'shoulder',
  deltoid_r: 'shoulder',
  rotator_cuff_l: 'shoulder',
  rotator_cuff_r: 'shoulder',
  shoulder_muscles_l: 'shoulder',
  shoulder_muscles_r: 'shoulder',
  // 背部（含斜方肌，斜方肌属于上背部）
  back_muscles_l: 'back',
  back_muscles_r: 'back',
  trapezius_l: 'back',
  trapezius_r: 'back',
  // 腹部
  abdominal_muscles: 'abdomen',
  intercostals_l: 'abdomen',
  intercostals_r: 'abdomen',
  // 手臂（上臂二头/三头 + 前臂）
  upper_arm_muscles_l: 'arm',
  upper_arm_muscles_r: 'arm',
  forearm_muscles_l: 'arm',
  forearm_muscles_r: 'arm',
  // 腿部
  quadriceps_l: 'leg',
  quadriceps_r: 'leg',
  hamstrings_l: 'leg',
  hamstrings_r: 'leg',
  adductors_l: 'leg',
  adductors_r: 'leg',
  calf_l: 'leg',
  calf_r: 'leg',
  shin_muscles_l: 'leg',
  shin_muscles_r: 'leg',
  // 臀部
  gluteal_l: 'glute',
  gluteal_r: 'glute',
  // 以下归入 ignore（不参与 6 大肌群）
  foot_muscles_l: 'ignore',
  foot_muscles_r: 'ignore',
  hand_muscles_l: 'ignore',
  hand_muscles_r: 'ignore',
  neck_muscles_l: 'ignore',
  neck_muscles_r: 'ignore',
  diaphragm: 'ignore',
  pelvic_floor: 'ignore',
  iliopsoas_l: 'ignore',
  iliopsoas_r: 'ignore'
}

// 6 大肌群的中文教程数据
const muscleData = {
  chest: {
    name: '胸部',
    group: '胸部',
    description: '胸部肌群以胸大肌为主，呈扇形覆盖胸前，是塑造饱满胸型的关键。主要功能是使手臂内收、内旋和向前推。卧推、飞鸟、俯卧撑都是经典训练动作。',
    exercises: [
      { name: '杠铃卧推', level: '中级', equipment: '杠铃', videoUrl: '/videos/barbell-bench-press.mp4', steps: ['躺在卧推凳上，双脚平放地面，背部贴紧凳面', '双手握杠铃，握距略宽于肩，手腕保持直立', '吸气，缓慢下放杠铃至胸前（乳头线位置）', '发力推起至手臂伸直但不锁死，呼气', '每组 8-12 次，做 3-4 组'] },
      { name: '哑铃飞鸟', level: '中级', equipment: '哑铃', videoUrl: '/videos/dumbbell-fly.mp4', steps: ['仰卧在平凳上，双手各持哑铃举至胸部上方', '手臂微弯保持固定角度，向两侧缓慢打开', '感受胸肌拉伸，下放到与肩同高', '用胸肌力量将哑铃夹回起始位置', '每组 10-15 次，做 3 组'] },
      { name: '俯卧撑', level: '初级', equipment: '无', videoUrl: '/videos/push-up.mp4', steps: ['双手撑地略宽于肩，身体呈一条直线', '收紧核心和臀部，不要塌腰或撅臀', '缓慢下降至胸部接近地面', '发力推起回到起始位置', '每组做到力竭，做 3-4 组'] }
    ]
  },
  shoulder: {
    name: '肩部',
    group: '肩部',
    description: '肩部以三角肌为主，分前、中、后三束，负责手臂外展、前举和后伸。侧平举、推举、前平举等动作能全面锻炼肩部，塑造饱满的肩部线条。',
    exercises: [
      { name: '前平举', level: '初级', equipment: '哑铃', videoUrl: '/videos/front-raise.mp4', steps: ['站立，双手握哑铃垂于大腿前方', '手臂微弯，将哑铃向前平举至肩高', '控制速度，不要借力摆动身体', '缓慢下放回到起始位置', '每组 12-15 次，做 3 组'] },
      { name: '哑铃推举', level: '中级', equipment: '哑铃', videoUrl: '/videos/shoulder-press.mp4', steps: ['坐姿或站姿，双手持哑铃举至肩部两侧', '核心收紧，背部挺直，不要后仰', '向上推举至手臂伸直，哑铃在头顶正上方', '缓慢下放回到起始位置', '每组 8-12 次，做 3-4 组'] },
      { name: '哑铃侧平举', level: '初级', equipment: '哑铃', videoUrl: '/videos/lateral-raise-new.mp4', steps: ['双手握哑铃垂于身体两侧，掌心相对', '手臂微弯保持固定角度，肘关节略高于手腕', '向两侧平举至肩高，不要耸肩', '在最高点稍作停顿，缓慢回落', '每组 12-15 次，做 3-4 组'] }
    ]
  },
  back: {
    name: '背部',
    group: '背部',
    description: '背部肌群以背阔肌和斜方肌为主，呈倒三角形，是"倒三角身材"的关键。主要负责手臂内收、后伸和肩胛骨活动。引体向上、划船、耸肩是锻炼背部的王牌动作。',
    exercises: [
      { name: '引体向上', level: '中级', equipment: '单杠', videoUrl: '/videos/push-up.mp4', steps: ['双手正握单杠，握距略宽于肩', '收紧核心，肩胛骨下沉', '用背部力量将身体拉起至下巴过杠', '缓慢下放至手臂伸直', '每组做到力竭，做 3-4 组'] },
      { name: '俯卧撑', level: '初级', equipment: '无', videoUrl: '/videos/push-up.mp4', steps: ['双手撑地略宽于肩，身体呈一条直线', '收紧核心和臀部，不要塌腰或撅臀', '缓慢下降至胸部接近地面', '发力推起回到起始位置', '每组做到力竭，做 3-4 组'] }
    ]
  },
  arm: {
    name: '手臂',
    group: '手臂',
    description: '手臂肌群包含肱二头肌、肱三头肌和前臂肌群。肱二头肌负责屈肘，肱三头肌负责伸肘，是"麒麟臂"的关键。弯举、臂屈伸等动作能有效锻炼手臂。',
    exercises: [
      { name: '哑铃弯举', level: '初级', equipment: '哑铃', videoUrl: '/videos/lateral-raise-new.mp4', steps: ['站立，双手握哑铃垂于身体两侧，掌心向前', '保持上臂贴紧身体，屈肘将哑铃举起', '在最高点收缩肱二头肌，停顿 1 秒', '缓慢下放回到起始位置', '每组 10-12 次，做 3-4 组'] },
      { name: '俯卧撑', level: '初级', equipment: '无', videoUrl: '/videos/push-up.mp4', steps: ['双手撑地略宽于肩，身体呈一条直线', '收紧核心和臀部，不要塌腰或撅臀', '缓慢下降至胸部接近地面', '发力推起回到起始位置', '每组做到力竭，做 3-4 组'] }
    ]
  },
  abdomen: {
    name: '腹部',
    group: '腹部',
    description: '腹部以腹直肌为主，就是我们常说的"八块腹肌"，从胸骨延伸到耻骨。主要功能是使躯干前屈、稳定核心。卷腹、平板支撑、仰卧举腿都能有效刺激腹部。',
    exercises: [
      { name: '平板支撑', level: '初级', equipment: '无', videoUrl: '/videos/plank-new.mp4', steps: ['双肘撑地与肩同宽，脚尖着地', '身体保持一条直线，收紧腹部和臀部', '眼睛看向地面，保持颈部自然', '均匀呼吸不要憋气', '每组坚持 30-60 秒，做 3-4 组'] },
      { name: '卷腹', level: '初级', equipment: '无', videoUrl: '/videos/crunch.mp4', steps: ['仰卧屈膝，双脚平放地面，双手交叉放胸前', '用腹部力量将上半身卷起，下背部贴地', '在最高点停顿 1 秒，感受腹肌收缩', '缓慢下放回到起始位置', '每组 15-20 次，做 3-4 组'] },
      { name: '仰卧举腿', level: '中级', equipment: '无', videoUrl: '/videos/leg-raise-new.mp4', steps: ['仰卧在垫子上，双手放身体两侧', '双腿并拢伸直，缓慢抬起至与地面垂直', '下背部始终贴地，用下腹发力', '控制速度缓慢下放，脚不触地', '每组 12-15 次，做 3 组'] }
    ]
  },
  leg: {
    name: '腿部',
    group: '腿部',
    description: '腿部肌群包含股四头肌、腘绳肌、内收肌和小腿肌群，是人体最大的肌群，负责支撑和移动身体。深蹲、箭步蹲、提踵等动作能有效锻炼腿部力量。',
    exercises: [
      { name: '杠铃深蹲', level: '中级', equipment: '杠铃', videoUrl: '/videos/barbell-bench-press.mp4', steps: ['双脚与肩同宽站立，杠铃置于上背部', '收紧核心，屈髋屈膝下蹲至大腿与地面平行', '膝盖与脚尖方向一致，不要内扣', '发力站起回到起始位置', '每组 8-12 次，做 3-4 组'] },
      { name: '平板支撑', level: '初级', equipment: '无', videoUrl: '/videos/plank-new.mp4', steps: ['双肘撑地与肩同宽，脚尖着地', '身体保持一条直线，收紧腹部和臀部', '眼睛看向地面，保持颈部自然', '均匀呼吸不要憋气', '每组坚持 30-60 秒，做 3-4 组'] }
    ]
  },
  glute: {
    name: '臀部',
    group: '臀部',
    description: '臀部以臀大肌为主，是人体最强壮的肌肉之一，负责髋关节伸展，塑造挺翘臀型。深蹲、臀桥、箭步蹲等动作能有效刺激臀部。',
    exercises: [
      { name: '臀桥', level: '初级', equipment: '无', videoUrl: '/videos/leg-raise-new.mp4', steps: ['仰卧屈膝，双脚平放地面，与髋同宽', '收紧臀部和腹部，用臀部力量将髋部向上顶起', '在最高点收紧臀大肌，停顿 1 秒', '缓慢下放回到起始位置', '每组 15-20 次，做 3-4 组'] },
      { name: '杠铃深蹲', level: '中级', equipment: '杠铃', videoUrl: '/videos/barbell-bench-press.mp4', steps: ['双脚与肩同宽站立，杠铃置于上背部', '收紧核心，屈髋屈膝下蹲至大腿与地面平行', '膝盖与脚尖方向一致，不要内扣', '发力站起回到起始位置', '每组 8-12 次，做 3-4 组'] }
    ]
  }
}

const tabs = [
  { key: 'male', name: '男性' },
  { key: 'female', name: '女性' }
]

const activeTab = ref('male')
const currentGroup = ref('')
const loading = ref(true)

const canvasContainer = ref(null)
const canvasWrap = ref(null)

// Three.js 相关对象
let renderer = null
let scene = null
let camera = null
let controls = null
let animationId = null
let currentModel = null
let muscleMeshes = [] // 所有肌肉 mesh 的引用
let muscleGroupOfNode = new Map() // 节点名 -> 肌群 key
let originalColors = new Map() // mesh uuid -> 原始颜色
let raycaster = null
let mouse = null

const currentInfo = computed(() => {
  if (!currentGroup.value || !muscleData[currentGroup.value]) {
    return { name: '', group: '', description: '', exercises: [] }
  }
  return muscleData[currentGroup.value]
})

const switchTab = (key) => {
  activeTab.value = key
  currentGroup.value = ''
  loadModel(key)
}

const selectGroup = (key) => {
  currentGroup.value = key
  applyColors()
}

// 初始化 Three.js 场景
const initScene = () => {
  const container = canvasContainer.value
  if (!container) return

  const width = container.clientWidth || 400
  const height = container.clientHeight || 520

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x1e1e1e)

  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100)
  camera.position.set(0, 0.6, 2.8)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.outputColorSpace = THREE.SRGBColorSpace
  container.appendChild(renderer.domElement)

  const ambientLight = new THREE.AmbientLight(0xffffff, 0.7)
  scene.add(ambientLight)

  const dirLight = new THREE.DirectionalLight(0xffffff, 1.2)
  dirLight.position.set(2, 3, 3)
  scene.add(dirLight)

  const backLight = new THREE.DirectionalLight(0xffffff, 0.5)
  backLight.position.set(-1, 1, -2)
  scene.add(backLight)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.08
  controls.target.set(0, 0.6, 0)
  controls.minDistance = 1.2
  controls.maxDistance = 5
  controls.update()

  raycaster = new THREE.Raycaster()
  mouse = new THREE.Vector2()

  renderer.domElement.addEventListener('click', onCanvasClick)
  renderer.domElement.addEventListener('mousemove', onCanvasMove)
  renderer.domElement.addEventListener('mouseleave', onCanvasLeave)

  const animate = () => {
    animationId = requestAnimationFrame(animate)
    controls.update()
    renderer.render(scene, camera)
  }
  animate()

  window.addEventListener('resize', onResize)
}

const onResize = () => {
  const container = canvasContainer.value
  if (!container || !renderer || !camera) return
  const width = container.clientWidth
  const height = container.clientHeight
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

// 加载模型
const loadModel = async (sex = 'male') => {
  loading.value = true

  if (currentModel) {
    scene.remove(currentModel)
    currentModel = null
  }
  muscleMeshes = []
  muscleGroupOfNode.clear()
  originalColors.clear()

  const filename = sex === 'male' ? 'anatomy-male.glb' : 'anatomy-female.glb'
  const url = `/models/${filename}`

  try {
    const loader = new GLTFLoader()
    loader.setMeshoptDecoder(MeshoptDecoder)
    const gltf = await loader.loadAsync(url)

    currentModel = gltf.scene

    // 遍历：显示半透明皮肤 + 5 大肌群肌肉，隐藏骨骼/器官/ignore 肌肉
    currentModel.traverse((obj) => {
      if (obj.isMesh) {
        let parent = obj.parent
        let systemGroup = ''
        while (parent) {
          if (['muscles', 'skin', 'skeleton', 'organs', 'vessels', 'nerves'].includes(parent.name)) {
            systemGroup = parent.name
            break
          }
          parent = parent.parent
        }

        if (systemGroup === 'muscles') {
          // 肌肉：判断属于哪个肌群
          const group = nodeToGroup[obj.name] || 'ignore'
          if (group !== 'ignore') {
            obj.userData.isMuscle = true
            obj.userData.group = group
            muscleMeshes.push(obj)
            muscleGroupOfNode.set(obj.name, group)
            if (obj.material && obj.material.color) {
              originalColors.set(obj.uuid, obj.material.color.getHex())
            }
            obj.visible = true
          } else {
            // ignore 的肌肉（脚、手、前臂等）隐藏
            obj.visible = false
          }
        } else if (systemGroup === 'skin') {
          // 皮肤：显示为半透明，让肌肉透出来，且不遮挡点击
          obj.visible = true
          obj.userData.isSkin = true
          // 禁用皮肤参与射线检测，点击穿透到肌肉
          obj.raycast = () => {}

          // 设置半透明材质
          if (obj.material) {
            if (Array.isArray(obj.material)) {
              obj.material.forEach((m) => {
                m.transparent = true
                m.opacity = 0.85
                m.depthWrite = false
              })
            } else {
              obj.material.transparent = true
              obj.material.opacity = 0.85
              obj.material.depthWrite = false
            }
          }
        } else {
          // 骨骼、器官、血管、神经等隐藏
          obj.visible = false
        }
      }
    })

    // 调整模型位置和缩放
    const box = new THREE.Box3().setFromObject(currentModel)
    const size = box.getSize(new THREE.Vector3())
    const maxDim = Math.max(size.x, size.y, size.z)
    const scale = 1.6 / maxDim
    currentModel.scale.setScalar(scale)

    const newBox = new THREE.Box3().setFromObject(currentModel)
    const newCenter = newBox.getCenter(new THREE.Vector3())
    currentModel.position.sub(newCenter)
    currentModel.position.y += 0.6

    scene.add(currentModel)

    loading.value = false
  } catch (err) {
    console.error('模型加载失败:', err)
    loading.value = false
    alert('3D 模型加载失败，请检查网络或稍后重试。\n错误信息：' + err.message)
  }
}

// 当前悬停的肌群（用于 hover 高亮）
let hoveredGroup = null

// 鼠标移动：检测悬停的肌肉，橙色高亮提示
const onCanvasMove = (event) => {
  if (!renderer || !raycaster || !mouse) return

  const rect = renderer.domElement.getBoundingClientRect()
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1

  raycaster.setFromCamera(mouse, camera)
  const intersects = raycaster.intersectObjects(muscleMeshes, false)

  let newHover = null
  if (intersects.length > 0) {
    const hit = intersects[0].object
    const group = hit.userData.group || nodeToGroup[hit.name]
    if (group && group !== 'ignore') {
      newHover = group
    }
  }

  // 悬停变化时更新高亮
  if (newHover !== hoveredGroup) {
    hoveredGroup = newHover
    applyColors()
  }

  // 更新鼠标样式
  renderer.domElement.style.cursor = newHover ? 'pointer' : 'grab'
}

// 鼠标离开画布：清除悬停高亮
const onCanvasLeave = () => {
  hoveredGroup = null
  applyColors()
}

// 画布点击检测
const onCanvasClick = (event) => {
  if (!renderer || !raycaster || !mouse) return

  const rect = renderer.domElement.getBoundingClientRect()
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1

  raycaster.setFromCamera(mouse, camera)
  const intersects = raycaster.intersectObjects(muscleMeshes, false)

  if (intersects.length > 0) {
    const hit = intersects[0].object
    const group = hit.userData.group || nodeToGroup[hit.name]
    if (group && group !== 'ignore') {
      currentGroup.value = group
      highlightGroup(group)
    }
  }
}

// 统一颜色处理：选中肌群变红，悬停肌群变橙，其余恢复原色
const applyColors = () => {
  muscleMeshes.forEach((mesh) => {
    const g = muscleGroupOfNode.get(mesh.name) || mesh.userData.group
    const original = originalColors.get(mesh.uuid)
    if (mesh.material) {
      if (g === currentGroup.value) {
        // 选中的肌群：红色
        mesh.material.color.setHex(0xe53935)
      } else if (g === hoveredGroup) {
        // 悬停的肌群：橙色
        mesh.material.color.setHex(0xff8c00)
      } else if (original !== undefined) {
        // 其余：恢复原色
        mesh.material.color.setHex(original)
      }
    }
  })
}

// 高亮某个肌群的所有肌肉（点击时调用）
const highlightGroup = (groupKey) => {
  currentGroup.value = groupKey
  applyColors()
}

onMounted(() => {
  initScene()
  loadModel('male')
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  if (renderer && renderer.domElement) {
    renderer.domElement.removeEventListener('click', onCanvasClick)
    renderer.domElement.removeEventListener('mousemove', onCanvasMove)
    renderer.domElement.removeEventListener('mouseleave', onCanvasLeave)
  }
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  if (renderer) {
    renderer.dispose()
  }
  if (currentModel) {
    scene.remove(currentModel)
  }
})
</script>

<style scoped>
.muscle3d-container {
  padding: 24px;
  min-height: 100%;
}

.top-controls {
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.sex-tabs,
.group-tabs {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.top-controls .el-button {
  border-radius: 8px;
}
.top-controls .el-button.active {
  background-color: #ff8c00;
  border-color: #ff8c00;
  color: #fff;
}

.main-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
  flex-wrap: wrap;
}

/* 左侧 3D 模型 */
.map-section {
  flex: 1;
  min-width: 340px;
  background-color: #fff;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.canvas-wrap {
  position: relative;
  width: 100%;
  height: 560px;
  border-radius: 12px;
  overflow: hidden;
  background-color: #1e1e1e;
}

.canvas-container {
  width: 100%;
  height: 100%;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: rgba(30, 30, 30, 0.85);
  color: #fff;
  z-index: 10;
}
.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.2);
  border-top-color: #ff8c00;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 16px;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.loading-overlay p {
  font-size: 14px;
  color: #ccc;
}

.hint-bar {
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 16px;
  background-color: rgba(0, 0, 0, 0.6);
  padding: 8px 16px;
  border-radius: 20px;
  color: #fff;
  font-size: 12px;
  pointer-events: none;
  white-space: nowrap;
}

/* 右侧教程 */
.tutorial-section {
  flex: 1;
  min-width: 340px;
  background-color: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  min-height: 450px;
}
.empty-state {
  height: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
}
.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}
.muscle-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.muscle-title {
  font-size: 20px;
  color: #1a1a1a;
  margin: 0;
}
.muscle-intro {
  background: #fff4e6;
  border-left: 3px solid #ff8c00;
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 20px;
}
.muscle-intro h3 {
  font-size: 15px;
  color: #e67e00;
  margin: 0 0 8px;
}
.muscle-intro p {
  font-size: 13px;
  color: #555;
  line-height: 1.8;
  margin: 0;
}

.exercise-card {
  background-color: #fafafa;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 20px;
  border: 1px solid #f0f0f0;
}
.exercise-name {
  font-size: 16px;
  color: #1a1a1a;
  margin-bottom: 16px;
}
.video-wrapper {
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  background-color: #000;
  margin-bottom: 16px;
}
.exercise-video {
  width: 100%;
  max-height: 360px;
  display: block;
  border-radius: 8px;
}
.video-placeholder {
  width: 100%;
  height: 220px;
  border-radius: 8px;
  overflow: hidden;
  background-color: #eef2f5;
  margin-bottom: 16px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.video-placeholder .demo-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.35;
}
.video-placeholder .placeholder-text {
  position: absolute;
  color: #8899a6;
  font-size: 15px;
  font-weight: 500;
}
.exercise-details h4 {
  font-size: 14px;
  color: #e67e00;
  margin-bottom: 8px;
}
.steps-list {
  padding-left: 20px;
  color: #666;
  line-height: 1.8;
  margin-bottom: 12px;
}
.tags {
  display: flex;
  gap: 8px;
}

@media (max-width: 900px) {
  .main-layout {
    flex-direction: column;
  }
  .canvas-wrap {
    height: 440px;
  }
}
</style>
