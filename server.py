"""
OPC UA 模拟服务器
模拟 opc_list_test.xlsx 中的所有点位数据
运行方式: python server.py
"""

import math
import random
import signal
import sys
import time
import threading

import openpyxl
from opcua import Server, ua


def read_point_table(excel_path):
    """从点表读取所有设备的点位信息"""
    wb = openpyxl.load_workbook(excel_path)
    ws = wb['Sheet1']

    equipment = [
        (1, 2, 'control', '设备启停'),
        (3, 4, 'shearer', '采煤机'),
        (5, 6, 'support', '电液控'),
        (7, 8, 'sanji', '三机'),
        (9, 10, 'belt', '皮带'),
        (11, 12, 'liquid', '泵站'),
        (13, 14, 'power', '供电'),
        (15, 16, 'transformer', '移变'),
        (17, 18, 'switch', '开关'),
        (19, 20, 'alarm', '故障'),
    ]

    all_points = []
    for name_col, addr_col, key, label in equipment:
        points = []
        for row in range(2, ws.max_row + 1):
            name = ws.cell(row=row, column=name_col).value
            if name is None:
                continue
            points.append(str(name))
        all_points.append((key, label, points))

    return all_points


def generate_value(point_name, tick):
    """根据点位名称生成模拟值"""
    name = point_name.lower()

    # 通讯状态 - 固定为1
    if '通讯' in name:
        return 1

    # 运行状态 - 周期性开关
    if '运行' in name or '状态' in name:
        return 1 if tick % 20 < 15 else 0

    # 请求开/关 - 脉冲
    if '请求开' in name:
        return 1 if tick % 30 == 0 else 0
    if '请求关' in name:
        return 1 if tick % 30 == 15 else 0

    # 闭锁/急停 - 正常为0
    if '闭锁' in name or '急停' in name:
        return 0

    # 远控/自动 - 正常为1
    if '远控' in name or '自动' in name or '手动' in name:
        return 1

    # 电流 - 随机波动
    if '电流' in name:
        base = 50.0 if '采煤机' in name else 30.0
        return round(base + random.uniform(-5, 5) + 2 * math.sin(tick * 0.1), 2)

    # 电压
    if '电压' in name:
        return round(3300 + random.uniform(-50, 50), 1)

    # 温度
    if '温度' in name:
        return round(45 + random.uniform(-5, 15) + 3 * math.sin(tick * 0.05), 1)

    # 压力
    if '压力' in name:
        return round(20 + random.uniform(-3, 5) + 2 * math.sin(tick * 0.08), 2)

    # 转速
    if '转速' in name:
        return round(1450 + random.uniform(-50, 50), 0)

    # 采高
    if '采高' in name or '高度' in name:
        return round(1.5 + random.uniform(-0.3, 0.3), 2)

    # 位置/架号
    if '位置' in name or '架号' in name:
        return int(50 + 20 * math.sin(tick * 0.02))

    # 速度
    if '速度' in name or '转速' in name:
        return round(5 + random.uniform(-1, 3), 1)

    # 浓度
    if '浓度' in name:
        return round(3.5 + random.uniform(-0.5, 0.5), 1)

    # 液位/油位/水位
    if '液位' in name or '油位' in name or '水位' in name:
        return round(60 + random.uniform(-10, 10), 1)

    # 瓦斯
    if '瓦斯' in name:
        return round(0.05 + random.uniform(0, 0.15), 3)

    # 倾角/俯仰角
    if '倾角' in name or '俯仰角' in name:
        return round(random.uniform(-5, 5), 1)

    # 转向/向左/向右/方向 - 0或1
    if '转向' in name or '向左' in name or '向右' in name or '方向' in name:
        return random.choice([0, 1])

    # 工作方式 - 整数
    if '工作方式' in name:
        return random.choice([0, 1, 2])

    # 开机率
    if '开机率' in name:
        return round(70 + random.uniform(-10, 20), 1)

    # 运行时间/累计时间
    if '时间' in name:
        return int(tick * 60 + random.randint(0, 3600))

    # 保护状态 - 正常为0
    if '保护' in name:
        return 0

    # 通断/故障字
    if '通断' in name:
        return 1
    if '故障' in name:
        return 0

    # 张力
    if '张力' in name:
        return round(50 + random.uniform(-5, 5), 1)

    # 频率
    if '频率' in name:
        return round(50 + random.uniform(-1, 1), 2)

    # 功率
    if '功率' in name:
        return round(100 + random.uniform(-20, 30), 1)

    # 转矩
    if '转矩' in name:
        return round(80 + random.uniform(-10, 15), 1)

    # 湿度
    if '湿度' in name:
        return round(40 + random.uniform(-5, 15), 1)

    # 方向
    if '方向' in name:
        return random.choice([0, 1])

    # 跟机状态
    if '跟机' in name:
        return random.choice([0, 1])

    # 默认返回随机小数
    return round(random.uniform(0, 100), 2)


class MiningOPCSimulator:
    def __init__(self, endpoint='opc.tcp://0.0.0.0:14840/freeopcua/server/'):
        self.server = Server()
        self.server.set_endpoint(endpoint)
        self.server.set_server_name('Mining Equipment Simulator')
        self.nodes = {}  # {point_name: node}
        self.point_names = []  # 按顺序存储所有点名
        self.tick = 0
        self.running = True

    def setup(self, excel_path):
        """从点表创建OPC节点"""
        all_points = read_point_table(excel_path)

        # 注册命名空间
        uri = 'http://mining.simulator'
        idx = self.server.register_namespace(uri)

        # 获取Objects节点
        objects = self.server.get_objects_node()

        total = 0
        for key, label, points in all_points:
            # 为每个设备类型创建文件夹
            folder = objects.add_folder(idx, label)

            for i, name in enumerate(points):
                # 清理名称用于OPC节点名
                clean_name = name.replace('_', '/')
                node = folder.add_variable(
                    ua.NodeId(f'{key}/{i}', idx),
                    clean_name,
                    0.0,
                    ua.VariantType.Double
                )
                node.set_writable()
                # 使用 folder_key/index 作为唯一键，避免重复点名覆盖
                unique_key = f'{key}/{i}'
                self.nodes[unique_key] = (name, node)
                self.point_names.append(name)
                total += 1

        print(f'已创建 {total} 个OPC节点')

    def update_values(self):
        """更新所有节点的模拟值"""
        for unique_key, (name, node) in self.nodes.items():
            try:
                val = generate_value(name, self.tick)
                node.set_value(val)
            except Exception as e:
                pass

    def run(self):
        """启动服务器"""
        self.server.start()
        print(f'OPC服务器已启动: {self.server.endpoint}')
        print(f'按 Ctrl+C 停止')

        try:
            while self.running:
                self.update_values()
                self.tick += 1
                time.sleep(2)  # 每2秒更新一次
        except KeyboardInterrupt:
            pass
        finally:
            self.server.stop()
            print('OPC服务器已停止')


def generate_reading_excel(excel_path, output_path, endpoint):
    """生成用于读取的点表Excel，OPC地址指向模拟服务器"""
    wb_src = openpyxl.load_workbook(excel_path)
    ws_src = wb_src['Sheet1']

    wb_new = openpyxl.Workbook()
    ws_new = wb_new.active
    ws_new.title = 'Sheet1'

    # 写入表头
    headers = [
        '设备启停 0', None, '采煤机2', None, '电液控4', None,
        '三机6', None, '皮带8', None, '供液10', None,
        '供电12', None, '移变14', None, '开关16', None, '故障18', None,
    ]
    for col, h in enumerate(headers, 1):
        if h is not None:
            ws_new.cell(row=1, column=col, value=h)

    # 设备类型到命名空间路径的映射
    equip_keys = ['control', 'shearer', 'support', 'sanji', 'belt',
                  'liquid', 'power', 'transformer', 'switch', 'alarm']

    # 复制数据并替换OPC地址
    for row in range(2, ws_src.max_row + 1):
        for equip_idx in range(10):
            name_col = equip_idx * 2 + 1
            addr_col = equip_idx * 2 + 2
            name = ws_src.cell(row=row, column=name_col).value
            if name is None:
                continue

            # 写入名称
            ws_new.cell(row=row, column=name_col, value=name)

            # 生成新的OPC地址
            point_idx = row - 2
            new_addr = f'ns=2;s={equip_keys[equip_idx]}/{point_idx}'
            ws_new.cell(row=row, column=addr_col, value=new_addr)

    wb_new.save(output_path)
    print(f'读取点表已生成: {output_path}')


if __name__ == '__main__':
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(script_dir, 'opc_list_test.xlsx')
    output_path = os.path.join(script_dir, 'opc_sim_list.xlsx')

    # 生成读取点表
    endpoint = 'opc.tcp://0.0.0.0:14840/freeopcua/server/'
    generate_reading_excel(excel_path, output_path, endpoint)

    # 启动OPC服务器
    sim = MiningOPCSimulator(endpoint)
    sim.setup(excel_path)
    sim.run()
