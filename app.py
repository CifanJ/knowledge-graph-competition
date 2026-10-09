import streamlit as st
import json
import requests
from streamlit_agraph import agraph, Node, Edge, Config

# ===================== 页面基础配置 =====================
st.set_page_config(page_title="基于AIGC的课程知识图谱智能构建与学习导航系统", layout="wide")

# ===================== 初始化会话状态 =====================
if "login_status" not in st.session_state:
    st.session_state.login_status = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "username" not in st.session_state:
    st.session_state.username = ""
if "course_list" not in st.session_state:
    st.session_state.course_list = []
# 用户库，存在session_state
if "user_db" not in st.session_state:
    st.session_state.user_db = [
        {"phone": "13800138000", "pwd": "teacher123", "role": "teacher", "name": "张老师"},
        {"phone": "13800138001", "pwd": "student123", "role": "student", "name": "小明同学"}
    ]

# ===================== DeepSeek API配置（从Secrets读取） =====================
DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_KEY"]
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

# ===================== DeepSeek：知识图谱生成 =====================
def generate_kg_by_deepseek(text):
    prompt = f"""
你是课程知识抽取专家，请从下面课程文本提取知识点，输出严格JSON格式，不要多余文字。
要求：
1. nodes数组：每个元素{{"id":数字,"name":"知识点名称"}}
2. edges数组：每个元素{{"source":起点id,"target":终点id,"relation":"关系，一般为前置知识点"}}
3. 知识点之间梳理前置依赖关系。
课程文本：
{text}
只返回JSON，不要任何解释。
"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role":"user","content":prompt}],
        "temperature":0.2
    }
    resp = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=60)
    res_json = resp.json()
    content = res_json["choices"][0]["message"]["content"]
    kg_data = json.loads(content)
    return kg_data

# ===================== 图谱可视化转换函数 =====================
def render_kg_graph(kg_json):
    nodes = []
    edges = []
    for n in kg_json["nodes"]:
        nodes.append(Node(id=str(n["id"]), label=n["name"], size=25, color="#4285F4"))
    for e in kg_json["edges"]:
        edges.append(Edge(source=str(e["source"]), target=str(e["target"]), label=e["relation"], color="#888888"))
    config = Config(width=1000, height=400, directed=True, physics=True, hierarchical=False)
    return agraph(nodes=nodes, edges=edges, config=config)

# ===================== 登录页面 =====================
def login_page():
    st.title("📱 用户登录")
    st.markdown("手机号 + 密码登录系统")
    phone_input = st.text_input("手机号", placeholder="13800138000")
    pwd_input = st.text_input("密码", type="password", placeholder="输入密码")
    if st.button("登录", type="primary"):
        match_user = None
        for u in st.session_state.user_db:
            if u["phone"] == phone_input and u["pwd"] == pwd_input:
                match_user = u
                break
        if match_user:
            st.session_state.login_status = True
            st.session_state.user_role = match_user["role"]
            st.session_state.username = match_user["name"]
            st.success("✅ 登录成功！")
            st.rerun()
        else:
            st.error("❌ 手机号或密码错误")

# ===================== 教师端页面 =====================
def teacher_page():
    st.title("基于AIGC的课程知识图谱智能构建与学习导航系统")
    st.markdown(f"👋 欢迎你，{st.session_state.username}（教师端）")
    logout_btn = st.button("退出登录")
    if logout_btn:
        st.session_state.login_status = False
        st.session_state.user_role = None
        st.rerun()
    st.divider()

    tab1, tab2 = st.tabs(["课程图谱管理", "学生账号管理"])

    # Tab1：课程图谱管理
    with tab1:
        st.subheader("📚 历史课程管理")
        if len(st.session_state.course_list) == 0:
            st.info("暂无课程，请粘贴课程讲义，调用DeepSeek生成知识图谱")
        else:
            for idx, course in enumerate(st.session_state.course_list):
                with st.expander(f"{course['name']}"):
                    st.write("### 知识图谱可视化")
                    render_kg_graph(course["graph"])
                    st.write("### 图谱原始JSON数据")
                    st.json(course["graph"])

        st.divider()
        st.subheader("✨ DeepSeek AIGC生成新课程知识图谱")
        course_name = st.text_input("输入课程名称", value="高等数学")
        course_text = st.text_area("粘贴课程讲义/知识点文本", height=200,
            value="高等数学包含极限、导数、积分三大核心模块。\n极限是导数的前置知识点；导数是不定积分的前置知识点；不定积分是定积分的前置知识点。\n极限：研究自变量趋近某值时函数的变化趋势。\n导数：函数在一点处的瞬时变化率。\n不定积分：导数的逆运算。\n定积分：曲边梯形面积计算。")

        if st.button("🤖 AIGC生成知识图谱", type="primary"):
            with st.spinner("正在调用DeepSeek抽取知识点，生成图谱..."):
                kg_data = generate_kg_by_deepseek(course_text)
                new_course = {"name":course_name, "content":course_text, "graph":kg_data}
                st.session_state.course_list.append(new_course)
                st.success("✅ 知识图谱生成成功！下方可查看可视化图谱")
                render_kg_graph(kg_data)

    # Tab2：学生账号管理：新增学生 + 修改学生密码
    with tab2:
        st.subheader("➕ 新增学生账号（教师注册学生）")
        new_stu_name = st.text_input("学生姓名", key="new_stu_name")
        new_stu_phone = st.text_input("学生手机号", key="new_stu_phone")
        new_stu_pwd = st.text_input("学生初始密码", key="new_stu_pwd")
        if st.button("添加学生账号", type="primary"):
            # 判断手机号是否已经存在
            exist = False
            for u in st.session_state.user_db:
                if u["phone"] == new_stu_phone:
                    exist = True
                    break
            if exist:
                st.error("❌ 该手机号账号已存在！")
            elif len(new_stu_phone)!=11 or not new_stu_phone.isdigit():
                st.error("❌ 手机号格式错误！")
            elif new_stu_name.strip() == "" or new_stu_pwd.strip() == "":
                st.error("❌ 姓名和密码不能为空！")
            else:
                # 添加学生账号
                new_student = {
                    "phone": new_stu_phone,
                    "pwd": new_stu_pwd,
                    "role": "student",
                    "name": new_stu_name
                }
                st.session_state.user_db.append(new_student)
                st.success(f"✅ 学生【{new_stu_name}】注册成功，学生可以使用该手机号+密码登录！")

        st.divider()
        st.subheader("👨‍🎓 已有学生账号列表（可修改密码）")
        student_list = [u for u in st.session_state.user_db if u["role"] == "student"]
        if len(student_list) ==0:
            st.info("暂无学生账号，请在上方新增学生")
        else:
            for stu in student_list:
                with st.expander(f"学生：{stu['name']} | 手机号：{stu['phone']}"):
                    update_pwd = st.text_input("修改密码", value=stu["pwd"], key=stu["phone"])
                    if st.button("保存密码", key=f"save_{stu['phone']}"):
                        for u in st.session_state.user_db:
                            if u["phone"] == stu["phone"]:
                                u["pwd"] = update_pwd
                                break
                        st.success(f"✅ {stu['name']} 的密码已更新！")

# ===================== 学生端页面 =====================
def student_page():
    st.title("基于AIGC的课程知识图谱智能构建与学习导航系统")
    st.markdown(f"👋 欢迎你，{st.session_state.username}（学生端）")
    logout_btn = st.button("退出登录")
    if logout_btn:
        st.session_state.login_status = False
        st.session_state.user_role = None
        st.rerun()
    st.divider()
    st.subheader("📖 课程学习导航")
    if len(st.session_state.course_list) == 0:
        st.info("暂无课程，请等待教师创建课程知识图谱")
    else:
        for idx, course in enumerate(st.session_state.course_list):
            with st.expander(f"📘 {course['name']} - 学习路径推荐"):
                st.write("🎯 可视化知识图谱（按前置关系规划学习顺序）")
                render_kg_graph(course["graph"])
                st.info("💡 学习提示：顺着箭头方向学习，先掌握前置知识点，再学习后续知识点")

# ===================== 主入口 =====================
if not st.session_state.login_status:
    login_page()
else:
    if st.session_state.user_role == "teacher":
        teacher_page()
    elif st.session_state.user_role == "student":
        student_page()
