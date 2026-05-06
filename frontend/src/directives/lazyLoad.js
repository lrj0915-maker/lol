/**
 * Vue 3 图片懒加载指令
 * 使用 Intersection Observer API 实现高性能懒加载
 * 支持加载失败重试和fallback
 */

// 占位符图片（1x1透明像素）
const PLACEHOLDER = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'

// 加载失败的默认图片（符文图标样式）
const ERROR_IMAGE = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="64" height="64"%3E%3Crect width="64" height="64" fill="%23222" rx="8"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%234ECCB3" font-size="32"%3E%3F%3C/text%3E%3C/svg%3E'

// 重试配置
const MAX_RETRIES = 2
const RETRY_DELAY = 1000 // 1秒

// 创建 Intersection Observer 实例
let observer = null

function createObserver() {
  if (observer) return observer

  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const img = entry.target
          const src = img.dataset.src

          if (src) {
            loadImage(img, src, 0)
          }

          // 停止观察已加载的图片
          observer.unobserve(img)
        }
      })
    },
    {
      // 提前 50px 开始加载
      rootMargin: '50px',
      // 至少 10% 可见时触发
      threshold: 0.1
    }
  )

  return observer
}

function loadImage(img, src, retryCount = 0) {
  // 创建新的 Image 对象预加载
  const tempImg = new Image()
  
  tempImg.onload = () => {
    img.src = src
    img.classList.add('lazy-loaded')
    img.classList.remove('lazy-loading', 'lazy-error')
    img.style.opacity = '1'
    
    // 触发自定义事件
    img.dispatchEvent(new CustomEvent('lazy-loaded', { detail: { src } }))
  }
  
  tempImg.onerror = (error) => {
    // 重试逻辑
    if (retryCount < MAX_RETRIES) {
      setTimeout(() => {
        loadImage(img, src, retryCount + 1)
      }, RETRY_DELAY * (retryCount + 1)) // 指数退避
    } else {
      // 最终失败，显示错误图片
      img.src = ERROR_IMAGE
      img.classList.add('lazy-error')
      img.classList.remove('lazy-loading')
      img.style.opacity = '0.5'
      
      // 触发自定义事件
      img.dispatchEvent(new CustomEvent('lazy-error', { detail: { src, error } }))
    }
  }
  
  tempImg.src = src
}

export default {
  // Vue 3 指令生命周期
  mounted(el, binding) {
    // 设置占位符
    el.src = PLACEHOLDER
    el.classList.add('lazy-loading')
    
    // 保存真实图片地址
    el.dataset.src = binding.value
    
    // 添加加载样式
    el.style.transition = 'opacity 0.3s ease-in-out'
    el.style.opacity = '0.3'
    
    // 添加加载动画
    el.style.animation = 'pulse 1.5s ease-in-out infinite'
    
    // 开始观察
    const obs = createObserver()
    obs.observe(el)
  },

  updated(el, binding) {
    // 如果图片地址变化，重新加载
    if (binding.value !== binding.oldValue) {
      el.src = PLACEHOLDER
      el.classList.remove('lazy-loaded', 'lazy-error')
      el.classList.add('lazy-loading')
      el.dataset.src = binding.value
      el.style.opacity = '0.3'
      el.style.animation = 'pulse 1.5s ease-in-out infinite'
      
      const obs = createObserver()
      obs.observe(el)
    }
  },

  unmounted(el) {
    // 清理观察
    if (observer) {
      observer.unobserve(el)
    }
  }
}

