// 全局 API 配置
// 开发环境：VITE_API_BASE 为空时走 vite 代理（/api -> 127.0.0.1:5000）
// 远程演示：设置 VITE_API_BASE 为后端公网地址，例如 https://xxx.cpolar.cn
export const API_BASE = import.meta.env.VITE_API_BASE || ''
