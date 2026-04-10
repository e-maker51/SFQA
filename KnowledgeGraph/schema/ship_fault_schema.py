"""
Ship Fault Knowledge Graph Schema Definition

Defines the node types, relationship types, and patterns for the ship fault
domain knowledge graph, following neo4j-graphrag schema conventions.
"""

SHIP_FAULT_NODE_TYPES = [
    {
        "label": "Equipment",
        "description": "船舶电气设备，如发电机、电动机、配电板、变压器等",
        "properties": [
            {"name": "name", "type": "STRING", "required": True},
            {"name": "category", "type": "STRING"},
            {"name": "specification", "type": "STRING"},
            {"name": "location", "type": "STRING"},
        ],
    },
    {
        "label": "Fault",
        "description": "设备故障类型，描述设备出现的具体故障",
        "properties": [
            {"name": "name", "type": "STRING", "required": True},
            {"name": "severity", "type": "STRING"},
            {"name": "description", "type": "STRING"},
        ],
    },
    {
        "label": "Symptom",
        "description": "故障现象和症状，如异常声响、温度过高、电压异常等",
        "properties": [
            {"name": "name", "type": "STRING", "required": True},
            {"name": "description", "type": "STRING"},
        ],
    },
    {
        "label": "Cause",
        "description": "故障原因，包括直接原因和根本原因",
        "properties": [
            {"name": "name", "type": "STRING", "required": True},
            {"name": "cause_type", "type": "STRING"},
            {"name": "description", "type": "STRING"},
        ],
    },
    {
        "label": "Solution",
        "description": "故障排除方法和维修方案",
        "properties": [
            {"name": "name", "type": "STRING", "required": True},
            {"name": "solution_type", "type": "STRING"},
            {"name": "description", "type": "STRING"},
            {"name": "steps", "type": "STRING"},
        ],
    },
    {
        "label": "System",
        "description": "船舶系统，如推进系统、导航系统、供电系统等",
        "properties": [
            {"name": "name", "type": "STRING", "required": True},
            {"name": "description", "type": "STRING"},
        ],
    },
    {
        "label": "Component",
        "description": "设备组成部件或零件",
        "properties": [
            {"name": "name", "type": "STRING", "required": True},
            {"name": "specification", "type": "STRING"},
            {"name": "material", "type": "STRING"},
        ],
    },
    {
        "label": "DiagnosticMethod",
        "description": "故障诊断方法，如传统诊断法、故障树分析法、专家系统诊断法等",
        "properties": [
            {"name": "name", "type": "STRING", "required": True},
            {"name": "method_type", "type": "STRING"},
            {"name": "description", "type": "STRING"},
        ],
    },
    {
        "label": "TestMethod",
        "description": "测试和检测方法，如绝缘测试、电压测量、电流测量等",
        "properties": [
            {"name": "name", "type": "STRING", "required": True},
            {"name": "tool_required", "type": "STRING"},
            {"name": "description", "type": "STRING"},
        ],
    },
    {
        "label": "SafetyMeasure",
        "description": "维修安全措施和注意事项",
        "properties": [
            {"name": "name", "type": "STRING", "required": True},
            {"name": "description", "type": "STRING"},
        ],
    },
]

SHIP_FAULT_RELATIONSHIP_TYPES = [
    {
        "label": "HAS_FAULT",
        "description": "设备发生的故障",
    },
    {
        "label": "HAS_SYMPTOM",
        "description": "故障表现出的症状",
    },
    {
        "label": "CAUSED_BY",
        "description": "故障的原因",
    },
    {
        "label": "SOLVED_BY",
        "description": "故障的解决方案",
    },
    {
        "label": "BELONGS_TO_SYSTEM",
        "description": "设备所属的船舶系统",
    },
    {
        "label": "CONTAINS_COMPONENT",
        "description": "设备包含的部件",
    },
    {
        "label": "DIAGNOSED_BY",
        "description": "故障的诊断方法",
    },
    {
        "label": "TESTED_BY",
        "description": "故障或设备的测试方法",
    },
    {
        "label": "REQUIRES_SAFETY",
        "description": "维修方案需要的安全措施",
    },
    {
        "label": "LEADS_TO",
        "description": "原因导致的故障（因果链）",
    },
    {
        "label": "RELATED_FAULT",
        "description": "相关联的故障",
    },
]

SHIP_FAULT_PATTERNS = [
    ("Equipment", "HAS_FAULT", "Fault"),
    ("Fault", "HAS_SYMPTOM", "Symptom"),
    ("Fault", "CAUSED_BY", "Cause"),
    ("Fault", "SOLVED_BY", "Solution"),
    ("Equipment", "BELONGS_TO_SYSTEM", "System"),
    ("Equipment", "CONTAINS_COMPONENT", "Component"),
    ("Fault", "DIAGNOSED_BY", "DiagnosticMethod"),
    ("Fault", "TESTED_BY", "TestMethod"),
    ("Solution", "REQUIRES_SAFETY", "SafetyMeasure"),
    ("Cause", "LEADS_TO", "Fault"),
    ("Fault", "RELATED_FAULT", "Fault"),
]


def get_ship_fault_schema_dict():
    """Return the ship fault schema as a dictionary for SimpleKGPipeline."""
    return {
        "node_types": SHIP_FAULT_NODE_TYPES,
        "relationship_types": SHIP_FAULT_RELATIONSHIP_TYPES,
        "patterns": SHIP_FAULT_PATTERNS,
        "additional_node_types": False,
    }
