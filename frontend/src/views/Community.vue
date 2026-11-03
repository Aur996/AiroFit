<template>
  <div class="community-page">
    <!-- 发布模块 -->
    <div class="publish-card">
      <h3>分享健身动态</h3>
      <el-input
        v-model="content"
        type="textarea"
        :rows="3"
        placeholder="分享你的训练、饮食、心得..."
        class="text-area"
      />

      <!-- 图片预览区 -->
      <div class="img-preview" v-if="previewList.length">
        <div class="preview-item" v-for="(img, i) in previewList" :key="i">
          <img :src="img" alt="预览" />
          <span class="del" @click="delImg(i)">×</span>
        </div>
      </div>

      <!-- 上传 + 发布 -->
      <div class="btn-group">
        <el-button type="primary" plain @click="chooseImg">
          {{ previewList.length > 0 ? `已选 ${previewList.length} 张` : '添加图片' }}
        </el-button>
        <el-button type="primary" @click="publish" :loading="loading">
          发布动态
        </el-button>
      </div>

      <input
        ref="fileInput"
        type="file"
        multiple
        accept="image/*"
        style="display: none"
        @change="handleImgChange"
      />
    </div>

    <!-- 动态列表 -->
    <div class="post-list">
      <div class="post-item" v-for="item in postList" :key="item.id">
        <!-- 头部：头像 + 用户名 + 时间 -->
        <div class="post-header">
          <el-avatar :size="36" class="avatar">{{ item.username.charAt(0) }}</el-avatar>
          <div class="post-meta">
            <span class="username">{{ item.username }}</span>
            <span class="time">{{ friendlyTime(item.time) }}</span>
          </div>
          <el-button
            v-if="item.user_id === currentUserId"
            text
            type="danger"
            size="small"
            :icon="Delete"
            class="del-post"
            @click="removePost(item.id)"
          />
        </div>

        <div class="content">{{ item.content }}</div>

        <div class="img-list" v-if="item.image_urls.length">
          <img
            v-for="(img, i) in item.image_urls"
            :key="i"
            :src="img"
            alt="动态图片"
            @click="previewImage(img)"
          />
        </div>

        <!-- 操作栏：点赞 + 评论 -->
        <div class="post-actions">
          <span class="action-btn" :class="{ active: item.liked }" @click="toggleLike(item)">
            <el-icon><component :is="item.liked ? 'StarFilled' : 'Star'" /></el-icon>
            {{ item.like_count || '点赞' }}
          </span>
          <span class="action-btn" @click="toggleComment(item)">
            <el-icon><ChatDotRound /></el-icon>
            {{ item.comment_count || '评论' }}
          </span>
        </div>

        <!-- 评论区 -->
        <div v-if="item.showComment" class="comment-section">
          <div class="comment-list" v-if="item.comments && item.comments.length">
            <div class="comment-item" v-for="c in item.comments" :key="c.id">
              <span class="comment-user">{{ c.username }}：</span>
              <span class="comment-content">{{ c.content }}</span>
              <span class="comment-time">{{ friendlyTime(c.created_at) }}</span>
              <el-button
                v-if="c.user_id === currentUserId"
                text
                type="danger"
                size="small"
                :icon="Delete"
                @click="removeComment(item, c.id)"
              />
            </div>
          </div>
          <div v-else class="no-comment">还没有评论，快来抢沙发～</div>

          <div class="comment-input">
            <el-input
              v-model="item.commentText"
              placeholder="写下你的评论..."
              size="small"
              @keyup.enter="submitComment(item)"
            />
            <el-button type="primary" size="small" @click="submitComment(item)">发送</el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 图片放大预览 -->
    <el-dialog v-model="imagePreviewVisible" title="图片预览" width="70%" :show-close="true">
      <img :src="imagePreviewUrl" style="width: 100%;" alt="预览" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, ChatDotRound, Star, StarFilled } from '@element-plus/icons-vue'
import { API_BASE } from '../config'

// 接口地址
const api = axios.create({ baseURL: API_BASE + '/api' })

// 当前用户（从 localStorage 读取，登录时写入）
const currentUserId = ref(1)
const currentUsername = ref(localStorage.getItem('username') || '匿名用户')

// 数据
const content = ref('')
const fileList = ref([])
const previewList = ref([])
const postList = ref([])
const loading = ref(false)
const fileInput = ref(null)

// 图片预览
const imagePreviewVisible = ref(false)
const imagePreviewUrl = ref('')

// 选择图片
const chooseImg = () => fileInput.value.click()

// 图片预览
const handleImgChange = (e) => {
  const files = e.target.files
  if (!files) return
  for (let f of files) {
    fileList.value.push(f)
    const reader = new FileReader()
    reader.onload = (ev) => previewList.value.push(ev.target.result)
    reader.readAsDataURL(f)
  }
}

// 删除预览图
const delImg = (idx) => {
  fileList.value.splice(idx, 1)
  previewList.value.splice(idx, 1)
}

// 友好时间
function friendlyTime(timeStr) {
  if (!timeStr) return ''
  const t = new Date(timeStr.replace(' ', 'T'))
  const now = new Date()
  const diff = Math.floor((now - t) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  if (diff < 86400 * 7) return `${Math.floor(diff / 86400)}天前`
  return timeStr.slice(0, 10)
}

// 发布动态
const publish = async () => {
  if (!content.value.trim()) return ElMessage.warning('请输入内容')
  loading.value = true

  const form = new FormData()
  form.append('content', content.value)
  form.append('user_id', currentUserId.value)
  form.append('username', currentUsername.value)
  fileList.value.forEach(f => form.append('images', f))

  try {
    await api.post('/posts', form, { headers: { 'Content-Type': 'multipart/form-data' } })
    ElMessage.success('发布成功')
    content.value = ''
    fileList.value = []
    previewList.value = []
    loadPosts()
  } catch (err) {
    ElMessage.error('发布失败')
    console.error(err)
  } finally {
    loading.value = false
  }
}

// 加载动态列表
const loadPosts = async () => {
  try {
    const res = await api.get('/posts', { params: { user_id: currentUserId.value } })
    postList.value = res.data.map(p => ({
      ...p,
      showComment: false,
      comments: [],
      commentText: '',
    }))
  } catch (err) {
    console.error('加载失败', err)
  }
}

// 点赞/取消点赞
const toggleLike = async (item) => {
  try {
    const res = await api.post(`/posts/${item.id}/like`, { user_id: currentUserId.value })
    if (res.data.success) {
      item.liked = res.data.liked
      item.like_count = res.data.like_count
    }
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

// 展开/收起评论
const toggleComment = async (item) => {
  item.showComment = !item.showComment
  if (item.showComment && item.comments.length === 0) {
    await loadComments(item)
  }
}

// 加载评论
const loadComments = async (item) => {
  try {
    const res = await api.get(`/posts/${item.id}/comments`)
    item.comments = res.data
  } catch (err) {
    console.error('加载评论失败', err)
  }
}

// 发表评论
const submitComment = async (item) => {
  const text = (item.commentText || '').trim()
  if (!text) return ElMessage.warning('请输入评论内容')
  try {
    await api.post(`/posts/${item.id}/comments`, {
      content: text,
      user_id: currentUserId.value,
      username: currentUsername.value,
    })
    item.commentText = ''
    item.comment_count = (item.comment_count || 0) + 1
    await loadComments(item)
  } catch (err) {
    ElMessage.error('评论失败')
  }
}

// 删除评论
const removeComment = async (item, commentId) => {
  try {
    await ElMessageBox.confirm('确定删除这条评论吗？', '确认删除', { type: 'warning' })
    await api.delete(`/comments/${commentId}`)
    item.comment_count = Math.max(0, (item.comment_count || 0) - 1)
    await loadComments(item)
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

// 删除动态
const removePost = async (postId) => {
  try {
    await ElMessageBox.confirm('确定删除这条动态吗？', '确认删除', { type: 'warning' })
    await api.delete(`/posts/${postId}`)
    ElMessage.success('已删除')
    loadPosts()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

// 图片放大预览
const previewImage = (url) => {
  imagePreviewUrl.value = url
  imagePreviewVisible.value = true
}

onMounted(() => loadPosts())
</script>

<style scoped>
.community-page {
  padding: 20px;
  background: #f0f9f4;
  min-height: 100vh;
}

.publish-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 1px 5px #00000010;
}

.publish-card h3 {
  margin: 0 0 12px 0;
  color: #ff8c00;
  font-size: 16px;
}

.text-area {
  margin-bottom: 12px;
}

.img-preview {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.preview-item {
  position: relative;
  width: 80px;
  height: 80px;
}

.preview-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 6px;
}

.del {
  position: absolute;
  top: -6px;
  right: -6px;
  background: #ff4444;
  color: #fff;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  cursor: pointer;
}

.btn-group {
  display: flex;
  gap: 10px;
}

.post-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.post-item {
  background: #fff;
  padding: 16px 20px;
  border-radius: 12px;
  box-shadow: 0 1px 5px #00000010;
}

.post-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  position: relative;
}

.avatar {
  background: #ff8c00;
  color: #fff;
  font-weight: 600;
}

.post-meta {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.username {
  font-size: 14px;
  font-weight: 600;
  color: #ff8c00;
}

.time {
  font-size: 12px;
  color: #999;
}

.del-post {
  position: absolute;
  right: 0;
  top: 0;
}

.post-item .content {
  margin-bottom: 10px;
  color: #333;
  line-height: 1.6;
}

.img-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.img-list img {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 6px;
  cursor: pointer;
  transition: transform 0.2s;
}

.img-list img:hover {
  transform: scale(1.05);
}

.post-actions {
  display: flex;
  gap: 24px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  user-select: none;
}

.action-btn:hover {
  color: #ff8c00;
}

.action-btn.active {
  color: #f56c6c;
}

.comment-section {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;
}

.comment-list {
  margin-bottom: 10px;
}

.comment-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  padding: 4px 0;
}

.comment-user {
  color: #ff8c00;
  font-weight: 600;
  white-space: nowrap;
}

.comment-content {
  color: #333;
  flex: 1;
}

.comment-time {
  font-size: 11px;
  color: #bbb;
  white-space: nowrap;
}

.no-comment {
  font-size: 13px;
  color: #bbb;
  text-align: center;
  padding: 10px 0;
}

.comment-input {
  display: flex;
  gap: 8px;
}
</style>
