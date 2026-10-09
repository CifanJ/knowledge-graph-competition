import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st

# 数据库连接函数
def get_conn():
    return sqlite3.connect("knowledge.db")

# 新增课程
def add_course(course_name, upload_time):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO course(course_name, upload_time) VALUES (?,?)",(course_name,upload_time))
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id

# 插入知识点
def add_node(course_id, node_name, difficulty, desc):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO knowledge_node(course_id,node_name,difficulty,description) VALUES (?,?,?,?)",
                (course_id, node_name, difficulty, desc))
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id

# 插入知识点关系
def add_relation(source_id, target_id, rel_type):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO knowledge_relation(source_id,target_id,relation_type) VALUES (?,?,?)",
                (source_id, target_id, rel_type))
    conn.commit()
    conn.close()

# 获取所有课程列表
def get_all_courses():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM course", conn)
    conn.close()
    return df

# 根据课程id读取知识点
def get_nodes_by_course(course_id):
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM knowledge_node WHERE course_id=?", conn, params=(course_id,))
    conn.close()
    return df

# 根据课程id读取关系
def get_relations_by_course(course_id):
    conn = get_conn()
    df = pd.read_sql('''SELECT r.*, s.node_name as source_name, t.node_name as target_name
                     FROM knowledge_relation r
                     LEFT JOIN knowledge_node s ON r.source_id = s.node_id
                     LEFT JOIN knowledge_node t ON r.target_id = t.node_id
                     WHERE s.course_id=?''', conn, params=(course_id,))
    conn.close()
    return df

# ---------------------- 页面配置 ----------------------
st.set_page_config(page_title="基于AIGC的课程知识图谱智能构建与学习导航系统", layout="wide")
st.title("基于AIGC的课程知识图谱智能构建与学习导航系统")

tab1, tab2 = st.tabs(["教师端：图谱生成与管理", "学生端：学习导航"])

with tab1:
    st.header("📚 历史课程管理")
    course_df = get_all_courses()
    if not course_df.empty:
        selected_course_id = st.selectbox("选择已有课程查看图谱", course_df["course_id"], 
                                          format_func=lambda x: course_df[course_df["course_id"]==x]["course_name"].values[0])
        node_df = get_nodes_by_course(selected_course_id)
        rel_df = get_relations_by_course(selected_course_id)
        st.subheader("知识点列表")
        st.dataframe(node_df, use_container_width=True)
        st.subheader("知识关联关系")
        st.dataframe(rel_df, use_container_width=True)
    else:
        st.info("暂无课程，请上传课程文档生成知识图谱")

    st.divider()
    st.header("✨ AIGC 生成新课程知识图谱")
    course_name = st.text_input("输入课程名称", value="高等数学")
    course_text = st.text_area("粘贴课程讲义/知识点文本", height=250,
                               placeholder="在这里粘贴课程内容，例如：导数是微分的前置知识点...")
    if st.button("AI抽取知识点并生成图谱，存入数据库") and course_text.strip():
        # 模拟AIGC抽取结果（比赛演示用，后续可接入真实大模型）
        nodes = [
            {"name": "极限", "difficulty": "中等", "desc": "函数极限定义与运算法则"},
            {"name": "导数", "difficulty": "困难", "desc": "导数定义、求导公式"},
            {"name": "微分", "difficulty": "困难", "desc": "微分定义，导数与微分关系"}
        ]
        relations = [
            {"source": "极限", "target": "导数", "type": "前置"},
            {"source": "导数", "target": "微分", "type": "前置"}
        ]

        # 存入数据库
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        course_id = add_course(course_name, now_time)
        node_map = {}
        for node in nodes:
            nid = add_node(course_id, node["name"], node["difficulty"], node["desc"])
            node_map[node["name"]] = nid
        for rel in relations:
            sid = node_map[rel["source"]]
            tid = node_map[rel["target"]]
            add_relation(sid, tid, rel["type"])
        st.success(f"✅ 课程【{course_name}】入库完成！课程ID:{course_id}，刷新页面下拉框即可加载")

with tab2:
    st.header("📖 学生学习导航")
    course_df = get_all_courses()
    if not course_df.empty:
        stu_course_id = st.selectbox("选择课程", course_df["course_id"], 
                                     format_func=lambda x: course_df[course_df["course_id"]==x]["course_name"].values[0])
        node_df = get_nodes_by_course(stu_course_id)
        if not node_df.empty:
            target_node = st.selectbox("选择想要学习的目标知识点", node_df["node_name"].tolist())
            st.subheader("智能推荐学习路径")
            st.write(f"建议学习顺序：极限 → 导数 → 微分")
            st.info("先学习前置知识点【极限】，再学习【导数】，最后学习目标知识点【微分】")
    else:
        st.warning("暂无课程数据，请教师端先上传生成图谱")
