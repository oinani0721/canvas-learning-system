"""
Mock API Server for Contract Testing

提供Canvas API和Agent API的Mock实现，用于Contract Testing验证。

使用方式:
```bash
# 启动Canvas API Mock服务器（端口8000）
python src/tests/contract/mock_api_server.py --api canvas --port 8000

# 启动Agent API Mock服务器（端口8001）
python src/tests/contract/mock_api_server.py --api agent --port 8001

# 同时启动两个服务器（使用多进程）
python src/tests/contract/mock_api_server.py --api both
```

环境变量:
- CANVAS_API_PORT: Canvas API端口（默认8000）
- AGENT_API_PORT: Agent API端口（默认8001）
"""

import argparse
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from flask import Flask, jsonify, request
from flask_cors import CORS

# ============================================================================
# Mock Data
# ============================================================================

# 14个Agents的元数据
AGENTS_METADATA = {
    "canvas-orchestrator": {
        "name": "canvas-orchestrator",
        "type": "learning",
        "description": "Orchestrates all Canvas learning system operations",
        "timeout": 120,
        "emoji": "🎯"
    },
    "basic-decomposition": {
        "name": "basic-decomposition",
        "type": "learning",
        "description": "Decomposes difficult materials into basic guiding questions",
        "timeout": 60,
        "emoji": "🔍"
    },
    "deep-decomposition": {
        "name": "deep-decomposition",
        "type": "learning",
        "description": "Creates deep verification questions to test true understanding",
        "timeout": 60,
        "emoji": "🔬"
    },
    "question-decomposition": {
        "name": "question-decomposition",
        "type": "learning",
        "description": "Generates problem-solving breakthrough questions",
        "timeout": 60,
        "emoji": "❓"
    },
    "oral-explanation": {
        "name": "oral-explanation",
        "type": "learning",
        "description": "Generates oral-style explanations like a professor teaching",
        "timeout": 90,
        "emoji": "🗣️"
    },
    "clarification-path": {
        "name": "clarification-path",
        "type": "learning",
        "description": "Generates systematic clarification documents (1500+ words)",
        "timeout": 90,
        "emoji": "🔍"
    },
    "comparison-table": {
        "name": "comparison-table",
        "type": "learning",
        "description": "Generates structured comparison tables",
        "timeout": 60,
        "emoji": "📊"
    },
    "memory-anchor": {
        "name": "memory-anchor",
        "type": "learning",
        "description": "Generates vivid analogies and mnemonics",
        "timeout": 60,
        "emoji": "⚓"
    },
    "four-level-explanation": {
        "name": "four-level-explanation",
        "type": "learning",
        "description": "Generates progressive 4-level explanations",
        "timeout": 90,
        "emoji": "🎯"
    },
    "example-teaching": {
        "name": "example-teaching",
        "type": "learning",
        "description": "Generates complete problem-solving tutorials",
        "timeout": 90,
        "emoji": "📝"
    },
    "scoring-agent": {
        "name": "scoring-agent",
        "type": "learning",
        "description": "Evaluates user's understanding using 4-dimension scoring",
        "timeout": 60,
        "emoji": "📊"
    },
    "verification-question-agent": {
        "name": "verification-question-agent",
        "type": "learning",
        "description": "Generates deep verification questions from red/purple nodes",
        "timeout": 60,
        "emoji": "✅"
    },
    "review-board-agent-selector": {
        "name": "review-board-agent-selector",
        "type": "system",
        "description": "Intelligent agent scheduler and quality analyzer",
        "timeout": 60,
        "emoji": "🎛️"
    },
    "graphiti-memory-agent": {
        "name": "graphiti-memory-agent",
        "type": "system",
        "description": "Graphiti knowledge graph memory service",
        "timeout": 90,
        "emoji": "🧠"
    }
}

# Mock Canvas数据
MOCK_CANVAS_DATA = {
    "nodes": [
        {
            "id": "question-001",
            "type": "text",
            "x": 100,
            "y": 200,
            "width": 300,
            "height": 100,
            "color": "1",
            "text": "什么是逆否命题？"
        },
        {
            "id": "yellow-001",
            "type": "text",
            "x": 150,
            "y": 360,
            "width": 300,
            "height": 100,
            "color": "6",
            "text": "逆否命题是将原命题的条件和结论都否定后再交换位置"
        }
    ],
    "edges": [
        {
            "id": "edge-001",
            "fromNode": "question-001",
            "toNode": "yellow-001",
            "fromSide": "bottom",
            "toSide": "top"
        }
    ]
}

# 任务存储（用于异步任务模拟）
TASKS_STORAGE: Dict[str, Dict[str, Any]] = {}

# ============================================================================
# Canvas API Endpoints
# ============================================================================

def create_canvas_api() -> Flask:
    """创建Canvas API Flask应用"""
    app = Flask(__name__)
    CORS(app)

    @app.route('/api/v1/canvas', methods=['GET'])
    def read_canvas():
        """读取Canvas文件"""
        path = request.args.get('path')
        if not path:
            return jsonify({"error": "MissingParameter", "message": "path parameter is required"}), 400

        # Mock: 所有路径都返回相同的测试数据
        return jsonify(MOCK_CANVAS_DATA), 200

    @app.route('/api/v1/canvas', methods=['POST'])
    def write_canvas():
        """写入Canvas文件"""
        data = request.get_json()
        if not data or 'path' not in data or 'data' not in data:
            return jsonify({"error": "InvalidRequest", "message": "Missing path or data"}), 400

        canvas_data = data['data']
        nodes_count = len(canvas_data.get('nodes', []))
        edges_count = len(canvas_data.get('edges', []))

        return jsonify({
            "success": True,
            "path": data['path'],
            "nodes_count": nodes_count,
            "edges_count": edges_count
        }), 200

    @app.route('/api/v1/canvas/<canvas_id>/nodes', methods=['GET'])
    def list_nodes(canvas_id: str):
        """列出所有节点"""
        color_filter = request.args.get('color')
        nodes = MOCK_CANVAS_DATA['nodes']

        if color_filter:
            nodes = [n for n in nodes if n.get('color') == color_filter]

        return jsonify({"nodes": nodes, "total": len(nodes)}), 200

    @app.route('/api/v1/canvas/<canvas_id>/nodes', methods=['POST'])
    def add_node(canvas_id: str):
        """添加节点"""
        node_data = request.get_json()
        if not node_data:
            return jsonify({"error": "InvalidRequest", "message": "Missing node data"}), 400

        # 生成节点ID（如果未提供）
        if 'id' not in node_data:
            node_data['id'] = f"node-{uuid.uuid4().hex[:8]}"

        return jsonify(node_data), 201

    @app.route('/api/v1/canvas/<canvas_id>/nodes/<node_id>', methods=['GET'])
    def get_node(canvas_id: str, node_id: str):
        """获取节点"""
        # Mock: 返回固定节点
        node = next((n for n in MOCK_CANVAS_DATA['nodes'] if n['id'] == node_id), None)
        if not node:
            return jsonify({"error": "NodeNotFound", "message": f"Node '{node_id}' not found"}), 404
        return jsonify(node), 200

    @app.route('/api/v1/canvas/<canvas_id>/nodes/<node_id>', methods=['PATCH'])
    def update_node(canvas_id: str, node_id: str):
        """更新节点"""
        updates = request.get_json()
        node = next((n for n in MOCK_CANVAS_DATA['nodes'] if n['id'] == node_id), None)

        if not node:
            return jsonify({"error": "NodeNotFound", "message": f"Node '{node_id}' not found"}), 404

        # 应用更新
        node.update(updates)
        return jsonify(node), 200

    @app.route('/api/v1/canvas/<canvas_id>/nodes/<node_id>', methods=['DELETE'])
    def delete_node(canvas_id: str, node_id: str):
        """删除节点"""
        return '', 204

    @app.route('/api/v1/canvas/<canvas_id>/edges', methods=['POST'])
    def add_edge(canvas_id: str):
        """添加边"""
        edge_data = request.get_json()
        if not edge_data:
            return jsonify({"error": "InvalidRequest", "message": "Missing edge data"}), 400

        # 验证必需字段
        required = ['fromNode', 'toNode']
        for field in required:
            if field not in edge_data:
                return jsonify({"error": "ValidationError", "message": f"Missing required field: {field}"}), 400

        # 生成边ID（如果未提供）
        if 'id' not in edge_data:
            edge_data['id'] = f"edge-{uuid.uuid4().hex[:8]}"

        return jsonify(edge_data), 201

    @app.route('/api/v1/canvas/<canvas_id>/edges/<edge_id>', methods=['DELETE'])
    def delete_edge(canvas_id: str, edge_id: str):
        """删除边"""
        return '', 204

    @app.route('/api/v1/canvas/<canvas_id>/nodes/<node_id>/color', methods=['PATCH'])
    def update_node_color(canvas_id: str, node_id: str):
        """更新节点颜色"""
        color_data = request.get_json()
        if not color_data or 'color' not in color_data:
            return jsonify({"error": "ValidationError", "message": "Missing required field: color"}), 400

        # 验证颜色代码 (Story 12.B.4: 1=灰, 2=绿, 3=紫, 4=红, 5=蓝, 6=黄)
        valid_colors = ["1", "2", "3", "4", "5", "6"]
        if color_data['color'] not in valid_colors:
            return jsonify({"error": "ValidationError", "message": f"Invalid color code: {color_data['color']}"}), 400

        # 查找节点
        node = next((n for n in MOCK_CANVAS_DATA['nodes'] if n['id'] == node_id), None)
        if not node:
            return jsonify({"error": "NodeNotFound", "message": f"Node '{node_id}' not found"}), 404

        # 更新颜色
        node['color'] = color_data['color']
        return jsonify(node), 200

    @app.route('/api/v1/canvas/<canvas_id>/layout', methods=['POST'])
    def apply_layout(canvas_id: str):
        """应用布局算法"""
        layout_data = request.get_json()
        if not layout_data or 'algorithm' not in layout_data:
            return jsonify({"error": "ValidationError", "message": "Missing required field: algorithm"}), 400

        # 验证algorithm
        valid_algorithms = ["v1.1", "clustered", "force-directed"]
        if layout_data['algorithm'] not in valid_algorithms:
            return jsonify({"error": "ValidationError", "message": f"Invalid algorithm: {layout_data['algorithm']}"}), 400

        # 返回带更新坐标的Canvas数据
        return jsonify(MOCK_CANVAS_DATA), 200

    @app.route('/api/v1/canvas/<canvas_id>/analyze', methods=['POST'])
    def analyze_canvas(canvas_id: str):
        """分析Canvas"""
        return jsonify({
            "total_nodes": 2,
            "total_edges": 1,
            "nodes_by_color": {
                "red": 1,
                "green": 0,
                "purple": 0,
                "blue": 0,
                "yellow": 1
            },
            "yellow_nodes": [MOCK_CANVAS_DATA['nodes'][1]],
            "verification_nodes": [MOCK_CANVAS_DATA['nodes'][0]]
        }), 200

    return app

# ============================================================================
# Agent API Endpoints
# ============================================================================

def create_agent_api() -> Flask:
    """创建Agent API Flask应用"""
    app = Flask(__name__)
    CORS(app)

    @app.route('/api/v1/agents', methods=['GET'])
    def list_agents():
        """列出所有agents"""
        agent_type = request.args.get('type')
        agents = list(AGENTS_METADATA.values())

        if agent_type:
            agents = [a for a in agents if a['type'] == agent_type]

        return jsonify({"agents": agents, "total": len(agents)}), 200

    @app.route('/api/v1/agents/<agent_name>', methods=['GET'])
    def get_agent_metadata(agent_name: str):
        """获取agent元数据"""
        if agent_name not in AGENTS_METADATA:
            return jsonify({
                "error": "AgentNotFoundError",
                "message": f"Agent '{agent_name}' not found"
            }), 404

        return jsonify(AGENTS_METADATA[agent_name]), 200

    @app.route('/api/v1/agents/<agent_name>/invoke', methods=['POST'])
    def invoke_agent(agent_name: str):
        """调用agent（异步）"""
        if agent_name not in AGENTS_METADATA:
            return jsonify({
                "error": "AgentNotFoundError",
                "message": f"Agent '{agent_name}' not found"
            }), 404

        request_data = request.get_json()
        if not request_data or 'input' not in request_data:
            return jsonify({
                "error": "ValidationError",
                "message": "Missing required field: input"
            }), 400

        # 创建任务
        task_id = f"task-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
        task = {
            "task_id": task_id,
            "status": "pending",
            "agent_name": agent_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "input": request_data['input'],
            "timeout": request_data.get('timeout', AGENTS_METADATA[agent_name]['timeout'])
        }

        TASKS_STORAGE[task_id] = task

        # 异步模拟：2秒后完成
        import threading
        def complete_task():
            time.sleep(2)
            TASKS_STORAGE[task_id]['status'] = 'completed'
            TASKS_STORAGE[task_id]['completed_at'] = datetime.now(timezone.utc).isoformat()

            # Mock结果（根据agent类型）
            if agent_name == 'scoring-agent':
                TASKS_STORAGE[task_id]['result'] = {
                    "accuracy": 22,
                    "imagery": 18,
                    "completeness": 20,
                    "originality": 15,
                    "total_score": 75,
                    "color": "3",
                    "recommendations": ["clarification-path", "oral-explanation"]
                }
            else:
                TASKS_STORAGE[task_id]['result'] = {
                    "message": f"{agent_name} executed successfully"
                }

        threading.Thread(target=complete_task, daemon=True).start()

        return jsonify(task), 202

    @app.route('/api/v1/agents/tasks/<task_id>', methods=['GET'])
    def get_task_status(task_id: str):
        """获取任务状态"""
        if task_id not in TASKS_STORAGE:
            return jsonify({
                "error": "TaskNotFoundError",
                "message": f"Task '{task_id}' not found"
            }), 404

        return jsonify(TASKS_STORAGE[task_id]), 200

    @app.route('/api/v1/agents/batch/invoke', methods=['POST'])
    def batch_invoke_agents():
        """批量调用agents"""
        request_data = request.get_json()
        if not request_data or 'agents' not in request_data:
            return jsonify({
                "error": "ValidationError",
                "message": "Missing required field: agents"
            }), 400

        agents_list = request_data['agents']
        batch_task_id = f"batch-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
        task_ids = []

        # 为每个agent创建任务
        for agent_req in agents_list:
            task_id = f"task-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
            task_ids.append(task_id)
            TASKS_STORAGE[task_id] = {
                "task_id": task_id,
                "status": "pending",
                "agent_name": agent_req['agent_name'],
                "created_at": datetime.now(timezone.utc).isoformat()
            }

        return jsonify({
            "batch_task_id": batch_task_id,
            "status": "pending",
            "total_agents": len(agents_list),
            "task_ids": task_ids,
            "created_at": datetime.now(timezone.utc).isoformat()
        }), 202

    return app

# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Mock API Server for Contract Testing')
    parser.add_argument('--api', choices=['canvas', 'agent', 'both'], default='both',
                        help='Which API to start (default: both)')
    parser.add_argument('--canvas-port', type=int, default=8000,
                        help='Canvas API port (default: 8000)')
    parser.add_argument('--agent-port', type=int, default=8001,
                        help='Agent API port (default: 8001)')

    args = parser.parse_args()

    if args.api in ['canvas', 'both']:
        canvas_app = create_canvas_api()
        print(f"[*] Starting Canvas API Mock Server on port {args.canvas_port}...")
        if args.api == 'canvas':
            canvas_app.run(host='0.0.0.0', port=args.canvas_port, debug=True)
        else:
            # 使用多线程启动
            import threading
            threading.Thread(
                target=canvas_app.run,
                kwargs={'host': '0.0.0.0', 'port': args.canvas_port, 'debug': False},
                daemon=True
            ).start()

    if args.api in ['agent', 'both']:
        agent_app = create_agent_api()
        print(f"[*] Starting Agent API Mock Server on port {args.agent_port}...")
        agent_app.run(host='0.0.0.0', port=args.agent_port, debug=False)

if __name__ == '__main__':
    main()
