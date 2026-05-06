# 🎙️ 音频文件目录

## 📁 这个目录用于存放野怪提示的语音文件

### 📝 需要的文件（共22个）

将生成的WAV文件放到这个目录下，文件名必须完全匹配：

#### 敌方野怪（6个）
- enemy_blue.wav
- enemy_red.wav
- enemy_gromp.wav
- enemy_raptors.wav
- enemy_wolves.wav
- enemy_krugs.wav

#### 己方野怪（6个）
- ally_blue.wav
- ally_red.wav
- ally_gromp.wav
- ally_raptors.wav
- ally_wolves.wav
- ally_krugs.wav

#### 路线野怪（2个）
- top_scuttle.wav
- bot_scuttle.wav

#### 史诗野怪（2个）
- enemy_herald.wav
- ally_herald.wav

#### 无前缀野怪（6个）
- scuttle.wav
- dragon.wav
- baron.wav
- herald.wav
- grubs.wav
- alert.wav

---

## ✅ 检查方法

运行测试脚本检查音频文件状态：

```bash
cd lol-assistant
python test_audio_system.py
```

---

## 🎤 文件要求

- **格式**: WAV
- **采样率**: 44100 Hz
- **位深度**: 16-bit
- **声道**: 单声道
- **时长**: 1-2秒

---

**将音频文件放到这个目录后，程序会自动识别并播放！**
