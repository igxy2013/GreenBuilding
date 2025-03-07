from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import re
import os
import sqlite3
from datetime import datetime
from functools import wraps

app = Flask(__name__)
# 使用绝对路径来存储数据库文件
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'fallback-secret-key')

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def init_db():
    """初始化数据库并添加测试数据"""
    with app.app_context():
        # 删除所有表
        db.drop_all()
        # 创建所有表
        db.create_all()
        
        # 添加测试用户
        test_user = User(email='test@example.com')
        test_user.set_password('password123')
        
        try:
            db.session.add(test_user)
            db.session.commit()
            print("数据库初始化成功！")
        except Exception as e:
            print(f"数据库初始化错误: {str(e)}")
            db.session.rollback()

@app.route('/')
def index():
    return render_template('login.html')  # 直接渲染登录页面

@app.route('/reset_password')
def reset_password_page():
    """处理密码重置页面路由"""
    try:
        return render_template('reset_password.html')
    except Exception as e:
        app.logger.error(f"渲染密码重置页面错误: {str(e)}")
        return "页面加载失败", 500

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # 验证数据
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': '请提供邮箱和密码'}), 400
    
    # 验证邮箱格式
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', data['email']):
        return jsonify({'error': '邮箱格式不正确'}), 400
    
    # 检查邮箱是否已存在（修复语法错误）
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({'error': '该邮箱已被注册'}), 400
    
    # 创建新用户
    try:
        user = User(email=data['email'])
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': '注册成功'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'注册失败：{str(e)}'}), 500

# 添加登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# 修改登录路由
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': '请提供邮箱和密码'}), 400
    
    try:
        user = User.query.filter_by(email=data['email']).first()
        
        if user and user.check_password(data['password']):
            session['user_id'] = user.id  # 在session中存储用户ID
            return jsonify({
                'message': '登录成功',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'created_at': user.created_at.isoformat()
                }
            }), 200
        else:
            return jsonify({'error': '用户名或密码错误'}), 401
            
    except Exception as e:
        app.logger.error(f"登录错误: {str(e)}")
        return jsonify({'error': '登录失败，请稍后重试'}), 500

# 修改 calculator 路由
@app.route('/calculator')
@login_required
def calculator():
    """处理计算器页面请求"""
    try:
        return render_template('calculator.html')
    except Exception as e:
        app.logger.error(f"渲染计算器页面错误: {str(e)}")
        return str(e), 500

# 添加静态资源路由（如果calculator.html需要额外的js或css文件）
@app.route('/static/<path:filename>')
def serve_static(filename):
    """处理静态文件请求"""
    try:
        return send_from_directory('static', filename)
    except Exception as e:
        app.logger.error(f"静态文件访问错误: {str(e)}")
        return "文件不存在", 404

# 修改dashboard路由重定向到calculator
@app.route('/dashboard')
@login_required
def dashboard():
    return redirect(url_for('calculator'))

if __name__ == '__main__':
    # 确保目录存在
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # 启用调试日志
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    with app.app_context():
        db.create_all()  # 创建数据库表
        
    app.run(debug=True)