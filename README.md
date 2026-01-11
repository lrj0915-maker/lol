# LOL 战绩助手

基于 LCU API 的英雄联盟辅助工具。

## 功能

- 自动准备：匹配成功后自动接受
- 自动选人：按预设优先级自动 Ban/Pick
- 战绩分析：游戏结束后展示详细数据分析

## 技术栈

- 后端：Python + PyWebView
- 前端：Vue 3 + Vite + ECharts
- 数据：SQLite

## 安装

### 后端依赖

```bash
cd lol-assistant
pip install -r requirements.txt
```

### 前端依赖

```bash
cd frontend
npm install
```

## 开发

### 启动前端开发服务器

```bash
cd frontend
npm run dev
```

### 启动后端

```bash
cd backend
python main.py
```

## 构建

### 构建前端

```bash
cd frontend
npm run build
```

## 使用说明

1. 启动英雄联盟客户端
2. 运行本程序
3. 程序会自动连接到客户端
4. 在"选人"页面配置各位置的 Ban/Pick 列表
5. 在状态栏开启自动准备/自动选人
6. 游戏结束后自动显示战绩分析
