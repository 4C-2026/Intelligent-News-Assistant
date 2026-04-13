<template>
  <div class="login-page">
    <div class="login-bg">
      <div class="aurora" aria-hidden="true"></div>
      <div class="floating-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
      </div>
    </div>
    <div class="login-container">
      <div class="login-card" @mouseenter="handleMouseEnter" @mouseleave="handleMouseLeave">
        <div class="particles-container" ref="particlesContainer"></div>
        <div class="login-content">
          <div class="login-header">
          <h1>📰</h1>
          <h2>新语</h2>
          <p>智能新闻助手</p>
        </div>

        <el-tabs v-model="activeTab" class="login-tabs" stretch>
          <el-tab-pane label="登录" name="login">
            <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" label-width="0">
              <el-form-item prop="username">
                <el-input
                  v-model="loginForm.username"
                  prefix-icon="User"
                  placeholder="请输入用户名"
                  size="large"
                />
              </el-form-item>
              <el-form-item prop="password">
                <el-input
                  v-model="loginForm.password"
                  prefix-icon="Lock"
                  type="password"
                  placeholder="请输入密码"
                  size="large"
                  show-password
                  @keyup.enter="handleLogin"
                />
              </el-form-item>
              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  class="login-btn"
                  :loading="loading"
                  @click="handleLogin"
                >
                  登 录
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="注册" name="register">
            <el-form ref="registerFormRef" :model="registerForm" :rules="registerRules" label-width="0">
              <el-form-item prop="username">
                <el-input
                  v-model="registerForm.username"
                  prefix-icon="User"
                  placeholder="请输入用户名"
                  size="large"
                />
              </el-form-item>
              <el-form-item prop="password">
                <el-input
                  v-model="registerForm.password"
                  prefix-icon="Lock"
                  type="password"
                  placeholder="请输入密码"
                  size="large"
                  show-password
                />
              </el-form-item>
              <el-form-item prop="confirmPassword">
                <el-input
                  v-model="registerForm.confirmPassword"
                  prefix-icon="Lock"
                  type="password"
                  placeholder="请确认密码"
                  size="large"
                  show-password
                  @keyup.enter="handleRegister"
                />
              </el-form-item>
              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  class="login-btn"
                  :loading="loading"
                  @click="handleRegister"
                >
                  注 册
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { userApi } from '../api/index.js'

const router = useRouter()
const activeTab = ref('login')
const loading = ref(false)
const loginFormRef = ref(null)
const registerFormRef = ref(null)

// 粒子交互效果
const particlesContainer = ref(null)
let particleInterval = null

const createEdgeParticle = () => {
  if (!particlesContainer.value) return
  
  const rect = particlesContainer.value.getBoundingClientRect()
  const w = rect.width
  const h = rect.height
  
  // 沿边缘生成
  const perimeter = 2 * (w + h)
  const p = Math.random() * perimeter
  
  let x, y
  // 内缩一点，使得粒子从卡片后方边缘飘出来更加自然
  const offset = 8 
  
  if (p < w) { // 上边缘
    x = p
    y = offset
  } else if (p < w + h) { // 右边缘
    x = w - offset
    y = p - w
  } else if (p < 2 * w + h) { // 下边缘
    x = 2 * w + h - p
    y = h - offset
  } else { // 左边缘
    x = offset
    y = 2 * (w + h) - p
  }

  const particle = document.createElement('div')
  particle.className = 'interaction-particle'
  
  // 高级轻量感：小尺寸，带有色彩的柔和发光
  const size = Math.random() * 2.5 + 1.5 // 1.5px - 4px
  const colors = [
    'rgba(59, 130, 246, 0.9)',   // blue-500
    'rgba(139, 92, 246, 0.9)',   // violet-500
    'rgba(14, 165, 233, 0.9)',   // sky-500
    'rgba(255, 255, 255, 0.9)'   // white
  ]
  const color = colors[Math.floor(Math.random() * colors.length)]
  
  particle.style.width = `${size}px`
  particle.style.height = `${size}px`
  particle.style.background = color
  particle.style.boxShadow = `0 0 ${size * 2}px ${color}`
  particle.style.left = `${x}px`
  particle.style.top = `${y}px`
  
  // 缓慢向外和向上飘散
  const centerX = w / 2
  const centerY = h / 2
  const dirX = (x - centerX) / centerX
  const dirY = (y - centerY) / centerY
  
  const distance = Math.random() * 45 + 25 // 飘散距离
  const tx = dirX * distance + (Math.random() - 0.5) * 15
  const ty = dirY * distance - Math.random() * 20
  
  particle.style.setProperty('--tx', `${tx}px`)
  particle.style.setProperty('--ty', `${ty}px`)
  
  const duration = Math.random() * 1.5 + 2 // 2s - 3.5s
  particle.style.animationDuration = `${duration}s`
  
  particlesContainer.value.appendChild(particle)
  
  setTimeout(() => {
    if (particlesContainer.value?.contains(particle)) {
      particlesContainer.value.removeChild(particle)
    }
  }, duration * 1000)
}

const handleMouseEnter = () => {
  if (particleInterval) clearInterval(particleInterval)
  
  // 初始散发一批
  for(let i = 0; i < 18; i++) {
    setTimeout(createEdgeParticle, Math.random() * 400)
  }
  
  // 持续生成，进一步增加粒子密度
  particleInterval = setInterval(() => {
    // 每次生成 3 个，一定概率生成第 4 个
    createEdgeParticle()
    createEdgeParticle()
    createEdgeParticle()
    if(Math.random() > 0.3) createEdgeParticle()
  }, 150) // 再次加快生成频率
}

const handleMouseLeave = () => {
  if (particleInterval) {
    clearInterval(particleInterval)
    particleInterval = null
  }
}

const loginForm = reactive({
  username: '',
  password: ''
})

const registerForm = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  const valid = await loginFormRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await userApi.login({
      username: loginForm.username,
      password: loginForm.password
    })
    // 后端返回：{ code, message, data: { access_token, token_type, user_id, username } }
    if (res?.code !== 0) {
      throw new Error(res?.message || '登录失败')
    }
    const token = res?.data?.access_token
    if (!token) {
      throw new Error('登录失败：未获取到 access_token')
    }
    localStorage.setItem('token', token)
    localStorage.setItem('username', res?.data?.username || loginForm.username)
    ElMessage.success('登录成功！')
    router.push('/')
  } catch (error) {
    // 真实联调模式：不要模拟成功，直接提示后端错误
    const backendMsg =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error?.message ||
      '登录失败'
    ElMessage.error(backendMsg)
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  const valid = await registerFormRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await userApi.register({
      username: registerForm.username,
      password: registerForm.password
    })
    if (res?.code !== 0) {
      throw new Error(res?.message || '注册失败')
    }
    ElMessage.success('注册成功，请登录！')
    activeTab.value = 'login'
    loginForm.username = registerForm.username
  } catch (error) {
    const backendMsg =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error?.message ||
      '注册失败'
    ElMessage.error(backendMsg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background-color: transparent; /* Let global animated background show through */
}

/* Remove static local background to use the new global animated one */
.login-bg {
  display: none;
}

/* Enhance local shapes for Login specific flair */
.floating-shapes {
  display: block;
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}
.shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(40px);
  opacity: 0.4;
  animation: float 15s ease-in-out infinite alternate;
}
.shape-1 {
  width: 300px;
  height: 300px;
  background: rgba(37, 99, 235, 0.2);
  top: -100px;
  left: -100px;
}
.shape-2 {
  width: 400px;
  height: 400px;
  background: rgba(139, 92, 246, 0.15);
  bottom: -150px;
  right: -100px;
  animation-delay: -5s;
}
.shape-3 {
  width: 200px;
  height: 200px;
  background: rgba(192, 38, 211, 0.15);
  top: 40%;
  left: 60%;
  animation-delay: -10s;
}

@keyframes float {
  0% { transform: translate(0, 0) scale(1) rotate(0deg); }
  33% { transform: translate(30px, -50px) scale(1.1) rotate(10deg); }
  66% { transform: translate(-20px, 20px) scale(0.9) rotate(-5deg); }
  100% { transform: translate(0, 0) scale(1) rotate(0deg); }
}

.login-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 440px;
  padding: 0 20px;
}

.login-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 48px 40px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(255, 255, 255, 0.8) inset;
  border: 1px solid rgba(255, 255, 255, 0.6);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.login-content {
  position: relative;
  z-index: 1;
}

.particles-container {
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: 24px;
  z-index: -1;
}
.login-card:hover {
  transform: translateY(-2px);
}
.login-header {
  text-align: center;
  margin-bottom: 32px;
}
.login-header h1 {
  font-size: 56px;
  margin-bottom: 16px;
  display: inline-block;
  background: var(--ina-ai-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  filter: drop-shadow(0 4px 12px rgba(37, 99, 235, 0.3));
  transform: scale(1);
  transition: transform 0.3s ease;
}
.login-header h1:hover {
  transform: scale(1.05);
}
.login-header h2 {
  font-size: 28px;
  color: var(--ina-text);
  margin: 0;
  font-weight: 800;
  letter-spacing: -0.5px;
}
.login-header p {
  font-size: 15px;
  color: var(--ina-text-3);
  margin: 10px 0 0;
  font-weight: 500;
}
.login-tabs {
  margin-top: 8px;
}
:deep(.el-tabs__nav-wrap::after) {
  display: none;
}
:deep(.el-tabs__item) {
  font-size: 16px;
  font-weight: 600;
  color: var(--ina-text-2);
}
:deep(.el-tabs__item.is-active) {
  color: var(--ina-primary);
}
:deep(.el-tabs__active-bar) {
  background-color: var(--ina-primary);
}
.login-btn {
  width: 100%;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 2px;
  border-radius: var(--ina-radius-md);
  background: var(--ina-ai-gradient);
  background-size: 200% auto;
  border: none;
  height: 52px;
  margin-top: 16px;
  box-shadow: 0 8px 20px -8px rgba(37, 99, 235, 0.6);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  color: white;
}
.login-btn:hover {
  background-position: right center;
  transform: translateY(-2px);
  box-shadow: 0 12px 24px -8px rgba(139, 92, 246, 0.7);
}
.login-btn:active {
  transform: translateY(1px) scale(0.98);
  box-shadow: 0 4px 12px -8px rgba(37, 99, 235, 0.5);
}
:deep(.el-input__wrapper) {
  border-radius: var(--ina-radius-md);
  box-shadow: none !important;
  border: 1px solid rgba(220, 223, 230, 0.8);
  background: rgba(255, 255, 255, 0.9);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 8px 16px;
}
:deep(.el-input__wrapper.is-focus) {
  border-color: var(--ina-primary);
  box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.1) !important;
  background: #ffffff;
}
:deep(.el-input__prefix-inner) {
  color: var(--ina-text-3);
  font-size: 18px;
}
</style>

<style>
/* 将粒子样式放在全局以防止 scoped 导致动态生成的 DOM 无法匹配动画和样式 */
.interaction-particle {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
  transform: translate(-50%, -50%);
  animation: particle-float-edge cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
  opacity: 0;
  z-index: 0;
}

@keyframes particle-float-edge {
  0% {
    transform: translate(-50%, -50%) scale(0.5);
    opacity: 0;
  }
  20% {
    opacity: 1;
    transform: translate(calc(-50% + var(--tx) * 0.2), calc(-50% + var(--ty) * 0.2)) scale(1.2);
  }
  100% {
    transform: translate(calc(-50% + var(--tx)), calc(-50% + var(--ty))) scale(0.2);
    opacity: 0;
  }
}
</style>
