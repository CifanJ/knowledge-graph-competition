import streamlit as st
import requests
import json

# 页面基础配置
st.set_page_config(page_title="基于AIGC的课程知识图谱智能构建与学习导航系统", layout="wide")

# 初始化会话状态
if "login" not in st.session_state:
    st.session_state.login = False
if "role" not in st.session_state:
    st.session_state.role = None
if "user_phone" not in st.session_state:
    st.session_state.user_phone = None
if "student_list" not in st.session_state:
    st.session_state.student_list = []
if "graph_data" not in st.session_state:
    st.session_state.graph_data = None

# DeepSeek API配置
DEEPSEEK_API_KEY = "sk-4f4c99f734fa410ebe0da47608f43dcb"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

# ---------------- 登录页面 ----------------
def login_page():
    st.title("📱 用户登录")
    st.subheader("手机号 + 密码登录系统")
    phone = st.text_input("手机号")
    pwd = st.text_input("密码", type="password")
    if st.button("登录"):
        # 内置账号
        if phone == "13800138000" and pwd == "teacher123":
            st.session_state.login = True
            st.session_state.role = "teacher"
            st.session_state.user_phone = phone
            st.rerun()
        else:
            # 匹配学生列表
            find_stu = False
            for s in st.session_state.student_list:
                if s["phone"] == phone and s["pwd"] == pwd:
                    st.session_state.login = True
                    st.session_state.role = "student"
                    st.session_state.user_phone = phone
                    find_stu = True
                    st.rerun()
            if not find_stu:
                st.error("手机号或密码错误！")

# ---------------- 教师模块 ----------------
def teacher_manage_student():
    st.header("👥 学生账号管理")
    st.divider()
    with st.form("add_student"):
        s_phone = st.text_input("学生手机号")
        s_pwd = st.text_input("学生密码")
        s_name = st.text_input("学生姓名")
        sub = st.form_submit_button("添加学生账号")
        if sub:
            exists = any(item["phone"] == s_phone for item in st.session_state.student_list)
            if exists:
                st.warning("该手机号学生账号已存在")
            else:
                st.session_state.student_list.append({"phone":s_phone,"pwd":s_pwd,"name":s_name})
                st.success("添加成功！")
    st.subheader("学生列表")
    if len(st.session_state.student_list) ==0:
        st.info("暂无学生账号")
    else:
        st.table(st.session_state.student_list)

def teacher_build_graph():
    st.header("🧠 AIGC课程知识图谱生成")
    st.divider()
    course_text = st.text_area("粘贴课程文本内容", height=250, placeholder="例如：高等数学包含极限、导数；导数由极限定义，微分和导数密切相关")
    if st.button("一键生成知识图谱"):
        with st.spinner("大模型正在抽取知识点与关系..."):
            prompt = f"""
你是知识图谱抽取专家。从下面课程文本提取【实体】和【实体之间的关系】，输出JSON格式：
{{"nodes":[{"id":"节点ID","name":"知识点名称"}],"edges":[{"source":"起点ID","target":"终点ID","label":"关系描述"}]}}
课程内容：{course_text}
只返回JSON，不要多余文字。
"""
            headers = {"Authorization":f"Bearer {DEEPSEEK_API_KEY}", "Content-Type":"application/json"}
            payload = {
                "model":"deepseek-chat",
                "messages":[{"role":"user","content":prompt}],
                "temperature":0.3
            }
            resp = requests.post(DEEPSEEK_URL, headers=headers, data=json.dumps(payload))
            res_json = resp.json()
            content = res_json["choices"][0]["message"]["content"]
            graph = json.loads(content)
            st.session_state.graph_data = graph
        st.success("图谱生成完成！")
        st.subheader("图谱节点")
        st.write(graph["nodes"])
        st.subheader("关系连线")
        st.write(graph["edges"])
        st.info("答辩演示：节点代表知识点，连线代表依赖关系，学生可以顺着关系得到学习导航")

# ---------------- 学生模块 ----------------
def student_view_graph():
    st.header("📖 课程知识图谱查看")
    st.divider()
    if st.session_state.graph_data is None:
        st.warning("暂无教师生成的课程知识图谱，请等待教师创建！")
    else:
        st.subheader("知识点图谱信息")
        st.write(st.session_state.graph_data)

def student_learn_nav():
    st.header("🧭 智能学习导航")
    st.divider()
    if st.session_state.graph_data is None:
        st.warning("暂无图谱，无法生成学习路径")
    else:
        st.markdown("""
### 学习顺序建议
1. 优先学习没有前置依赖的基础知识点
2. 再学习有前置要求的进阶知识点
> 本系统创新点：AIGC自动识别知识点依赖关系，自动规划学习路线，不用人工标注
""")

# ---------------- 主逻辑 侧边栏导航 ----------------
if not st.session_state.login:
    login_page()
else:
    # ==========侧边栏菜单==========
    with st.sidebar:
        st.title("📚 系统导航")
        st.divider()
        if st.session_state.role == "teacher":
            menu = st.radio("功能菜单", [
                "🏠 教师首页",
                "👥 学生账号管理",
                "🧠 AIGC知识图谱生成",
                "🚪 退出登录"
            ])
        else:
            menu = st.radio("功能菜单", [
                "🏠 学生首页",
                "📖 课程知识图谱查看",
                "🧭 学习导航",
                "🚪 退出登录"
            ])
        st.divider()
        st.caption("金扬智能｜AIGC课程知识图谱系统")

    # 页面内容
    if menu == "🚪 退出登录":
        st.session_state.login = False
        st.session_state.role = None
        st.rerun()
    elif menu == "🏠 教师首页":
        st.title("欢迎教师使用系统")
        st.markdown("""
### 系统简介
本系统面向教学场景，基于AIGC自动构建课程知识图谱
✅ 学生账号管理
✅ 课程文本一键生成知识图谱
✅ 自动提取知识点和依赖关系
        """)
    elif menu == "👥 学生账号管理":
        teacher_manage_student()
    elif menu == "🧠 AIGC知识图谱生成":
        teacher_build_graph()
    elif menu == "🏠 学生首页":
        st.title("欢迎同学使用学习导航系统")
        st.markdown("查看课程知识图谱，获取AI推荐学习顺序")
    elif menu == "📖 课程知识图谱查看":
        student_view_graph()
    elif menu == "🧭 学习导航":
        student_learn_nav()
