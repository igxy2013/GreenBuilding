from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_from_directory, make_response, flash
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

# 添加缓存控制装饰器
def cache_control(max_age=3600):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = make_response(f(*args, **kwargs))
            response.headers['Cache-Control'] = f'public, max-age={max_age}'
            return response
        return decorated_function
    return decorator

@app.route('/')
@cache_control(max_age=3600)
def index():
    return render_template('login.html')  # 直接渲染登录页面

@app.route('/reset_password')
@cache_control(max_age=3600)
def reset_password_page():
    """处理密码重置页面路由"""
    try:
        return render_template('reset_password.html')
    except Exception as e:
        app.logger.error(f"渲染密码重置页面错误: {str(e)}")
        return "页面加载失败", 500

@app.route('/register')
@cache_control(max_age=3600)
def register_page():
    return render_template('register.html')

@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('calculator'))
    # 获取next参数，用于登录后重定向
    next_url = request.args.get('next') or session.get('next_url')
    if next_url:
        session['next_url'] = next_url
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

# 修改登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查session中是否存在user_id
        if 'user_id' not in session:
            # 将要访问的原始URL存储在session中
            session['next_url'] = request.url
            # 闪现消息通知用户需要登录
            flash('请先登录后再访问', 'error')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': '请提供邮箱和密码'}), 400
    
    try:
        user = User.query.filter_by(email=data['email']).first()
        
        if user and user.check_password(data['password']):
            session['user_id'] = user.id
            # 获取登录后要重定向的URL
            next_url = session.pop('next_url', None)
            return jsonify({
                'message': '登录成功',
                'redirect': next_url or url_for('calculator'),
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

# 添加登出路由
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

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
@cache_control(max_age=86400)  # 24小时缓存
def serve_static(filename):
    """处理静态文件请求"""
    try:
        # 确保目录使用正确的绝对路径
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        return send_from_directory(static_dir, filename)
    except Exception as e:
        app.logger.error(f"静态文件访问错误: {str(e)}")
        return "文件不存在", 404

# 修改dashboard路由重定向到calculator
@app.route('/dashboard')
@login_required
def dashboard():
    return redirect(url_for('calculator'))

@app.route('/api/template')
@login_required
def get_template():
    """处理Word模板请求"""
    try:
        template_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            'static', 
            '绿色建材应用比例计算书.docx'
        )
        return send_from_directory(
            os.path.dirname(template_path),
            os.path.basename(template_path),
            as_attachment=True
        )
    except Exception as e:
        app.logger.error(f"模板文件访问错误: {str(e)}")
        return "模板文件不存在", 404

@app.route('/api/check_auth')
def check_auth():
    """检查用户是否已登录"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'status': 'authenticated'}), 200

# 确保使用正确的路径分隔符
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

# 修改配置为开发环境
app.config['DEBUG'] = True
app.config['ENV'] = 'development'

if __name__ == '__main__':
    # 确保目录存在
    os.makedirs(static_dir, exist_ok=True)
    os.makedirs(templates_dir, exist_ok=True)
    
    with app.app_context():
        db.create_all()
    
    # 使用开发服务器
    app.run(host='0.0.0.0', port=8090, debug=True)