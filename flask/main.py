# 1. 导入 Flask 类
# 2. 实例化应用
# 3. 绑定路由和视图函数
# 4. 定义启动服务器的代码

from flask import Flask

# Flask(__name__)
app = Flask(__name__)


# @app.route(路径)
# def index() 视图函数

@app.route('/')
def root():
    return 'hello flask'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999, debug=True)
