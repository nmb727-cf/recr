from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from django.db import transaction

from apps.orchestration_center.models.workflow import Workflow, WorkflowEdge, WorkflowNode
from apps.workflow_execution.models import (
    WorkflowBuilderConnection,
    WorkflowBuilderLayout,
    WorkflowBuilderNode,
)


class WorkflowVisualBuilderEngine:
    NODE_TYPE_TO_RUNTIME = {
        'start': 'start',
        'stage': 'action',
        'decision': 'condition',
        'action': 'action',
        'human_task': 'human_task',
        'approval': 'approval',
        'delay': 'delay',
        'end': 'end',
    }

    @staticmethod
    def create_node(
        *,
        workflow_id,
        node_type: str,
        node_name: str,
        position_x: int = 0,
        position_y: int = 0,
        config: dict[str, Any] | None = None,
        tenant_id=None,
        created_by=None,
    ) -> WorkflowBuilderNode:
        return WorkflowBuilderNode.objects.create(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            node_type=node_type,
            node_name=node_name,
            position_x=position_x,
            position_y=position_y,
            config=config or {},
            created_by=created_by,
            is_active=True,
        )

    @staticmethod
    def update_node(
        *,
        node: WorkflowBuilderNode,
        node_name: str | None = None,
        position_x: int | None = None,
        position_y: int | None = None,
        config: dict[str, Any] | None = None,
        is_active: bool | None = None,
    ) -> WorkflowBuilderNode:
        if node_name is not None:
            node.node_name = node_name
        if position_x is not None:
            node.position_x = position_x
        if position_y is not None:
            node.position_y = position_y
        if config is not None:
            node.config = config
        if is_active is not None:
            node.is_active = is_active
        node.save(update_fields=['node_name', 'position_x', 'position_y', 'config', 'is_active', 'updated_at'])
        return node

    @staticmethod
    def delete_node(node: WorkflowBuilderNode) -> None:
        WorkflowBuilderConnection.objects.filter(
            workflow_id=node.workflow_id,
            source_node_id=node.id,
        ).delete()
        WorkflowBuilderConnection.objects.filter(
            workflow_id=node.workflow_id,
            target_node_id=node.id,
        ).delete()
        node.delete()

    @staticmethod
    def connect_nodes(
        *,
        workflow_id,
        source_node_id,
        target_node_id,
        connection_type: str = 'default',
        condition_label: str = '',
        metadata: dict[str, Any] | None = None,
        tenant_id=None,
        created_by=None,
    ) -> WorkflowBuilderConnection:
        if source_node_id == target_node_id:
            raise ValueError('Source and target node cannot be the same.')

        source_exists = WorkflowBuilderNode.objects.filter(id=source_node_id, workflow_id=workflow_id, is_active=True).exists()
        target_exists = WorkflowBuilderNode.objects.filter(id=target_node_id, workflow_id=workflow_id, is_active=True).exists()
        if not source_exists or not target_exists:
            raise ValueError('Source or target node not found for this workflow.')

        connection, _ = WorkflowBuilderConnection.objects.update_or_create(
            workflow_id=workflow_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            defaults={
                'tenant_id': tenant_id,
                'connection_type': connection_type,
                'condition_label': condition_label,
                'metadata': metadata or {},
                'created_by': created_by,
            },
        )
        return connection

    @staticmethod
    def remove_connection(connection: WorkflowBuilderConnection) -> None:
        connection.delete()

    @staticmethod
    def _build_graph(workflow_id):
        nodes = list(WorkflowBuilderNode.objects.filter(workflow_id=workflow_id, is_active=True))
        node_ids = {n.id for n in nodes}
        connections = list(
            WorkflowBuilderConnection.objects.filter(
                workflow_id=workflow_id,
                source_node_id__in=node_ids,
                target_node_id__in=node_ids,
            )
        )
        adjacency: dict[Any, list[Any]] = defaultdict(list)
        incoming: dict[Any, int] = defaultdict(int)
        for conn in connections:
            adjacency[conn.source_node_id].append(conn.target_node_id)
            incoming[conn.target_node_id] += 1
            incoming.setdefault(conn.source_node_id, incoming.get(conn.source_node_id, 0))
        return nodes, connections, adjacency, incoming

    @staticmethod
    def validate_workflow_graph(*, workflow_id) -> dict[str, Any]:
        nodes, connections, adjacency, incoming = WorkflowVisualBuilderEngine._build_graph(workflow_id)
        errors: list[str] = []
        warnings: list[str] = []

        if not nodes:
            return {'valid': False, 'errors': ['Workflow graph has no nodes.'], 'warnings': []}

        starts = [n for n in nodes if n.node_type == 'start']
        if len(starts) != 1:
            errors.append('Workflow must have exactly one start node.')
        ends = [n for n in nodes if n.node_type == 'end']
        if not ends:
            warnings.append('End node is recommended for safe completion tracking.')

        node_map = {node.id: node for node in nodes}

        for node in nodes:
            out_degree = len(adjacency.get(node.id, []))
            in_degree = incoming.get(node.id, 0)
            if node.node_type == 'decision' and out_degree < 2:
                errors.append(f'Decision node "{node.node_name}" must have at least 2 outputs.')
            if node.node_type != 'start' and in_degree == 0:
                errors.append(f'Node "{node.node_name}" has no incoming connection.')
            if node.node_type != 'end' and out_degree == 0:
                errors.append(f'Node "{node.node_name}" has no outgoing connection.')

        start_node = starts[0] if len(starts) == 1 else None
        if start_node:
            reachable = set()
            queue = deque([start_node.id])
            while queue:
                nid = queue.popleft()
                if nid in reachable:
                    continue
                reachable.add(nid)
                for nxt in adjacency.get(nid, []):
                    if nxt not in reachable:
                        queue.append(nxt)
            for node in nodes:
                if node.id not in reachable:
                    errors.append(f'Orphan/unreachable node detected: "{node.node_name}".')

            layout = WorkflowBuilderLayout.objects.filter(workflow_id=workflow_id).first()
            allow_loops = bool((layout.canvas_config or {}).get('allow_loops')) if layout else False
            if not allow_loops:
                visited = set()
                stack = set()

                def dfs(nid):
                    visited.add(nid)
                    stack.add(nid)
                    for nxt in adjacency.get(nid, []):
                        if nxt not in visited and dfs(nxt):
                            return True
                        if nxt in stack:
                            return True
                    stack.remove(nid)
                    return False

                for node in nodes:
                    if node.id not in visited and dfs(node.id):
                        errors.append('Workflow contains an infinite loop. Enable allow_loops to bypass.')
                        break

        return {'valid': len(errors) == 0, 'errors': errors, 'warnings': warnings}

    @staticmethod
    def auto_layout_graph(*, workflow_id, x_spacing: int = 280, y_spacing: int = 140) -> list[WorkflowBuilderNode]:
        nodes, _, adjacency, _ = WorkflowVisualBuilderEngine._build_graph(workflow_id)
        if not nodes:
            return []
        start = next((n for n in nodes if n.node_type == 'start'), nodes[0])
        levels: dict[Any, int] = {start.id: 0}
        queue = deque([start.id])
        while queue:
            nid = queue.popleft()
            for nxt in adjacency.get(nid, []):
                if nxt not in levels:
                    levels[nxt] = levels[nid] + 1
                    queue.append(nxt)
        # place disconnected nodes after max level
        max_level = max(levels.values()) if levels else 0
        for node in nodes:
            levels.setdefault(node.id, max_level + 1)

        buckets: dict[int, list[WorkflowBuilderNode]] = defaultdict(list)
        for node in nodes:
            buckets[levels[node.id]].append(node)

        updated = []
        for level in sorted(buckets.keys()):
            for idx, node in enumerate(sorted(buckets[level], key=lambda n: (n.node_type, n.created_at))):
                node.position_x = level * x_spacing
                node.position_y = idx * y_spacing
                node.save(update_fields=['position_x', 'position_y', 'updated_at'])
                updated.append(node)
        return updated

    @staticmethod
    def export_workflow_graph(*, workflow_id) -> dict[str, Any]:
        nodes = WorkflowBuilderNode.objects.filter(workflow_id=workflow_id, is_active=True).order_by('created_at')
        connections = WorkflowBuilderConnection.objects.filter(workflow_id=workflow_id).order_by('created_at')
        layout = WorkflowBuilderLayout.objects.filter(workflow_id=workflow_id).first()
        return {
            'workflow_id': str(workflow_id),
            'nodes': [
                {
                    'id': str(node.id),
                    'node_type': node.node_type,
                    'node_name': node.node_name,
                    'position_x': node.position_x,
                    'position_y': node.position_y,
                    'config': node.config or {},
                    'is_active': node.is_active,
                }
                for node in nodes
            ],
            'connections': [
                {
                    'id': str(conn.id),
                    'source_node_id': str(conn.source_node_id),
                    'target_node_id': str(conn.target_node_id),
                    'condition_label': conn.condition_label,
                    'connection_type': conn.connection_type,
                    'metadata': conn.metadata or {},
                }
                for conn in connections
            ],
            'layout': {
                'canvas_config': (layout.canvas_config if layout else {}),
                'zoom_level': (layout.zoom_level if layout else 1.0),
                'viewport': (layout.viewport if layout else {}),
            },
        }

    @staticmethod
    @transaction.atomic
    def import_workflow_graph(
        *,
        workflow_id,
        payload: dict[str, Any],
        tenant_id=None,
        created_by=None,
    ) -> dict[str, Any]:
        WorkflowBuilderConnection.objects.filter(workflow_id=workflow_id).delete()
        WorkflowBuilderNode.objects.filter(workflow_id=workflow_id).delete()

        old_to_new: dict[str, Any] = {}
        for node_data in payload.get('nodes', []):
            node = WorkflowVisualBuilderEngine.create_node(
                workflow_id=workflow_id,
                node_type=str(node_data.get('node_type', 'stage')),
                node_name=str(node_data.get('node_name', 'Stage')),
                position_x=int(node_data.get('position_x', 0)),
                position_y=int(node_data.get('position_y', 0)),
                config=node_data.get('config', {}),
                tenant_id=tenant_id,
                created_by=created_by,
            )
            old_to_new[str(node_data.get('id') or node.id)] = node.id

        for conn_data in payload.get('connections', []):
            source = old_to_new.get(str(conn_data.get('source_node_id')))
            target = old_to_new.get(str(conn_data.get('target_node_id')))
            if not source or not target:
                continue
            WorkflowVisualBuilderEngine.connect_nodes(
                workflow_id=workflow_id,
                source_node_id=source,
                target_node_id=target,
                connection_type=str(conn_data.get('connection_type', 'default')),
                condition_label=str(conn_data.get('condition_label', '')),
                metadata=conn_data.get('metadata', {}),
                tenant_id=tenant_id,
                created_by=created_by,
            )

        layout = payload.get('layout', {}) or {}
        WorkflowBuilderLayout.objects.update_or_create(
            workflow_id=workflow_id,
            defaults={
                'tenant_id': tenant_id,
                'canvas_config': layout.get('canvas_config', {}),
                'zoom_level': float(layout.get('zoom_level', 1.0)),
                'viewport': layout.get('viewport', {}),
                'created_by': created_by,
            },
        )
        return WorkflowVisualBuilderEngine.export_workflow_graph(workflow_id=workflow_id)

    @staticmethod
    @transaction.atomic
    def save_to_runtime(*, workflow_id):
        validation = WorkflowVisualBuilderEngine.validate_workflow_graph(workflow_id=workflow_id)
        if not validation['valid']:
            return {'saved': False, 'validation': validation}

        workflow = Workflow.objects.filter(id=workflow_id).first()
        if workflow is None:
            return {'saved': False, 'validation': validation, 'errors': ['Workflow not found in runtime.']}

        nodes = list(WorkflowBuilderNode.objects.filter(workflow_id=workflow_id, is_active=True).order_by('created_at'))
        connections = list(WorkflowBuilderConnection.objects.filter(workflow_id=workflow_id).order_by('created_at'))

        workflow.nodes.all().delete()
        workflow.edges.all().delete()

        builder_to_runtime = {}
        for node in nodes:
            runtime_type = WorkflowVisualBuilderEngine.NODE_TYPE_TO_RUNTIME.get(node.node_type, 'action')
            runtime_node = WorkflowNode.objects.create(
                workflow=workflow,
                node_type=runtime_type,
                config={
                    'label': node.node_name,
                    'builder_node_type': node.node_type,
                    **(node.config or {}),
                },
                position_x=node.position_x,
                position_y=node.position_y,
            )
            builder_to_runtime[node.id] = runtime_node

        for connection in connections:
            source = builder_to_runtime.get(connection.source_node_id)
            target = builder_to_runtime.get(connection.target_node_id)
            if not source or not target:
                continue
            WorkflowEdge.objects.create(
                workflow=workflow,
                source_node=source,
                target_node=target,
                condition={
                    'label': connection.condition_label,
                    'connection_type': connection.connection_type,
                    **(connection.metadata or {}),
                },
            )

        return {
            'saved': True,
            'validation': validation,
            'runtime_nodes': len(builder_to_runtime),
            'runtime_edges': len(connections),
        }


# Function-style exports required by prompt contract.
create_node = WorkflowVisualBuilderEngine.create_node
update_node = WorkflowVisualBuilderEngine.update_node
delete_node = WorkflowVisualBuilderEngine.delete_node
connect_nodes = WorkflowVisualBuilderEngine.connect_nodes
remove_connection = WorkflowVisualBuilderEngine.remove_connection
validate_workflow_graph = WorkflowVisualBuilderEngine.validate_workflow_graph
auto_layout_graph = WorkflowVisualBuilderEngine.auto_layout_graph
export_workflow_graph = WorkflowVisualBuilderEngine.export_workflow_graph
import_workflow_graph = WorkflowVisualBuilderEngine.import_workflow_graph
