"""
Flask Configuration Classes
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400))
    )
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # MySQL Database
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'sfqa_db')
    
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@"
        f"{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    
    # Celery
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
    
    # LLM Provider
    LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'ollama').lower()

    # Ollama
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_EMBEDDING_MODEL = os.getenv('OLLAMA_EMBEDDING_MODEL', 'nomic-embed-text')
    OLLAMA_DEFAULT_MODEL = os.getenv('OLLAMA_DEFAULT_MODEL', 'qwen2.5:7b')

    # llama.cpp
    LLAMACPP_BASE_URL = os.getenv('LLAMACPP_BASE_URL', 'http://localhost:8080')
    LLAMACPP_MODEL_PATH = os.getenv('LLAMACPP_MODEL_PATH', 'models/llama-model.gguf')
    LLAMACPP_N_CTX = int(os.getenv('LLAMACPP_N_CTX', '4096'))
    LLAMACPP_N_THREADS = int(os.getenv('LLAMACPP_N_THREADS', '4'))
    LLAMACPP_N_BATCH = int(os.getenv('LLAMACPP_N_BATCH', '512'))
    
    # RAG Configuration
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1000))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 200))
    CHUNK_MIN_SIZE = int(os.getenv('CHUNK_MIN_SIZE', 200))
    EMBEDDING_BATCH_SIZE = int(os.getenv('EMBEDDING_BATCH_SIZE', 32))
    
    # RAG Search Configuration
    RELEVANCE_THRESHOLD = float(os.getenv('RELEVANCE_THRESHOLD', 0.3))
    ENABLE_HYBRID_SEARCH = os.getenv('ENABLE_HYBRID_SEARCH', 'true').lower() == 'true'
    HYBRID_BM25_WEIGHT = float(os.getenv('HYBRID_BM25_WEIGHT', 0.3))
    
    # Multi-source RAG Configuration (Reference: Open-WebUI)
    RAG_TOP_K = int(os.getenv('RAG_TOP_K', 10))  # 基础检索数量，从5增加到10
    RAG_TOP_K_RERANKER = int(os.getenv('RAG_TOP_K_RERANKER', 5))  # 重排序后保留数量
    RAG_ENABLE_MULTI_SOURCE = os.getenv('RAG_ENABLE_MULTI_SOURCE', 'true').lower() == 'true'
    RAG_MAX_CHUNKS_PER_FILE = int(os.getenv('RAG_MAX_CHUNKS_PER_FILE', 3))  # 每个文件最多返回的chunk数
    RAG_MIN_FILES = int(os.getenv('RAG_MIN_FILES', 2))  # 至少来自多少个不同文件
    
    # File Upload
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 50 * 1024 * 1024))
    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        os.getenv('UPLOAD_FOLDER', 'uploads')
    )
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'md', 'xlsx', 'xls'}
    
    # Chroma Vector DB
    CHROMA_PERSIST_DIRECTORY = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        os.getenv('CHROMA_PERSIST_DIRECTORY', 'vector_db')
    )


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
