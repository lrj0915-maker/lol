"""音频播放管理器 - 使用 pygame.mixer 支持MP3"""
import os
import sys
import threading

from logger import get_logger

log = get_logger("AudioManager")

try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False
    log.warning("pygame未安装，语音播放功能不可用")


class AudioManager:
    """音频播放管理器 - 使用 pygame.mixer 播放MP3/WAV音频"""
    
    def __init__(self):
        # 音频文件目录
        self.audio_dir = os.path.join(
            os.path.dirname(__file__), 
            'audio'
        )
        self._ensure_audio_dir()
        self._initialized = False
        self._play_lock = threading.Lock()
        self._channel = None
        
        # 初始化 pygame.mixer
        if HAS_PYGAME:
            try:
                pygame.mixer.init()
                self._initialized = True
                # 预留一个专用 channel 用于顺序播报
                self._channel = pygame.mixer.Channel(0)
                log.info("pygame.mixer 初始化成功")
            except Exception as e:
                log.error("pygame.mixer 初始化失败: %s", e)
                self._initialized = False
    
    def _ensure_audio_dir(self):
        """确保音频目录存在"""
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)
            log.info("创建音频目录: %s", self.audio_dir)
    
    def play(self, audio_name):
        """播放音频（异步）
        
        Args:
            audio_name: 音频文件名（可含或不含扩展名）
        
        Returns:
            bool: 播放是否成功
        """
        if not HAS_PYGAME or not self._initialized:
            log.warning("pygame未初始化，无法播放")
            return False
        
        # 查找音频文件（支持 .mp3 和 .wav）
        audio_path = None
        
        # 如果已经包含扩展名
        if audio_name.endswith('.mp3') or audio_name.endswith('.wav'):
            test_path = os.path.join(self.audio_dir, audio_name)
            if os.path.exists(test_path):
                audio_path = test_path
        else:
            # 尝试 .mp3
            test_path = os.path.join(self.audio_dir, f"{audio_name}.mp3")
            if os.path.exists(test_path):
                audio_path = test_path
            else:
                # 尝试 .wav
                test_path = os.path.join(self.audio_dir, f"{audio_name}.wav")
                if os.path.exists(test_path):
                    audio_path = test_path
        
        if not audio_path:
            log.warning("音频文件不存在: %s", audio_name)
            return False
        
        try:
            # 使用专用 channel 顺序播放，避免多个音频叠加
            sound = pygame.mixer.Sound(audio_path)
            with self._play_lock:
                if self._channel is not None:
                    self._channel.queue(sound)
                else:
                    sound.play()
            return True
        except Exception as e:
            log.error("播放失败 %s: %s", audio_name, e)
            return False
    
    def get_audio_name(self, text):
        """根据识别文本生成音频文件名（中文）
        
        Args:
            text: 识别文本，如 "敌方蓝Buff" 或 "小龙"
        
        Returns:
            str: 音频文件名（不含扩展名）
        """
        # 清理文本
        text = text.strip()
        
        # 前缀映射：己方 → 我方
        if text.startswith('己方'):
            text = text.replace('己方', '我方', 1)
        
        # 河道蟹特殊处理
        if '河道蟹' in text:
            # 检测上/下关键字
            if '上' in text or '上路' in text:
                return '上路河道蟹'
            elif '下' in text or '下路' in text:
                return '下路河道蟹'
            else:
                # 默认使用上路
                return '上路河道蟹'
        
        # 直接返回文本作为文件名
        return text
    
    def play_by_text(self, text):
        """根据文本播放音频
        
        Args:
            text: 语音文本，如 "敌方蓝Buff" 或 "小龙"
        
        Returns:
            bool: 播放是否成功
        """
        # 获取音频文件名
        audio_name = self.get_audio_name(text)
        
        # 播放
        return self.play(audio_name)
    
    def list_audio_files(self):
        """列出所有可用的音频文件
        
        Returns:
            list: 音频文件列表
        """
        if not os.path.exists(self.audio_dir):
            return []
        
        files = []
        for f in os.listdir(self.audio_dir):
            if f.endswith('.wav') or f.endswith('.mp3'):
                files.append(f)
        
        return sorted(files)
    
    def check_missing_files(self):
        """检查缺失的音频文件
        
        Returns:
            list: 缺失的文件名列表
        """
        # 所有应该存在的文件（中文文件名）
        required_files = [
            # 敌方野怪
            '敌方蓝Buff', '敌方红Buff', '敌方魔沼蛙',
            '敌方锋喙鸟', '敌方三狼', '敌方石甲虫',
            # 我方野怪
            '我方蓝Buff', '我方红Buff', '我方魔沼蛙',
            '我方锋喙鸟', '我方三狼', '我方石甲虫',
            # 路线野怪
            '上路河道蟹', '下路河道蟹',
            # 史诗野怪
            '小龙', '大龙', '峡谷先锋', '虚空巢虫',
        ]
        
        existing_files = self.list_audio_files()
        # 去除扩展名
        existing_names = [f.replace('.mp3', '').replace('.wav', '') for f in existing_files]
        
        missing = []
        for f in required_files:
            if f not in existing_names:
                missing.append(f)
        
        return missing
    
    def get_audio_status(self):
        """获取音频文件状态
        
        Returns:
            dict: 状态信息
        """
        total = 18  # 更新为实际需要的文件数
        existing = len(self.list_audio_files())
        missing = self.check_missing_files()
        
        return {
            'total': total,
            'existing': existing,
            'missing_count': len(missing),
            'missing_files': missing,
            'complete': len(missing) == 0,
            'pygame_available': HAS_PYGAME and self._initialized
        }


# 全局实例
audio_manager = AudioManager()


if __name__ == '__main__':
    # 测试代码
    log.info("=" * 60)
    log.info("音频管理器测试")
    log.info("=" * 60)
    
    # 检查状态
    status = audio_manager.get_audio_status()
    log.info("音频文件状态:")
    log.info("  总数: %d", status['total'])
    log.info("  已有: %d", status['existing'])
    log.info("  缺失: %d", status['missing_count'])
    
    if status['missing_files']:
        log.info("缺失的文件:")
        for f in status['missing_files']:
            log.info("  - %s", f)
    else:
        log.info("所有音频文件已就绪")
    
    # 测试播放
    if status['existing'] > 0:
        log.info("测试播放第一个音频文件...")
        files = audio_manager.list_audio_files()
        if files:
            test_file = files[0].replace('.wav', '')
            log.info("  播放: %s.wav", test_file)
            audio_manager.play(test_file)
