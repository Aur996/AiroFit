<template>
  <div class="shop-page">
    <!-- 顶部工具栏 -->
    <div class="shop-toolbar">
      <div class="category-tabs">
        <el-button
          :type="activeCategory === 'all' ? 'primary' : 'default'"
          size="small"
          @click="changeCategory('all')"
        >全部</el-button>
        <el-button
          v-for="cat in categories"
          :key="cat"
          :type="activeCategory === cat ? 'primary' : 'default'"
          size="small"
          @click="changeCategory(cat)"
        >{{ cat }}</el-button>
      </div>
      <div class="toolbar-right">
        <el-input
          v-model="keyword"
          placeholder="搜索商品..."
          size="small"
          clearable
          style="width: 200px;"
          @keyup.enter="loadProducts"
          @clear="loadProducts"
        >
          <template #append>
            <el-button :icon="Search" @click="loadProducts" />
          </template>
        </el-input>
        <el-badge :value="cartCount" :hidden="cartCount === 0" class="cart-badge">
          <el-button type="warning" :icon="ShoppingCart" @click="showCart = true">
            购物车
          </el-button>
        </el-badge>
        <el-button :icon="List" @click="openOrders">我的订单</el-button>
      </div>
    </div>

    <!-- 商品列表 -->
    <div v-if="loading" class="loading-box">
      <el-skeleton :rows="3" animated />
    </div>
    <div v-else class="product-grid">
      <div class="product-card" v-for="p in products" :key="p.id">
        <div class="product-img">
          <img v-if="p.image" :src="p.image" :alt="p.name" class="product-pic" />
          <span v-else class="emoji">{{ categoryEmoji(p.category) }}</span>
          <span class="badge" v-if="p.original_price > p.price">特惠</span>
        </div>
        <div class="product-info">
          <div class="product-name">{{ p.name }}</div>
          <div class="product-desc">{{ p.description }}</div>
          <div class="product-meta">
            <span class="price">¥{{ p.price }}</span>
            <span class="original" v-if="p.original_price > p.price">¥{{ p.original_price }}</span>
            <span class="sales">已售 {{ p.sales }}</span>
          </div>
          <div class="product-actions">
            <el-button type="primary" size="small" :icon="ShoppingCart" @click="addToCart(p)">
              加入购物车
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty v-if="!loading && products.length === 0" description="暂无商品" />

    <!-- 购物车抽屉 -->
    <el-drawer v-model="showCart" title="购物车" size="420px">
      <div v-if="cart.length === 0" class="empty-cart">
        <el-empty description="购物车还是空的" :image-size="80" />
      </div>
      <div v-else>
        <div class="cart-item" v-for="(item, i) in cart" :key="i">
          <div class="cart-item-info">
            <div class="cart-item-name">{{ item.name }}</div>
            <div class="cart-item-price">¥{{ item.price }} × {{ item.quantity }}</div>
          </div>
          <el-input-number
            v-model="item.quantity"
            :min="1"
            :max="99"
            size="small"
            @change="saveCart"
          />
          <el-button text type="danger" size="small" :icon="Delete" @click="removeFromCart(i)" />
        </div>
        <div class="cart-footer">
          <div class="cart-total">
            合计：<span class="total-price">¥{{ cartTotal }}</span>
          </div>
          <el-button type="primary" :loading="ordering" @click="submitOrder">
            提交订单
          </el-button>
        </div>
      </div>
    </el-drawer>
    <!-- 我的订单抽屉 -->
    <el-drawer v-model="showOrders" title="我的订单" size="500px">
      <div v-if="orders.length === 0" class="empty-cart">
        <el-empty description="还没有订单" :image-size="80" />
      </div>
      <div v-else class="order-list">
        <div class="order-item" v-for="o in orders" :key="o.id">
          <div class="order-header">
            <span class="order-id">订单号：{{ o.id }}</span>
            <el-tag :type="o.status === '待发货' ? 'warning' : 'success'" size="small">{{ o.status }}</el-tag>
          </div>
          <div class="order-items">
            <div class="order-line" v-for="(it, i) in o.items" :key="i">
              <span class="order-name">{{ it.name }}</span>
              <span class="order-qty">× {{ it.quantity }}</span>
              <span class="order-price">¥{{ (it.price * it.quantity).toFixed(2) }}</span>
            </div>
          </div>
          <div class="order-footer">
            <span class="order-time">{{ o.created_at }}</span>
            <span class="order-total">合计：<b>¥{{ o.total_price }}</b></span>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { ShoppingCart, Search, Delete, List } from '@element-plus/icons-vue'
import { useRoute } from 'vue-router'
import { API_BASE } from '../config'

const route = useRoute()

const products = ref([])
const categories = ref([])
const activeCategory = ref('all')
const keyword = ref('')
const loading = ref(false)

const cart = ref([])
const showCart = ref(false)
const ordering = ref(false)

const orders = ref([])
const showOrders = ref(false)

const cartCount = computed(() => cart.value.reduce((s, i) => s + i.quantity, 0))
const cartTotal = computed(() => cart.value.reduce((s, i) => s + i.price * i.quantity, 0).toFixed(2))

const categoryEmoji = (cat) => {
  const map = { '器材': '🏋️', '补剂': '💊', '服饰': '👕' }
  return map[cat] || '🛒'
}

async function loadProducts() {
  loading.value = true
  try {
    const res = await axios.get(`${API_BASE}/api/products`, {
      params: { category: activeCategory.value, keyword: keyword.value }
    })
    if (res.data.success) products.value = res.data.data
  } catch (e) {
    ElMessage.error('加载商品失败')
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  try {
    const res = await axios.get(`${API_BASE}/api/products/categories`)
    if (res.data.success) categories.value = res.data.data
  } catch (e) {
    console.error('加载分类失败', e)
  }
}

function changeCategory(cat) {
  activeCategory.value = cat
  loadProducts()
}

function addToCart(p) {
  const existing = cart.value.find(i => i.id === p.id)
  if (existing) {
    existing.quantity++
  } else {
    cart.value.push({ id: p.id, name: p.name, price: p.price, quantity: 1 })
  }
  saveCart()
  ElMessage.success('已加入购物车')
}

function removeFromCart(idx) {
  cart.value.splice(idx, 1)
  saveCart()
}

function saveCart() {
  localStorage.setItem('shop_cart', JSON.stringify(cart.value))
}

function loadCart() {
  try {
    cart.value = JSON.parse(localStorage.getItem('shop_cart') || '[]')
  } catch (e) {
    cart.value = []
  }
}

async function submitOrder() {
  if (cart.value.length === 0) return ElMessage.warning('购物车为空')
  ordering.value = true
  try {
    const res = await axios.post(`${API_BASE}/api/orders`, {
      user_id: 1,
      items: cart.value.map(i => ({ id: i.id, name: i.name, price: i.price, quantity: i.quantity }))
    })
    if (res.data.success) {
      ElMessage.success(`下单成功！订单号 ${res.data.data.order_id}，共 ¥${res.data.data.total_price}`)
      cart.value = []
      saveCart()
      showCart.value = false
    }
  } catch (e) {
    ElMessage.error('下单失败')
  } finally {
    ordering.value = false
  }
}

async function openOrders() {
  showOrders.value = true
  try {
    const res = await axios.get(`${API_BASE}/api/orders`, { params: { user_id: 1 } })
    if (res.data.success) orders.value = res.data.data
  } catch (e) {
    ElMessage.error('加载订单失败')
  }
}

onMounted(() => {
  loadCart()
  loadCategories()
  loadProducts()
  // 从个人中心跳转过来，自动打开订单抽屉
  if (route.query.show === 'orders') {
    openOrders()
  }
})
</script>

<style scoped>
.shop-page { padding: 0; }

.shop-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.category-tabs { display: flex; gap: 8px; flex-wrap: wrap; }

.toolbar-right { display: flex; align-items: center; gap: 12px; }

.cart-badge { display: inline-flex; }

.loading-box { padding: 40px 0; }

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.product-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 5px #00000010;
  transition: transform 0.2s, box-shadow 0.2s;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 16px #00000018;
}

.product-img {
  height: 160px;
  background: linear-gradient(135deg, #f0f9f4, #e8f5ee);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.product-img .product-pic {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-img .emoji { font-size: 64px; }

.product-img .badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background: #ff6b6b;
  color: #fff;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
}

.product-info { padding: 14px; }

.product-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
}

.product-desc {
  font-size: 12px;
  color: #909399;
  margin-bottom: 10px;
  line-height: 1.5;
  height: 36px;
  overflow: hidden;
}

.product-meta {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 10px;
}

.price { font-size: 18px; font-weight: 700; color: #ff6b6b; }

.original { font-size: 13px; color: #bbb; text-decoration: line-through; }

.sales { font-size: 12px; color: #999; margin-left: auto; }

.product-actions { display: flex; }

.empty-cart { padding: 40px 0; }

.cart-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.cart-item-info { flex: 1; }

.cart-item-name { font-size: 14px; font-weight: 600; color: #303133; }

.cart-item-price { font-size: 13px; color: #ff6b6b; margin-top: 4px; }

.cart-footer {
  position: sticky;
  bottom: 0;
  background: #fff;
  padding: 16px 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid #f0f0f0;
}

.cart-total { font-size: 14px; color: #666; }

.total-price { font-size: 20px; font-weight: 700; color: #ff6b6b; }

.order-list { display: flex; flex-direction: column; gap: 14px; }
.order-item { border: 1px solid #f0f0f0; border-radius: 10px; padding: 14px; }
.order-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.order-id { font-size: 13px; color: #666; font-weight: 600; }
.order-items { margin-bottom: 10px; }
.order-line { display: flex; align-items: center; gap: 8px; padding: 4px 0; font-size: 13px; }
.order-name { flex: 1; color: #303133; }
.order-qty { color: #909399; }
.order-price { color: #ff6b6b; font-weight: 600; }
.order-footer { display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #f0f0f0; padding-top: 10px; }
.order-time { font-size: 12px; color: #bbb; }
.order-total { font-size: 14px; color: #303133; }
.order-total b { color: #ff6b6b; font-size: 16px; }
</style>
