"""
测试客户端 - 连接模拟OPC服务器并读取数据
用法: 先运行 server.py，再运行此脚本
"""

from opcua import Client


def main():
    endpoint = 'opc.tcp://localhost:14840/freeopcua/server/'
    client = Client(endpoint)

    try:
        client.connect()
        print(f'已连接到: {endpoint}')

        # 获取所有节点
        root = client.get_root_node()
        objects = client.get_objects_node()
        children = objects.get_children()

        print(f'\n设备文件夹:')
        for child in children:
            name = child.get_browse_name().Name
            nodes = child.get_children()
            print(f'  {name}: {len(nodes)} 个节点')

            # 读取前3个节点的值
            for node in nodes[:3]:
                try:
                    val = node.get_value()
                    bname = node.get_browse_name().Name
                    print(f'    {bname} = {val}')
                except Exception:
                    pass
            print()

    except Exception as e:
        print(f'连接失败: {e}')
        print('请先运行 python server.py 启动OPC服务器')
    finally:
        client.disconnect()


if __name__ == '__main__':
    main()
