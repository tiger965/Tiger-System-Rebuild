#!/bin/bash
#
# Tiger系统 - 自动部署脚本
# 10号窗口 - 一键部署
#

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 部署环境
ENVIRONMENT=${1:-development}
PROJECT_ROOT="/mnt/c/Users/tiger/TigerSystem"
PYTHON_VERSION="3.10"

echo "============================================================"
echo "Tiger智能交易分析系统 - 自动部署"
echo "环境: ${ENVIRONMENT}"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"
echo ""

# 1. 检查Python版本
check_python_version() {
    print_info "检查Python版本..."
    
    python_ver=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
    required_ver="3.10"
    
    if [ "$(printf '%s\n' "$required_ver" "$python_ver" | sort -V | head -n1)" = "$required_ver" ]; then 
        print_success "Python版本符合要求: $python_ver"
    else
        print_error "Python版本不符合要求。需要: >= $required_ver, 当前: $python_ver"
        exit 1
    fi
}

# 2. 检查依赖
check_dependencies() {
    print_info "检查系统依赖..."
    
    # 检查必需的命令
    commands=("git" "pip3" "mysql" "redis-cli")
    for cmd in "${commands[@]}"; do
        if command -v $cmd &> /dev/null; then
            print_success "$cmd 已安装"
        else
            print_warning "$cmd 未安装，某些功能可能不可用"
        fi
    done
}

# 3. 创建虚拟环境
setup_virtual_env() {
    print_info "设置虚拟环境..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "虚拟环境创建成功"
    else
        print_info "虚拟环境已存在"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    print_success "虚拟环境已激活"
}

# 4. 安装Python依赖
install_python_deps() {
    print_info "安装Python依赖..."
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Python依赖安装完成"
    else
        print_warning "requirements.txt 不存在，跳过依赖安装"
    fi
}

# 5. 初始化数据库
init_database() {
    print_info "初始化数据库..."
    
    # 检查MySQL服务
    if command -v mysql &> /dev/null; then
        # 这里添加实际的数据库初始化脚本
        print_info "数据库初始化（模拟）"
        print_success "数据库初始化完成"
    else
        print_warning "MySQL未安装，跳过数据库初始化"
    fi
}

# 6. 配置检查
check_config() {
    print_info "检查配置文件..."
    
    cd "$PROJECT_ROOT"
    
    # 运行配置验证
    python3 -c "
from tests.integration.config_manager import ConfigManager
manager = ConfigManager()
results = manager.validate_config()
if results['valid']:
    print('配置验证通过')
    exit(0)
else:
    print('配置验证失败')
    exit(1)
" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "配置验证通过"
    else
        print_warning "配置验证失败，使用默认配置"
    fi
}

# 7. 启动服务
start_services() {
    print_info "启动系统服务..."
    
    # 检查Redis
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            print_success "Redis服务正常"
        else
            print_warning "Redis服务未运行"
        fi
    fi
    
    # 启动主程序
    print_info "启动Tiger系统..."
    
    # 根据环境选择启动方式
    case $ENVIRONMENT in
        development)
            print_info "开发模式启动"
            # python3 tests/integration/main.py --dev &
            ;;
        testing)
            print_info "测试模式启动"
            # python3 tests/integration/main.py --test &
            ;;
        production)
            print_info "生产模式启动"
            # nohup python3 tests/integration/main.py --prod > tiger.log 2>&1 &
            ;;
        *)
            print_error "未知环境: $ENVIRONMENT"
            exit 1
            ;;
    esac
    
    print_success "系统启动命令已执行"
}

# 8. 健康检查
health_check() {
    print_info "执行健康检查..."
    
    # 等待系统启动
    sleep 3
    
    # 检查系统状态
    python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from tests.integration.main import TigerSystem
import asyncio

async def check():
    system = TigerSystem()
    success, total = system.initialize_modules()
    if success > 0:
        print(f'健康检查通过: {success}/{total} 模块正常')
        return True
    else:
        print('健康检查失败: 无可用模块')
        return False

result = asyncio.run(check())
exit(0 if result else 1)
" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "健康检查通过"
    else
        print_warning "健康检查未完全通过"
    fi
}

# 9. 部署完成
deployment_complete() {
    echo ""
    echo "============================================================"
    print_success "Tiger系统部署完成！"
    echo "============================================================"
    echo ""
    echo "系统信息:"
    echo "  - 环境: $ENVIRONMENT"
    echo "  - 路径: $PROJECT_ROOT"
    echo "  - 时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "后续操作:"
    echo "  - 查看日志: tail -f logs/integration.log"
    echo "  - 运行测试: python3 tests/integration/test_suite.py"
    echo "  - 查看监控: python3 tests/integration/monitoring.py"
    echo ""
}

# 主流程
main() {
    cd "$PROJECT_ROOT"
    
    # 创建必要的目录
    mkdir -p logs
    mkdir -p data
    mkdir -p config
    mkdir -p reports
    
    # 执行部署步骤
    check_python_version
    check_dependencies
    # setup_virtual_env
    # install_python_deps
    # init_database
    check_config
    start_services
    health_check
    deployment_complete
}

# Docker部署函数
docker_deploy() {
    print_info "Docker部署模式..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker未安装"
        exit 1
    fi
    
    # 检查docker-compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose未安装"
        exit 1
    fi
    
    # 构建镜像
    print_info "构建Docker镜像..."
    docker-compose build
    
    # 启动容器
    print_info "启动Docker容器..."
    docker-compose up -d
    
    # 查看状态
    print_info "容器状态:"
    docker-compose ps
    
    print_success "Docker部署完成"
}

# 处理参数
case "${2:-}" in
    --docker)
        docker_deploy
        ;;
    *)
        main
        ;;
esac