<template>
  <div class="page">
    <!-- 个人信息卡片：头像 + 昵称 + 签名 + 联系方式 -->
    <el-card shadow="hover" class="profile-card">
      <template #header>
        <div class="card-header">
          <span><el-icon><User /></el-icon> 个人信息</span>
        </div>
      </template>
      <div class="identity-box">
        <div class="avatar-box" @click="chooseAvatar">
          <el-avatar :size="80" :src="form.avatar || undefined" class="avatar">
            {{ form.nickname ? form.nickname.charAt(0) : '健' }}
          </el-avatar>
          <div class="avatar-mask">更换头像</div>
          <input ref="avatarInput" type="file" accept="image/*" style="display:none" @change="handleAvatarChange" />
        </div>
        <div class="identity-info">
          <el-input v-model="form.nickname" placeholder="昵称" class="nickname-input" />
          <el-input v-model="form.signature" placeholder="个性签名：一句话介绍自己" class="signature-input" />
          <el-input v-model="form.contact" placeholder="联系方式：手机 / 微信 / 邮箱" class="contact-input" />
        </div>
      </div>
    </el-card>

    <!-- 我的动态 / 我的订单 入口 -->
    <el-card shadow="hover" class="profile-card">
      <template #header>
        <div class="card-header">
          <span><el-icon><Paperclip /></el-icon> 我的内容</span>
        </div>
      </template>
      <div class="content-entry">
        <div class="entry-item" @click="goCommunity">
          <div class="entry-icon" style="background:#e6f4ff;"><el-icon><ChatDotRound /></el-icon></div>
          <div class="entry-text">
            <div class="entry-title">我的动态</div>
            <div class="entry-sub">{{ myPostCount }} 条</div>
          </div>
        </div>
        <div class="entry-item" @click="goShop">
          <div class="entry-icon" style="background:#fff0e6;"><el-icon><ShoppingCart /></el-icon></div>
          <div class="entry-text">
            <div class="entry-title">我的订单</div>
            <div class="entry-sub">{{ myOrderCount }} 单</div>
          </div>
        </div>
      </div>
    </el-card>

    <el-card shadow="hover" class="profile-card">
      <template #header>
        <div class="card-header">
          <span><el-icon><User /></el-icon> 身体数据</span>
        </div>
      </template>

      <el-form :model="form" label-width="100px" class="profile-form">
        <el-form-item label="性别">
          <el-radio-group v-model="form.gender">
            <el-radio value="male">男</el-radio>
            <el-radio value="female">女</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="年龄">
          <el-input-number v-model="form.age" :min="10" :max="100" :step="1" />
          <span class="unit">岁</span>
        </el-form-item>

        <el-form-item label="身高">
          <el-input-number v-model="form.height_cm" :min="100" :max="250" :step="1" />
          <span class="unit">cm</span>
        </el-form-item>

        <el-form-item label="体重">
          <el-input-number v-model="form.weight_kg" :min="30" :max="300" :step="0.5" :precision="1" />
          <span class="unit">kg</span>
        </el-form-item>

        <el-form-item label="活动水平">
          <el-select v-model="form.activity_level" style="width: 240px;">
            <el-option label="久坐（几乎不运动）" value="sedentary" />
            <el-option label="轻度（每周1-3次）" value="light" />
            <el-option label="中度（每周3-5次）" value="moderate" />
            <el-option label="高强度（每周6-7次）" value="active" />
            <el-option label="极高（体力劳动/专业训练）" value="very_active" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="budget" shadow="hover" class="budget-card">
      <template #header>
        <div class="card-header">
          <span><el-icon><TrendCharts /></el-icon> 每日热量预算</span>
        </div>
      </template>
      <div class="budget-content">
        <div class="budget-item main">
          <span class="label">每日应摄入</span>
          <span class="value">{{ budget.daily_budget }} <i>kcal</i></span>
        </div>
        <div class="budget-row">
          <div class="budget-item">
            <span class="label">今日已摄入</span>
            <span class="value food">{{ budget.food_calorie }} <i>kcal</i></span>
          </div>
          <div class="budget-item">
            <span class="label">今日运动消耗</span>
            <span class="value burn">{{ budget.exercise_burn }} <i>kcal</i></span>
          </div>
          <div class="budget-item">
            <span class="label">还可摄入</span>
            <span class="value remain" :class="{ negative: budget.remaining < 0 }">
              {{ budget.remaining }} <i>kcal</i>
            </span>
          </div>
        </div>
      </div>
    </el-card>
    <el-card shadow="hover" class="exercise-card">
      <template #header>
        <div class="card-header">
          <span><el-icon><Bicycle /></el-icon> 今日运动记录</span>
        </div>
      </template>

      <!-- 录入区 -->
      <div class="exercise-form">
        <el-select v-model="exerciseForm.exercise_type" placeholder="选择运动类型" filterable style="width: 180px;">
          <el-option v-for="t in exerciseTypes" :key="t" :label="t" :value="t" />
        </el-select>
        <el-input-number v-model="exerciseForm.duration_min" :min="1" :max="600" :step="5" />
        <span class="unit">分钟</span>
        <el-button type="primary" :loading="addingExercise" @click="addExercise">
          记录
        </el-button>
      </div>

      <!-- 今日运动列表 -->
      <div v-if="exercises.length === 0" class="empty-exercise">
        <el-empty description="今天还没有运动记录" :image-size="60" />
      </div>
      <div v-else class="exercise-list">
        <div v-for="e in exercises" :key="e.id" class="exercise-item">
          <div class="ex-left">
            <span class="ex-type">{{ e.exercise_type }}</span>
            <span class="ex-time">{{ e.duration_min }} 分钟</span>
          </div>
          <div class="ex-right">
            <span class="ex-burn">-{{ e.calorie_burn }} kcal</span>
            <el-button text type="danger" size="small" :icon="Delete" @click="removeExercise(e.id)" />
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, TrendCharts, Bicycle, Delete, Paperclip, ChatDotRound, ShoppingCart } from '@element-plus/icons-vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { API_BASE } from '../config'

const router = useRouter()

const saving = ref(false)
const budget = ref(null)

// 我的动态/订单数量
const myPostCount = ref(0)
const myOrderCount = ref(0)

// 运动记录
const addingExercise = ref(false)
const exerciseTypes = ref([])
const exercises = ref([])
const exerciseForm = reactive({
  exercise_type: '',
  duration_min: 30,
})

const form = reactive({
  nickname: '健身达人',
  avatar: '',
  signature: '',
  contact: '',
  gender: 'male',
  age: 25,
  height_cm: 170,
  weight_kg: 65,
  activity_level: 'light',
})

const avatarInput = ref(null)
const uploadingAvatar = ref(false)

function chooseAvatar() {
  avatarInput.value.click()
}

async function handleAvatarChange(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  uploadingAvatar.value = true
  const fd = new FormData()
  fd.append('file', file)
  try {
    const res = await axios.post(`${API_BASE}/api/profile/avatar`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    if (res.data.success) {
      form.avatar = res.data.url
      ElMessage.success('头像已更新，记得保存')
    }
  } catch (err) {
    ElMessage.error('头像上传失败')
  } finally {
    uploadingAvatar.value = false
    e.target.value = ''
  }
}

async function load() {
  try {
    const res = await axios.get(`${API_BASE}/api/profile`)
    if (res.data.success && res.data.data) {
      Object.assign(form, res.data.data)
    }
    await refreshBudget()
    await loadExerciseTypes()
    await loadExercises()
    await loadMyCounts()
  } catch (e) {
    console.error('加载个人资料失败:', e)
  }
}

async function loadMyCounts() {
  try {
    const [posts, orders] = await Promise.all([
      axios.get(`${API_BASE}/api/posts`, { params: { user_id: 1, mine: 1 } }),
      axios.get(`${API_BASE}/api/orders`, { params: { user_id: 1 } }),
    ])
    myPostCount.value = posts.data.length
    myOrderCount.value = orders.data.data ? orders.data.data.length : 0
  } catch (e) {
    console.error('加载我的内容统计失败:', e)
  }
}

function goCommunity() {
  router.push('/community')
}

function goShop() {
  router.push('/shop?show=orders')
}

async function refreshBudget() {
  try {
    const b = await axios.get(`${API_BASE}/api/budget`)
    if (b.data.success && b.data.data.has_profile) {
      budget.value = b.data.data
    }
  } catch (e) {
    console.error('加载预算失败:', e)
  }
}

async function loadExerciseTypes() {
  try {
    const res = await axios.get(`${API_BASE}/api/exercise/types`)
    if (res.data.success) exerciseTypes.value = res.data.data
  } catch (e) {
    console.error('加载运动类型失败:', e)
  }
}

async function loadExercises() {
  try {
    const res = await axios.get(`${API_BASE}/api/exercise`)
    if (res.data.success) exercises.value = res.data.data
  } catch (e) {
    console.error('加载运动记录失败:', e)
  }
}

async function addExercise() {
  if (!exerciseForm.exercise_type) {
    ElMessage.warning('请选择运动类型')
    return
  }
  addingExercise.value = true
  try {
    const res = await axios.post(`${API_BASE}/api/exercise`, {
      exercise_type: exerciseForm.exercise_type,
      duration_min: exerciseForm.duration_min,
    })
    if (res.data.success) {
      ElMessage.success(`已记录：${res.data.data.exercise_type}，消耗 ${res.data.data.calorie_burn} kcal`)
      exerciseForm.exercise_type = ''
      exerciseForm.duration_min = 30
      await loadExercises()
      await refreshBudget()
    }
  } catch (e) {
    ElMessage.error('记录失败：' + (e.response?.data?.error || e.message))
  } finally {
    addingExercise.value = false
  }
}

async function removeExercise(id) {
  try {
    await ElMessageBox.confirm('确定删除这条运动记录吗？', '确认删除', { type: 'warning' })
    await axios.delete(`${API_BASE}/api/exercise/${id}`)
    ElMessage.success('已删除')
    await loadExercises()
    await refreshBudget()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

async function save() {
  saving.value = true
  try {
    const res = await axios.post(`${API_BASE}/api/profile`, form)
    if (res.data.success) {
      ElMessage.success('保存成功')
      // 同步昵称到 localStorage，社区/顶栏立即生效
      if (form.nickname) localStorage.setItem('username', form.nickname)
      await refreshBudget()
    }
  } catch (e) {
    ElMessage.error('保存失败：' + (e.response?.data?.error || e.message))
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page { padding: 20px; max-width: 900px; margin: 0 auto; }
.profile-card { margin-bottom: 20px; }
.card-header { display: flex; align-items: center; gap: 6px; font-weight: 600; font-size: 15px; }
.profile-form { max-width: 480px; }
.unit { margin-left: 8px; color: #909399; font-size: 13px; }

.identity-box { display: flex; gap: 24px; align-items: flex-start; }
.avatar-box { position: relative; cursor: pointer; flex-shrink: 0; }
.avatar-box .avatar { background: #ff8c00; color: #fff; font-size: 30px; font-weight: 600; }
.avatar-mask {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.2s;
}
.avatar-box:hover .avatar-mask { opacity: 1; }
.identity-info { flex: 1; display: flex; flex-direction: column; gap: 12px; }
.nickname-input :deep(.el-input__inner) { font-size: 18px; font-weight: 600; }
.signature-input :deep(.el-input__inner) { color: #606266; }
.contact-input :deep(.el-input__inner) { color: #606266; }

.content-entry { display: flex; gap: 16px; }
.entry-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  cursor: pointer;
  transition: all 0.2s;
}
.entry-item:hover {
  border-color: #ff8c00;
  box-shadow: 0 2px 8px #00000012;
}
.entry-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #ff8c00;
}
.entry-title { font-size: 15px; font-weight: 600; color: #303133; }
.entry-sub { font-size: 12px; color: #909399; margin-top: 2px; }

.budget-content { text-align: center; }
.budget-item.main { margin-bottom: 20px; }
.budget-item .label { display: block; font-size: 13px; color: #909399; margin-bottom: 6px; }
.budget-item.main .value { font-size: 40px; font-weight: 700; color: #ff8c00; }
.budget-item .value i { font-size: 14px; font-style: normal; color: #909399; }
.budget-row { display: flex; justify-content: space-around; }
.budget-row .value { font-size: 24px; font-weight: 700; }
.budget-row .value.food { color: #FF6B6B; }
.budget-row .value.burn { color: #67C23A; }
.budget-row .value.remain { color: #E6A23C; }
.budget-row .value.remain.negative { color: #F56C6C; }

.exercise-card { margin-bottom: 20px; }
.exercise-form { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.empty-exercise { padding: 10px 0; }
.exercise-list { max-height: 320px; overflow-y: auto; }
.exercise-item { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
.exercise-item:last-child { border-bottom: none; }
.ex-left { display: flex; align-items: center; gap: 10px; }
.ex-type { font-size: 14px; font-weight: 600; color: #303133; }
.ex-time { font-size: 13px; color: #909399; }
.ex-right { display: flex; align-items: center; gap: 8px; }
.ex-burn { font-size: 14px; font-weight: 600; color: #67C23A; }
</style>
