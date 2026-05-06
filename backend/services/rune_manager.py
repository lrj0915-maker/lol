"""符文页管理服务。"""

from lcu.connection import LCUConnection


class RuneManager:
    """负责将符文配置应用到客户端。"""

    MAX_PAGES = 25
    VALID_TREE_IDS = {8000, 8100, 8200, 8300, 8400}

    def __init__(self, lcu_connection: LCUConnection):
        self.lcu = lcu_connection

    def get_current_page(self):
        return self.lcu.get('/lol-perks/v1/currentpage')

    def get_all_pages(self):
        return self.lcu.get('/lol-perks/v1/pages')

    def delete_page(self, page_id):
        return self.lcu.delete(f'/lol-perks/v1/pages/{page_id}')

    def create_page(self, page_data):
        return self.lcu.post('/lol-perks/v1/pages', page_data)

    def apply_rune_config(self, rune_config, champion_name='', position=''):
        try:
            editable, reason, reason_code = self.is_rune_page_editable()
            if not editable:
                return {
                    'success': False,
                    'message': reason,
                    'code': reason_code,
                }

            current_page = self.get_current_page()
            if not current_page:
                return {
                    'success': False,
                    'message': '无法获取当前符文页，请确认客户端已启动并停留在可编辑阶段。',
                    'code': 'RUNE_CURRENT_PAGE_MISSING',
                }

            page_name = self._generate_page_name(champion_name, position)
            selected_perk_ids = self._build_selected_perk_ids(rune_config)

            # 优先复用当前非默认页：稳定、快、不占页数。
            current_page_id = current_page.get('id')
            if current_page_id and not current_page.get('isDefault', False):
                update_payload = {
                    'id': current_page_id,
                    'name': page_name,
                    'primaryStyleId': rune_config.get('primary_page_id'),
                    'subStyleId': rune_config.get('secondary_page_id'),
                    'selectedPerkIds': selected_perk_ids,
                    'current': True,
                }
                update_result = self.lcu.put(f'/lol-perks/v1/pages/{current_page_id}', update_payload)
                if update_result:
                    return {
                        'success': True,
                        'message': f'符文已应用（复用当前页）：{page_name}',
                        'code': 'OK',
                        'strategy': 'update',
                        'page_data': update_payload,
                    }

                # 复用失败时降级：删除后重建。
                if not self.delete_page(current_page_id):
                    return {
                        'success': False,
                        'message': '符文页更新失败，且无法删除旧页后重建。',
                        'code': 'RUNE_UPDATE_FAILED',
                    }

            # 如果页数已满，先尝试删除一个可删的非默认页。
            pages = self.get_all_pages() or []
            if len(pages) >= self.MAX_PAGES:
                reusable = next((page for page in pages if not page.get('isDefault', False)), None)
                if not reusable:
                    return {
                        'success': False,
                        'message': '符文页已满且没有可复用页，请先手动删除一个自定义符文页。',
                        'code': 'RUNE_PAGE_FULL',
                    }
                if not self.delete_page(reusable.get('id')):
                    return {
                        'success': False,
                        'message': '符文页已满，尝试清理旧页失败。',
                        'code': 'RUNE_PAGE_FULL',
                    }

            page_data = {
                'name': page_name,
                'primaryStyleId': rune_config.get('primary_page_id'),
                'subStyleId': rune_config.get('secondary_page_id'),
                'selectedPerkIds': selected_perk_ids,
                'current': True,
            }

            create_result = self.create_page(page_data)
            if not create_result:
                return {
                    'success': False,
                    'message': '创建符文页失败，请稍后重试。',
                    'code': 'RUNE_CREATE_FAILED',
                }

            return {
                'success': True,
                'message': f'符文已应用：{page_name}',
                'code': 'OK',
                'strategy': 'create',
                'page_data': page_data,
            }
        except Exception as exc:
            return {
                'success': False,
                'message': f'应用符文时出现异常: {exc}',
                'code': 'RUNE_EXCEPTION',
            }

    def is_rune_page_editable(self):
        try:
            phase = self.lcu.get('/lol-gameflow/v1/gameflow-phase')
            if phase in ('InProgress', 'EndOfGame'):
                return False, '当前游戏阶段不允许修改符文，请在对局外操作。', 'RUNE_EDIT_NOT_ALLOWED'

            pages = self.get_all_pages() or []
            if len(pages) >= self.MAX_PAGES:
                has_non_default = any(not page.get('isDefault', False) for page in pages)
                if not has_non_default:
                    return False, '符文页已满且无可复用页，请先删除一个自定义符文页。', 'RUNE_PAGE_FULL'

            return True, '', ''
        except Exception as exc:
            return False, f'检查符文页状态失败: {exc}', 'RUNE_EDIT_CHECK_FAILED'

    def _build_selected_perk_ids(self, rune_config):
        return (
            rune_config.get('primary_rune_ids', [])
            + rune_config.get('secondary_rune_ids', [])
            + rune_config.get('stat_mod_ids', [])
        )

    def _generate_page_name(self, champion_name='', position=''):
        parts = []
        if champion_name:
            parts.append(champion_name)

        if position:
            position_names = {
                'TOP': '上单',
                'JUNGLE': '打野',
                'MID': '中单',
                'ADC': '下路',
                'SUPPORT': '辅助',
            }
            parts.append(position_names.get(position, position))

        if not parts:
            parts.append('推荐符文')

        return ' - '.join(parts)

    def get_available_rune_pages_count(self):
        pages = self.get_all_pages()
        if not pages:
            return 0
        return self.MAX_PAGES - len(pages)

    def validate_rune_config(self, rune_config):
        required_fields = ['primary_page_id', 'secondary_page_id', 'primary_rune_ids', 'secondary_rune_ids', 'stat_mod_ids']
        for field in required_fields:
            if field not in rune_config:
                return False, f'缺少必需字段: {field}'

        if len(rune_config['primary_rune_ids']) != 4:
            return False, f"主系符文数量错误: 需要4个，实际{len(rune_config['primary_rune_ids'])}个"

        if len(rune_config['secondary_rune_ids']) != 2:
            return False, f"副系符文数量错误: 需要2个，实际{len(rune_config['secondary_rune_ids'])}个"

        if len(rune_config['stat_mod_ids']) != 3:
            return False, f"属性碎片数量错误: 需要3个，实际{len(rune_config['stat_mod_ids'])}个"

        if rune_config['primary_page_id'] not in self.VALID_TREE_IDS:
            return False, f"无效的主系符文树ID: {rune_config['primary_page_id']}"

        if rune_config['secondary_page_id'] not in self.VALID_TREE_IDS:
            return False, f"无效的副系符文树ID: {rune_config['secondary_page_id']}"

        if rune_config['primary_page_id'] == rune_config['secondary_page_id']:
            return False, '主系和副系符文树不能相同'

        return True, ''

