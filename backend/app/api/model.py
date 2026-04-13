"""Model Management API Routes
"""
import uuid
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import model_bp
from ..utils.response import success_response, error_response
from ..models import CustomModel, KnowledgeBase, ModelKnowledgeBinding
from ..extensions import db
from ..services import get_llm_service, get_llm_provider


@model_bp.route('/ollama', methods=['GET'])
@jwt_required()
def get_ollama_models():
    """Get available LLM models (Ollama or llama.cpp)"""
    llm = get_llm_service()
    models = llm.get_models()

    return success_response(
        data=[{
            'name': m.get('name', ''),
            'size': m.get('size', 0),
            'modified_at': m.get('modified_at', ''),
            'provider': get_llm_provider()
        } for m in models]
    )


@model_bp.route('/custom', methods=['GET'])
@jwt_required()
def get_custom_models():
    """Get user's custom models"""
    user_id = get_jwt_identity()
    
    models = CustomModel.query.filter_by(user_id=user_id).order_by(
        CustomModel.created_at.desc()
    ).all()
    
    return success_response(
        data=[m.to_dict(include_knowledge=True) for m in models]
    )


@model_bp.route('/custom', methods=['POST'])
@jwt_required()
def create_custom_model():
    """Create a custom model"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('base_model'):
        return error_response(400, 'Name and base_model are required')
    
    model = CustomModel(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=data['name'],
        base_model=data['base_model'],
        system_prompt=data.get('system_prompt', ''),
        description=data.get('description', '')
    )
    
    try:
        db.session.add(model)
        db.session.commit()
        return success_response(model.to_dict(), 'Model created', 201)
    except Exception as e:
        db.session.rollback()
        return error_response(400, str(e))


@model_bp.route('/custom/<model_id>', methods=['GET'])
@jwt_required()
def get_custom_model(model_id):
    """Get custom model details"""
    user_id = get_jwt_identity()
    
    model = CustomModel.query.filter_by(id=model_id, user_id=user_id).first()
    if not model:
        return error_response(404, 'Model not found')
    
    return success_response(model.to_dict(include_knowledge=True))


@model_bp.route('/custom/<model_id>', methods=['PUT'])
@jwt_required()
def update_custom_model(model_id):
    """Update custom model"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    model = CustomModel.query.filter_by(id=model_id, user_id=user_id).first()
    if not model:
        return error_response(404, 'Model not found')
    
    if 'name' in data:
        model.name = data['name']
    if 'base_model' in data:
        model.base_model = data['base_model']
    if 'system_prompt' in data:
        model.system_prompt = data['system_prompt']
    if 'description' in data:
        model.description = data['description']
    
    try:
        db.session.commit()
        return success_response(model.to_dict(include_knowledge=True), 'Model updated')
    except Exception as e:
        db.session.rollback()
        return error_response(400, str(e))


@model_bp.route('/custom/<model_id>', methods=['DELETE'])
@jwt_required()
def delete_custom_model(model_id):
    """Delete custom model"""
    user_id = get_jwt_identity()
    
    model = CustomModel.query.filter_by(id=model_id, user_id=user_id).first()
    if not model:
        return error_response(404, 'Model not found')
    
    try:
        db.session.delete(model)
        db.session.commit()
        return success_response(message='Model deleted')
    except Exception as e:
        db.session.rollback()
        return error_response(400, str(e))


@model_bp.route('/custom/<model_id>/knowledge', methods=['POST'])
@jwt_required()
def bind_knowledge_base(model_id):
    """Bind knowledge base to model"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('knowledge_base_id'):
        return error_response(400, 'knowledge_base_id is required')
    
    model = CustomModel.query.filter_by(id=model_id, user_id=user_id).first()
    if not model:
        return error_response(404, 'Model not found')
    
    kb = KnowledgeBase.query.filter_by(
        id=data['knowledge_base_id'], 
        user_id=user_id
    ).first()
    if not kb:
        return error_response(404, 'Knowledge base not found')
    
    # Check if binding exists
    existing = ModelKnowledgeBinding.query.filter_by(
        custom_model_id=model_id,
        knowledge_base_id=kb.id
    ).first()
    
    if existing:
        return error_response(400, 'Knowledge base already bound to this model')
    
    binding = ModelKnowledgeBinding(
        id=str(uuid.uuid4()),
        custom_model_id=model_id,
        knowledge_base_id=kb.id
    )
    
    try:
        db.session.add(binding)
        db.session.commit()
        return success_response(
            model.to_dict(include_knowledge=True),
            'Knowledge base bound'
        )
    except Exception as e:
        db.session.rollback()
        return error_response(400, str(e))


@model_bp.route('/custom/<model_id>/knowledge/<kb_id>', methods=['DELETE'])
@jwt_required()
def unbind_knowledge_base(model_id, kb_id):
    """Unbind knowledge base from model"""
    user_id = get_jwt_identity()
    
    model = CustomModel.query.filter_by(id=model_id, user_id=user_id).first()
    if not model:
        return error_response(404, 'Model not found')
    
    binding = ModelKnowledgeBinding.query.filter_by(
        custom_model_id=model_id,
        knowledge_base_id=kb_id
    ).first()
    
    if not binding:
        return error_response(404, 'Binding not found')
    
    try:
        db.session.delete(binding)
        db.session.commit()
        return success_response(
            model.to_dict(include_knowledge=True),
            'Knowledge base unbound'
        )
    except Exception as e:
        db.session.rollback()
        return error_response(400, str(e))


@model_bp.route('/health', methods=['GET'])
@jwt_required()
def get_llm_health():
    """Get LLM service health status"""
    llm = get_llm_service()
    provider = get_llm_provider()

    is_available = llm.is_available()

    return success_response(
        data={
            'provider': provider,
            'available': is_available,
            'default_model': llm.get_default_model() if is_available else None
        }
    )
